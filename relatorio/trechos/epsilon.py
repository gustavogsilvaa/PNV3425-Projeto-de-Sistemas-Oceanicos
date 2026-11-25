def epsilon_restrito(df_ws, df_am, cen=CEN_G02, n=N_EPSILON):
    """Método ε-restrito: min W_casco sujeito a Hz ≤ ε. Preenche trechos da
    fronteira que a soma ponderada não alcança (fronteira não convexa).
    [REV 3] Partidas: amostra/ótimo mais leve com Hz ≤ ε e ótimo da soma
    ponderada imediatamente abaixo de ε."""
    cols = NOMES_X + ["W_casco", "Hz"]
    conhecidos = pd.concat([df_am.loc[df_am.viavel, cols], df_ws[cols]], ignore_index=True)
    H_lo, H_hi = df_ws.Hz.min(), df_ws.Hz.max()
    niveis = np.linspace(H_lo, H_hi, n + 2)[1:-1]
    tarefas = []                                  # todos os níveis em paralelo
    for k, eps in enumerate(niveis):
        cand = conhecidos[conhecidos.Hz <= eps]
        tarefas.append(("eps", eps, cand.loc[cand.W_casco.idxmin(), NOMES_X].values.astype(float),
                        k, cen))
        abaixo = df_ws[df_ws.Hz <= eps]
        if len(abaixo):
            tarefas.append(("eps", eps, abaixo.loc[abaixo.Hz.idxmax(), NOMES_X].values.astype(float),
                            k, cen))
    resultados = _mapear(tarefas)
    sols = []
    for k, eps in enumerate(niveis):
        ok = [t for t in resultados if t["origem"] == k and t["ok"]]
        if not ok:
            print(f"   ε={eps:.4f} m | FALHA: nenhuma partida terminou em ponto viável")
            continue
        t = min(ok, key=lambda t: t["reg"]["W_casco"])
        g = t["reg"]
        sols.append(dict(eps=eps, **g, success=t["success"], iter=t["nit"]))
        print(f"   ε={eps:.4f} m | W_casco={g['W_casco']:9.1f} t | Hz={g['Hz']:.4f} m"
              f" | GM_T={g['GM_T']:.2f} | Tn={g['Tn']:.2f} s | A/B={g['AB_min']:.2f}"
              f" | success={t['success']}")
    return pd.DataFrame(sols)


def variaveis_no_limite(x, tol=1e-3):
    return [f"{n} = {v:.2f} ({'mín' if abs(v - b[0]) < tol else 'máx'})"
            for n, v, b in zip(NOMES_X, x, BOUNDS) if abs(v - b[0]) < tol or abs(v - b[1]) < tol]


def ponto_joelho(W, H):
    """Ponto da fronteira mais próximo do ponto utópico (normalizado 0-1)."""
    Wn = (W - W.min()) / (W.max() - W.min() + 1e-12)
    Hn = (H - H.min()) / (H.max() - H.min() + 1e-12)
    return int(np.argmin(np.hypot(Wn, Hn)))
