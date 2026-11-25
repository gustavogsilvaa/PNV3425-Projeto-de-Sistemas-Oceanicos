class Problema:
    """Cache para o SLSQP: objetivo e restrições compartilham avaliações."""

    def __init__(self, cen=CEN_G02):
        self.cen, self.cache = cen, {}
        x_meio = [0.5 * (a + b) for a, b in BOUNDS]
        self.n_g = len(avaliar(x_meio, cen)["restr"])

    def _aval(self, x):
        k = tuple(np.round(x, 10))
        if k not in self.cache:
            try:
                r = avaliar(x, self.cen, com_estab=True)
                self.cache[k] = (r["hv"]["Hz"], r["pes"]["W_casco"], r["restr"]["_g"].values)
            except Exception:
                self.cache[k] = (1e3, 1e6, -1e3 * np.ones(self.n_g))
        return self.cache[k]

    def objetivo(self, x, w1):
        Hz, W, _ = self._aval(x)
        return w1 * Hz + (1 - w1) * W / 10000.0

    def restricoes(self, x):
        return self._aval(x)[2]


def _slsqp(fobj, x0, cons):
    return minimize(fobj, x0, method="SLSQP", bounds=BOUNDS, constraints=cons,
                    options=dict(maxiter=MAXITER, ftol=1e-8, eps=1e-5))


def _registro(r, xs):
    return dict(**dict(zip(NOMES_X, xs)), W_casco=r["pes"]["W_casco"], Hz=r["hv"]["Hz"],
                GM_T=r["pes"]["GM_T"], Tn=r["hv"]["Tn"], AB_min=r["est"]["AB_min"],
                W_lastro=r["pes"]["W_lastro"], a=r["a"], a_min=r["a_min"])


# ---- Execução paralela das partidas do SLSQP (cada processo tem seu cache) ----
N_PROCESSOS = int(os.environ.get("N_PROCESSOS", os.cpu_count() or 1))
_PROBS = {}


def _tarefa_slsqp(args):
    """Uma partida do SLSQP. tipo='ws': min w1·Hz + w2·W/1e4; tipo='eps':
    min W s.a. Hz ≤ ε. Devolve o resultado já verificado com DPHI_FINAL."""
    tipo, par, x0, origem, cen = args
    prob = _PROBS.setdefault(cen, Problema(cen))
    cons = [{"type": "ineq", "fun": prob.restricoes}]
    if tipo == "ws":
        res = _slsqp(lambda x: prob.objetivo(x, par), x0, cons)
    else:
        cons.append({"type": "ineq", "fun": lambda x: par - prob._aval(x)[0]})
        res = _slsqp(lambda x: prob._aval(x)[1] / 1e4, x0, cons)
    r = avaliar(res.x, cen, com_estab=True, dphi=DPHI_FINAL)
    ok = viavel(r) and (tipo == "ws" or r["hv"]["Hz"] <= par + 1e-4)
    return dict(origem=origem, x=res.x.copy(), success=bool(res.success), nit=int(res.nit),
                msg=str(res.message), ok=ok, reg=_registro(r, res.x))
