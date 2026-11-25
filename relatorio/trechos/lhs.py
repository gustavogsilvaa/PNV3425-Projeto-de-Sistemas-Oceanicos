def nao_dominados(W, H):
    idx = np.argsort(W, kind="stable")
    front, melhor = [], np.inf
    for i in idx:
        if H[i] < melhor * (1 - 1e-5):
            front.append(i)
            melhor = H[i]
    return np.array(front, int)


def variacao_sistematica(n=N_AMOSTRAS, cen=CEN_G02):
    lo = np.array([b[0] for b in BOUNDS])
    hi = np.array([b[1] for b in BOUNDS])
    X = qmc.scale(qmc.LatinHypercube(d=6, seed=SEMENTE).random(n), lo, hi)
    regs = []
    for x in X:
        r = avaliar(x, cen, com_estab=False)
        ok_pre = viavel(r)
        reg = dict(zip(NOMES_X, x), W_casco=r["pes"]["W_casco"], Hz=r["hv"]["Hz"],
                   GM_T=r["pes"]["GM_T"], Tn=r["hv"]["Tn"], pre_viavel=ok_pre, viavel=False)
        if ok_pre:
            r = avaliar(x, cen, com_estab=True)
            reg["viavel"] = viavel(r)
            reg["AB_min"] = r["est"]["AB_min"]
        regs.append(reg)
    return pd.DataFrame(regs)
