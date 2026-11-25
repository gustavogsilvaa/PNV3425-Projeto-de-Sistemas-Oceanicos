def _volume_e_derivada(cx, alpha, beta):
    """Volume submerso e dV/dα. A derivada é exata: Σ t·(comprimento da linha
    d'água dentro de cada retângulo)."""
    u0, u1, z0, z1, t = cx
    a = alpha[:, None]
    b = beta[:, None]
    p = np.clip((z0 - a) / b, u0, u1)
    q = np.clip((z1 - a) / b, u0, u1)
    L = q - p
    area = (a + b * (p + q) / 2 - z0) * L + (u1 - q) * (z1 - z0)
    return (t * area).sum(1), (t * L).sum(1)


def equilibrio_2d(cx, V0, phis_rad, alpha0=None, tol=1e-10, n_max=100):
    """Para cada ângulo, acha a linha d'água que mantém ∇ = V0.
    Newton com salvaguarda: mantém o intervalo [lo, hi] da bissecção e usa
    bissecção sempre que o passo de Newton sai dele. alpha0 (ex.: o calado T)
    é o chute inicial; sem ele, parte do meio do intervalo."""
    beta = np.maximum(np.tan(phis_rad), 1e-12)
    u0, u1, z0, z1, _ = cx
    lo = z0.min() - beta * u1.max() - 1.0
    hi = z1.max() - beta * u0.min() + 1.0
    alpha = 0.5 * (lo + hi) if alpha0 is None else np.clip(np.broadcast_to(alpha0, lo.shape), lo, hi)
    tol_V = tol * V0                                   # tolerância em volume [m³]
    for _ in range(n_max):
        V, dV = _volume_e_derivada(cx, alpha, beta)
        ok = np.abs(V - V0) <= tol_V                   # convergência por ângulo
        if ok.all():
            break
        acima = V > V0
        hi = np.where(acima, alpha, hi)
        lo = np.where(acima, lo, alpha)
        with np.errstate(divide="ignore", invalid="ignore"):
            novo = alpha - (V - V0) / dV
        # Newton só se cair estritamente dentro de (lo, hi); senão bissecção.
        # Isso impede o ciclo entre as duas pontas do intervalo, que acontece
        # quando V(α) tem quinas (linha d'água passando por cantos).
        fora = ~np.isfinite(novo) | (novo <= lo) | (novo >= hi)
        novo = np.where(fora, 0.5 * (lo + hi), novo)
        alpha = np.where(ok, alpha, novo)              # convergidos ficam parados
    else:                                              # garantia: bissecção pura
        for _ in range(60):
            V, _ = _volume_e_derivada(cx, alpha, beta)
            ok = np.abs(V - V0) <= tol_V
            if ok.all():
                break
            acima = V > V0
            hi = np.where(acima, alpha, hi)
            lo = np.where(acima, lo, alpha)
            alpha = np.where(ok, alpha, 0.5 * (lo + hi))
    V, Mu, Mz = _integrais_submersas(cx, alpha, beta)
    return alpha, Mu / V, Mz / V


def curva_gz(x, KG, V0, plano, phis_deg):
    cx = caixas_2d(x, plano)
    ph = np.radians(phis_deg)
    alpha, uB, zB = equilibrio_2d(cx, V0, ph, alpha0=float(x[5]))
    GZ = uB * np.cos(ph) + (zB - KG) * np.sin(ph)
    return GZ, alpha
