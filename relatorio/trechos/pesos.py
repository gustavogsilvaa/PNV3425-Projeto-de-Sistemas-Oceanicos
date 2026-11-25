def pesos(x, hid, cen):
    Lp, bp, hp, bc, hc, T = map(float, x)
    D = hid["Delta"]
    z_top = hp + hc                                  # fundo do convés
    hd, hm = cen.hd, cen.hm

    W_planta = PESO_PLANTA_T_BOE * cen.BOE
    W_conv = F_CONVES * W_planta
    W_oper = F_OPER * W_planta
    V_pont = 2 * Lp * bp * hp
    V_colunas = 4 * bc**2 * hc
    W_pont = GAMMA_E * V_pont
    W_col = GAMMA_E * V_colunas
    W_ris = F_RISERS * D
    W_amr = F_AMARR * D

    itens = [("Planta de produção", W_planta, z_top + hd + hm / 2),
             ("Estrutura do convés", W_conv, z_top + hd / 2),
             ("Carga operacional", W_oper, z_top + hd / 2),
             ("Pontoons", W_pont, hp / 2),
             ("Colunas", W_col, hp + hc / 2),
             ("Risers", W_ris, z_top),
             ("Amarração", W_amr, z_top)]
    W_sem_lastro = sum(w for _, w, _ in itens)
    W_lastro = D - W_sem_lastro
    V_lastro = W_lastro / RHO
    nivel = float(np.clip(V_lastro / (2 * Lp * bp), 0.0, hp))
    itens.append(("Lastro (nos pontoons)", W_lastro, nivel / 2))

    W_tot = sum(w for _, w, _ in itens)              # = Δ
    M_tot = sum(w * z for _, w, z in itens)
    KG = M_tot / W_tot
    W_top = W_planta + W_conv + W_oper
    VCG_top = (W_planta * (z_top + hd + hm / 2) + (W_conv + W_oper) * (z_top + hd / 2)) / W_top
    return dict(W_planta=W_planta, W_conves=W_conv, W_oper=W_oper, W_topside=W_top,
                VCG_topside=VCG_top, W_pontoons=W_pont, W_colunas=W_col,
                W_casco=W_pont + W_col, W_risers=W_ris, W_amarracao=W_amr,
                W_lastro=W_lastro, V_lastro=V_lastro, V_pont=V_pont,
                nivel_lastro=nivel, KG=KG, W_total=W_tot, M_total=M_tot, itens=itens,
                GM_T=hid["KM_T"] - KG, GM_L=hid["KM_L"] - KG)
