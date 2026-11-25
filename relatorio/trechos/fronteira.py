    # Fronteira de Pareto = não dominados entre todas as soluções viáveis.
    # Cada candidato do LHS é reconfirmado com o passo angular fino (DPHI_FINAL).
    cols = NOMES_X + ["W_casco", "Hz"]
    viaveis = pd.concat([df_am.loc[df_am.viavel, cols].assign(origem="LHS"),
                         df_ws[cols].assign(origem="Soma ponderada"),
                         df_eps[cols].assign(origem="ε-restrito") if len(df_eps) else None],
                        ignore_index=True)
    while True:
        front = viaveis.iloc[nao_dominados(viaveis.W_casco.values, viaveis.Hz.values)]
        reprov = [i for i in front.index if viaveis.loc[i, "origem"] == "LHS" and
                  not viavel(avaliar(viaveis.loc[i, NOMES_X].values.astype(float), cen, dphi=DPHI_FINAL))]
        if not reprov:
            break
        viaveis = viaveis.drop(index=reprov)
    front = front.sort_values("W_casco").reset_index(drop=True)
    front.to_csv(os.path.join(OUT_DIR, "fronteira_pareto.csv"), index=False)
