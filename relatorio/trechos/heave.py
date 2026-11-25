OMEGAS = np.linspace(0.02, 2.5, 1500)        # [rad/s] malha fina p/ ressonância


def ca_retangulo(a_sobre_b):
    """CA 2D de retângulo (DNV-RP-C205, Tab. A-1); a = meia-largura normal ao
    movimento (bp/2), b = meia-altura na direção do movimento (hp/2)."""
    tab_ab = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 1e6])
    tab_ca = np.array([2.23, 1.98, 1.70, 1.51, 1.36, 1.21, 1.14, 1.00])
    return float(np.interp(np.log(a_sobre_b), np.log(tab_ab), tab_ca))


def espectro_mar(w, Hs, Tp, gamma=None):
    """JONSWAP (DNV-RP-C205). [REV 6] γ = None -> lê GAMMA_JONSWAP na chamada."""
    gamma = GAMMA_JONSWAP if gamma is None else gamma
    wp = 2 * np.pi / Tp
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        S = (5.0 / 16.0) * Hs**2 * wp**4 * w**-5 * np.exp(-1.25 * (wp / w)**4)
        if gamma != 1.0:
            sig = np.where(w <= wp, 0.07, 0.09)
            S = S * (1 - 0.287 * np.log(gamma)) * gamma**np.exp(-0.5 * ((w - wp) / (sig * wp))**2)
    return np.nan_to_num(S)


def heave(x, hid, cen, gamma=None):
    Lp, bp, hp, bc, hc, T = map(float, x)
    gamma = GAMMA_JONSWAP if gamma is None else gamma
    M = hid["Delta"]
    A_wp = hid["A_wp"]
    A_p = 2 * Lp * bp                                   # área em planta dos pontoons
    CA = ca_retangulo(bp / hp)
    ld = Lp - 2 * bc                                    # [REV 2] comprimento livre
    A33 = 2 * ld * CA * RHO * np.pi * (bp / 2)**2       # massa adicional [t]
    C33 = RHO * G * A_wp                                # [kN/m]
    wn = np.sqrt(C33 / (M + A33))
    Tn = 2 * np.pi / wn
    B33 = 2 * XI_HEAVE * np.sqrt(C33 * (M + A33))       # [kN·s/m]

    w = OMEGAS
    k = w**2 / G
    dp = Lp - bp                                        # distância entre pontoons
    fase = np.cos(k * dp / 2)                           # [REV 2] cos(ω²dp/2g)
    d_top = max(T - hp, 0.0)                            # prof. do topo do pontoon
    F_col = RHO * G * A_wp * np.exp(-k * d_top) * fase
    F_pont = -RHO * G * A_p * (np.exp(-k * d_top) - np.exp(-k * T)) * fase
    F_dif = -A33 * w**2 * np.exp(-k * (T - hp / 2)) * fase
    F3 = F_col + F_pont + F_dif                         # [kN/m de amplitude]
    RAO = np.abs(F3) / np.abs(C33 - (M + A33) * w**2 + 1j * B33 * w)

    S = espectro_mar(w, cen.Hs, cen.Tp, gamma)
    Sz = RAO**2 * S
    m0z = trapezoid(Sz, w)
    Hz = 4 * np.sqrt(m0z)
    # H1/3 de heave com o outro γ (1,0 <-> 3,3), só para comparação
    gamma_alt = 1.0 if gamma != 1.0 else 3.3
    Hz_alt = 4 * np.sqrt(trapezoid(RAO**2 * espectro_mar(w, cen.Hs, cen.Tp, gamma_alt), w))
    troca = np.where(np.sign(F3[1:]) != np.sign(F3[:-1]))[0]   # 1ª troca de sinal
    i_canc = troca[0] + 1 if len(troca) else len(w) - 1
    return dict(M=M, A33=A33, CA=CA, ld=ld, C33=C33, B33=B33, wn=wn, Tn=Tn,
                omega=w, fase=fase, F_col=F_col, F_pont=F_pont, F_dif=F_dif, F3=F3,
                RAO=RAO, S=S, Sz=Sz, m0z=m0z, Hz=Hz, gamma=gamma,
                gamma_alt=gamma_alt, Hz_alt=Hz_alt,
                Hs_check=4 * np.sqrt(trapezoid(S, w)), w_cancel=w[i_canc])
