def angulo_alagamento(x, V0, plano, phis_deg, alpha):
    """φal: fundo do convés (u = Lp/2, z = hp+hc) toca a água na borda."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    zd = hp + hc
    cx = caixas_2d(x, plano)

    def folga(phd):
        a, _, _ = equilibrio_2d(cx, V0, np.radians([phd]), alpha0=T)
        return zd - (a[0] + np.tan(np.radians(phd)) * Lp / 2)

    f = zd - (alpha + np.tan(np.radians(phis_deg)) * Lp / 2)
    idx = np.where(f <= 0)[0]
    if len(idx) == 0:
        ph_prev = phis_deg[-1]
        for phd in np.arange(phis_deg[-1] + 2.0, 86.0, 2.0):
            if folga(phd) <= 0:
                return brentq(folga, ph_prev, phd, xtol=1e-7)
            ph_prev = phd
        return 85.0
    i = idx[0]
    if i == 0:
        return 0.0
    return brentq(folga, phis_deg[i - 1], phis_deg[i], xtol=1e-7)
