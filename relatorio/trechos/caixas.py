def caixas_2d(x, plano):
    """Retângulos da projeção 2D: (u0, u1, z0, z1, espessura fora do plano)."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    if plano == "Transversal":       # inclinação em torno do eixo longitudinal
        yc = (Lp - bp) / 2
        cx = [(-Lp / 2, -Lp / 2 + bp, 0.0, hp, Lp),
              (Lp / 2 - bp, Lp / 2, 0.0, hp, Lp),
              (-yc - bc / 2, -yc + bc / 2, hp, hp + hc, 2 * bc),
              (yc - bc / 2, yc + bc / 2, hp, hp + hc, 2 * bc)]
    else:                            # inclinação em torno do eixo transversal
        cx = [(-Lp / 2, Lp / 2, 0.0, hp, 2 * bp),
              (-Lp / 2, -Lp / 2 + bc, hp, hp + hc, 2 * bc),
              (Lp / 2 - bc, Lp / 2, hp, hp + hc, 2 * bc)]
    return np.array(cx, float).T


def _integrais_submersas(cx, alpha, beta):
    """Área e momentos exatos dos retângulos abaixo da linha z = alpha + beta·u
    (coordenadas do corpo). Vetorizado em ângulos (linhas) x caixas (colunas)."""
    u0, u1, z0, z1, t = cx
    a = alpha[:, None]
    b = beta[:, None]
    H = z1 - z0
    p = np.clip((z0 - a) / b, u0, u1)
    q = np.clip((z1 - a) / b, u0, u1)
    zp, zq = a + b * p, a + b * q
    L = q - p
    area = ((zp + zq) / 2 - z0) * L + (u1 - q) * H
    mu = (a - z0) * (q**2 - p**2) / 2 + b * (q**3 - p**3) / 3 + H * (u1**2 - q**2) / 2
    mz = L * ((zp**2 + zp * zq + zq**2) / 3 - z0**2) / 2 + (u1 - q) * (z1**2 - z0**2) / 2
    return (t * area).sum(1), (t * mu).sum(1), (t * mz).sum(1)
