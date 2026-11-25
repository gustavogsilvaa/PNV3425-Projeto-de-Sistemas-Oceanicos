def avaliar(x, cen=CEN_G02, com_estab=True, dphi=DPHI_OTIM):
    x = np.asarray(x, float)
    Lp, bp, hp, bc, hc, T = x
    hid = hidrostatica(x)
    pes = pesos(x, hid, cen)
    hv = heave(x, hid, cen)
    a = hp + hc - T
    z_min = -1.86 * hv["Hz"] / 2
    r = dict(x=x, cen=cen, hid=hid, pes=pes, hv=hv, a=a, area=Lp**2,
             eta_max=cen.eta_max, z_min=z_min, a_min=cen.eta_max - z_min)
    if com_estab:
        r["est"] = estabilidade(x, hid, pes, cen, dphi=dphi)
    r["restr"] = tabela_restricoes(r)
    return r


def tabela_restricoes(r):
    Lp, bp, hp, bc, hc, T = r["x"]
    cen, pes, hv = r["cen"], r["pes"], r["hv"]
    # (nome, unidade, valor, sentido, limite, escala p/ otimizador e "ativa")
    L = [("Área de convés Lp²", "m²", r["area"], "≥", cen.area_req, 1000.0),
         ("GM_T mínimo", "m", pes["GM_T"], "≥", GM_MIN, 1.0),
         ("GM_T máximo", "m", pes["GM_T"], "≤", GM_MAX, 1.0),
         ("Período natural de heave Tn", "s", hv["Tn"], ">", TN_MIN, 1.0),
         ("Peso de lastro positivo", "t", pes["W_lastro"], ">", 0.0, 1e4),
         ("V_lastro ≤ 0,9·V_pontoons", "m³", pes["V_lastro"], "≤", FRAC_LASTRO * pes["V_pont"], 1e4),
         ("bc ≤ bp", "m", bc, "≤", bp, 1.0),
         ("Air gap a ≥ a_mín", "m", r["a"], "≥", r["a_min"], 1.0),
         ("Imersão das colunas T−hp (geométrica)", "m", T - hp, "≥", IMERSAO_MIN_COL, 1.0)]
    if LASTRO_MIN_FRAC > 0:                                         # [REV 4]
        L.append((f"V_lastro ≥ {LASTRO_MIN_FRAC:g}·V_pontoons", "m³", pes["V_lastro"], "≥",
                  LASTRO_MIN_FRAC * pes["V_pont"], 1e4))
    if "est" in r:
        L += [("Critério de áreas min(A/B), 4 casos", "-", r["est"]["AB_min"], "≥", AB_MIN, 1.0),
              ("GZ>0 até φ2/φal: min(GZ/senφ)", "m", r["est"]["GZsen_min"], ">", 0.0, 1.0)]
    linhas = []
    for nome, un, val, sentido, lim, esc in L:
        folga = val - lim if sentido in ("≥", ">") else lim - val
        ref = max(abs(lim), esc if esc > 1 else 1.0)
        estrita = sentido == ">"
        atende = folga > 0 if estrita else folga >= -1e-6
        margem = (MARGEM_OTIM + (1e-3 if estrita else 0.0)
                  + (MARGEM_AB_OTIM if nome.startswith("Critério") else 0.0))
        linhas.append(dict(Restrição=nome, Unid=un, Valor=val, Sentido=sentido,
                           Limite=lim, Folga=folga, Folga_pct=100 * folga / ref,
                           Atende="SIM" if atende else "NÃO",
                           Ativa="ATIVA" if (atende and abs(folga) / ref < 0.01) else "",
                           _g=folga / esc - margem))
    return pd.DataFrame(linhas)


def viavel(r):
    return bool((r["restr"].Atende == "SIM").all())
