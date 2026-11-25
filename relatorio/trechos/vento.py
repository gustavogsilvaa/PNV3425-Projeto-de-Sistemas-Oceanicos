def z_clr(x, plano):
    """[REV 1] Centro de resistência lateral: centroide da silhueta submersa
    vista na direção do vento (medido a partir da quilha).
      Transversal : Lp·hp (pontoons sobrepostos) + 2·bc·(T−hp)
      Longitudinal: 2·bp·hp (topos dos pontoons) + 2·bc·(T−hp)"""
    Lp, bp, hp, bc, hc, T = map(float, x)
    t_p, t_c = min(T, hp), max(T - hp, 0.0)
    A_pont = Lp * t_p if plano == "Transversal" else 2 * bp * t_p
    A_col = 2 * bc * t_c
    return (A_pont * t_p / 2 + A_col * (hp + t_c / 2)) / (A_pont + A_col)


def tabela_vento(x, V, plano, cen):
    """Forças, braços e momentos por parcela no plano dado.
    [REV 1] Colunas: 4·bc·a (Ex. 9: sem efeito de sombra). Braço medido do
    centroide da parcela até o z_CLR do plano. Deck box e módulos têm a mesma
    projeção nos dois planos (planta quadrada)."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    hd, hm = cen.hd, cen.hm
    a = max(hp + hc - T, 0.0)
    q = 0.5 * RHO_AR * V**2 / 1000.0          # pressão dinâmica [kPa]
    zclr = z_clr(x, plano)
    prof_clr = T - zclr                         # z_CLR abaixo da LA [m]
    parcelas = [("Colunas (4, sem sombra)", 4 * bc * a, a / 2, CS_COLUNAS),
                ("Deck box", Lp * hd, a + hd / 2, CS_DECKBOX),
                ("Módulos de topside", FRAC_LARG_MODULOS * Lp * hm, a + hd + hm / 2, CS_MODULOS),
                ("Face inferior do convés (HMud)", Lp * Lp, a, CS_UNDERDECK)]
    linhas = []
    for nome, A, zc, cs in parcelas:
        ch = coef_altura(zc)
        F = q * cs * ch * A
        braco = zc + prof_clr
        linhas.append(dict(Parcela=nome, Area_m2=A, z_LA_m=zc, Cs=cs, Ch=ch,
                           Forca_kN=F, Braco_m=braco, Momento_kNm=F * braco))
    HM0 = sum(l["Momento_kNm"] for l in linhas[:3])
    HMud = linhas[3]["Momento_kNm"]
    return linhas, HM0, HMud, zclr          # linhas -> pd.DataFrame no relatório
