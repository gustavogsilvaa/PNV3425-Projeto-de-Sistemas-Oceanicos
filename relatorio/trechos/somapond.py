def soma_ponderada(df_amostras, cen=CEN_G02):
    """[REV 3] Para cada w1: SLSQP a partir das N_PARTIDAS melhores amostras e
    do ótimo do w1 anterior (continuação). Só aceita o res.x do SLSQP; se
    nenhuma partida termina em ponto viável, o w1 é reportado como falha (não
    volta mais para o ponto de partida)."""
    am = df_amostras[df_amostras.viavel]
    pool_x = [np.array(v, float) for v in am[NOMES_X].values]
    pool_W, pool_H = list(am.W_casco.values), list(am.Hz.values)
    ws = np.round(np.arange(0.0, 1.0 + 1e-9, PASSO_W), 4)
    sols, x_ant = [], None
    for w1 in ws:
        f_pool = w1 * np.array(pool_H) + (1 - w1) * np.array(pool_W) / 1e4
        ordem = np.argsort(f_pool)[:N_PARTIDAS]
        tarefas = [("ws", w1, pool_x[i], "LHS", cen) for i in ordem]
        if x_ant is not None:
            tarefas.append(("ws", w1, x_ant, "w1 anterior", cen))
        f_part = f_pool[ordem[0]]
        melhor = None
        resultados = _mapear(tarefas)
        for t in resultados:
            if t["ok"]:
                f = w1 * t["reg"]["Hz"] + (1 - w1) * t["reg"]["W_casco"] / 1e4
                if melhor is None or f < melhor[0] - 1e-12:
                    melhor = (f, t)
        if melhor is None:
            print(f"   w1={w1:5.2f} | FALHA: nenhuma partida terminou em ponto viável")
            for t in resultados:
                print(f"      - {t['origem']}: success={t['success']} it={t['nit']} ({t['msg']})")
            continue
        f, t = melhor
        g = t["reg"]
        ganho = 100 * (1 - f / f_part)
        x_ant = t["x"]
        pool_x.append(t["x"]); pool_W.append(g["W_casco"]); pool_H.append(g["Hz"])
        n_succ = sum(s["success"] for s in resultados)
        sols.append(dict(w1=w1, w2=1 - w1, **g, F_obj=f, ganho_vs_LHS_pct=ganho,
                         success=t["success"], partida=t["origem"], iter=t["nit"],
                         partidas_success=f"{n_succ}/{len(resultados)}"))
        print(f"   w1={w1:5.2f} | W_casco={g['W_casco']:9.1f} t | Hz={g['Hz']:.4f} m"
              f" | GM_T={g['GM_T']:.2f} | Tn={g['Tn']:.2f} s | A/B={g['AB_min']:.2f}"
              f" | ganho s/ melhor LHS={ganho:5.1f}% | success={t['success']} ({t['origem']},"
              f" {n_succ}/{len(resultados)} partidas convergiram)", flush=True)
    df = pd.DataFrame(sols)
    if len(df):
        nd = set(nao_dominados(df.W_casco.values, df.Hz.values))
        df["dominado"] = [i not in nd for i in range(len(df))]
        if df.dominado.any():
            print(f"   Ótimos locais dominados (descartados pela fronteira): "
                  f"w1 = {df.loc[df.dominado, 'w1'].tolist()}")
    return df
