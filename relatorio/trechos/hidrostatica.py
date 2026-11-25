def hidrostatica(x):
    Lp, bp, hp, bc, hc, T = map(float, x)
    t_p = min(T, hp)                 # calado nos pontoons
    t_c = max(T - hp, 0.0)           # calado nas colunas
    V_pont = 2 * Lp * bp * t_p
    V_col = 4 * bc**2 * t_c
    V = V_pont + V_col
    KB = (V_pont * t_p / 2 + V_col * (hp + t_c / 2)) / V

    yc = (Lp - bp) / 2               # coluna -> eixo longitudinal (plano T)
    xc = (Lp - bc) / 2               # coluna -> eixo transversal (plano L)
    if t_c > 0:
        A_wp = 4 * bc**2
        I_T = 4 * (bc**4 / 12 + bc**2 * yc**2)
        I_L = 4 * (bc**4 / 12 + bc**2 * xc**2)
    else:                            # linha d'água nos pontoons (robustez)
        A_wp = 2 * Lp * bp
        I_T = 2 * (Lp * bp**3 / 12 + Lp * bp * yc**2)
        I_L = 2 * (bp * Lp**3 / 12)
    BM_T, BM_L = I_T / V, I_L / V
    return dict(V=V, Delta=RHO * V, V_pont_sub=V_pont, V_col_sub=V_col,
                KB=KB, I_T=I_T, I_L=I_L, BM_T=BM_T, BM_L=BM_L,
                KM_T=KB + BM_T, KM_L=KB + BM_L, A_wp=A_wp)
