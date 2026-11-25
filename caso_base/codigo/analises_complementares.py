# -*- coding: utf-8 -*-
"""
PNV3425 - Grupo 02 - Análises complementares para o relatório.

Roda DEPOIS de pnv3425_grupo02.py (lê os CSVs de resultados/) e gera em
resultados/complementar/:
  06_curva_producao.png ........ curva de produção do campo KZ-2026-B
  07_variaveis_fronteira.png ... variáveis de projeto ao longo da fronteira
  08_sensibilidade_hd_hm.png ... A/B e KG da solução final x hd e hm
  restricoes_ativas_fronteira.csv, custo_marginal.csv,
  sensibilidade_hd_hm.csv, sensibilidade_heave.csv

Uso (na pasta caso_base/):  python codigo/analises_complementares.py
"""
import os
import sys
import dataclasses

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pnv3425_grupo02 as m  # noqa: E402

RES = m.OUT_DIR
OUT = os.path.join(RES, "complementar")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Curva de produção (dados do campo designado)
# ---------------------------------------------------------------------------
anos = np.arange(23)
bpd = np.array([0, 39723.62, 79447.24, 119170.86, 143005.03, 158894.48, 158894.48,
                158894.48, 150949.76, 143005.03, 127115.58, 111226.14, 95336.69,
                79447.24, 63557.79, 50846.23, 39723.62, 30189.95, 22245.23,
                15889.45, 11122.61, 6355.78, 3177.89])
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(anos, bpd / 1e3, color="tab:green", alpha=.8)
ax.axhline(bpd.max() / 1e3, c="k", ls="--", lw=1)
ax.text(12, bpd.max() / 1e3 + 3, f"pico = {bpd.max():,.0f} bpd (anos 5 a 7)".replace(",", "."),
        ha="center")
ax.set_xlabel("Ano de produção"); ax.set_ylabel("Produção de óleo [mil bpd]")
ax.set_title("Curva de produção - bloco KZ-2026-B", fontweight="bold")
ax.set_ylim(0, 185); ax.grid(ls="--", alpha=.5)
acum = np.trapezoid(bpd, anos) * 365 / 1e6 if hasattr(np, "trapezoid") else np.trapz(bpd, anos) * 365 / 1e6
print(f"Produção acumulada da curva (trapézios): {acum:,.0f} milhões de bbl "
      f"(reserva recuperável: {m.OLEO_RECUP_BBL/1e6:,.0f} milhões)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "06_curva_producao.png"), dpi=150)

# ---------------------------------------------------------------------------
# 2. Fronteira: variáveis, restrições ativas e custo marginal
# ---------------------------------------------------------------------------
front = pd.read_csv(os.path.join(RES, "fronteira_pareto.csv"))
lin = []
for _, p in front.iterrows():
    r = m.avaliar(p[m.NOMES_X].values.astype(float), dphi=m.DPHI_FINAL)
    at = r["restr"].loc[r["restr"].Ativa == "ATIVA", "Restrição"].tolist()
    lin.append(dict(W_casco=r["pes"]["W_casco"], Hz=r["hv"]["Hz"], Tn=r["hv"]["Tn"],
                    W_lastro=r["pes"]["W_lastro"], AB=r["est"]["AB_min"],
                    ativas="; ".join(at), no_limite="; ".join(m.variaveis_no_limite(r["x"]))))
df_at = pd.concat([front[m.NOMES_X + ["origem"]], pd.DataFrame(lin)], axis=1)
df_at.to_csv(os.path.join(OUT, "restricoes_ativas_fronteira.csv"), index=False)
cont = pd.Series([a for s in df_at.ativas for a in s.split("; ") if a]).value_counts()
print("\nRestrições ativas ao longo da fronteira (nº de pontos em", len(df_at), "):")
print(cont.to_string())

fig, ax = plt.subplots(figsize=(10, 5))
for nome, (lo, hi) in zip(m.NOMES_X, m.BOUNDS):
    ax.plot(front.W_casco, (front[nome] - lo) / (hi - lo), "o-", ms=4, label=nome)
ax.set_xlabel("Peso estrutural do casco [t]")
ax.set_ylabel("(x − x_mín)/(x_máx − x_mín)")
ax.set_title("Variáveis de projeto ao longo da fronteira de Pareto (0 = limite inferior, 1 = superior)",
             fontweight="bold", fontsize=11)
ax.set_ylim(-0.05, 1.05); ax.grid(ls="--", alpha=.5)
ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.13))
fig.tight_layout(); fig.savefig(os.path.join(OUT, "07_variaveis_fronteira.png"), dpi=150)

ficha = pd.read_csv(os.path.join(RES, "ficha_tecnica_3_cenarios.csv"), index_col=0)
W = ficha.loc["Peso casco [t]"].values
Hcol = [i for i in ficha.index if i.startswith("H1/3 heave γ=3.3")][0]
H = ficha.loc[Hcol].values
cm = pd.DataFrame([("Cenário 1 → 3", W[2] - W[0], H[0] - H[2]),
                   ("Cenário 3 → 2", W[1] - W[2], H[2] - H[1])],
                  columns=["Trecho", "dW_t", "dHz_m"])
cm["t_por_mm"] = cm.dW_t / (cm.dHz_m * 1000)
cm.to_csv(os.path.join(OUT, "custo_marginal.csv"), index=False)
print("\nCusto marginal:\n", cm.round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Sensibilidade da solução final a hd e hm (geometria fixa)
# ---------------------------------------------------------------------------
xK = ficha.loc[["Lp [m]", "bp [m]", "hp [m]", "bc [m]", "hc [m]", "T [m]"],
               "3. Intermediária (escolhida)"].values.astype(float)
sens = []
for hd in (6.0, 8.0, 10.0):
    for hm in (10.0, 12.0, 15.0):
        c = dataclasses.replace(m.CEN_G02, hd=hd, hm=hm)
        r = m.avaliar(xK, c, dphi=m.DPHI_FINAL)
        sens.append(dict(hd=hd, hm=hm, KG=r["pes"]["KG"], GM_T=r["pes"]["GM_T"],
                         AB_min=r["est"]["AB_min"], viavel=m.viavel(r)))
df_s = pd.DataFrame(sens)
df_s.to_csv(os.path.join(OUT, "sensibilidade_hd_hm.csv"), index=False)
print("\nSensibilidade a hd/hm (geometria da solução final):\n", df_s.round(3).to_string(index=False))

fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for hd, g in df_s.groupby("hd"):
    axs[0].plot(g.hm, g.AB_min, "o-", label=f"hd = {hd:g} m")
    axs[1].plot(g.hm, g.GM_T, "o-", label=f"hd = {hd:g} m")
axs[0].axhline(m.AB_MIN, c="r", ls="--", label="A/B = 1,3")
axs[1].axhspan(m.GM_MIN, m.GM_MAX, color="g", alpha=.08, label="1 ≤ GM_T ≤ 4 m")
axs[0].set_ylabel("min A/B [-]"); axs[1].set_ylabel("GM_T [m]")
for ax in axs:
    ax.set_xlabel("hm [m]"); ax.grid(ls="--", alpha=.5); ax.legend(fontsize=8)
fig.suptitle("Solução final com hd e hm alterados (geometria fixa)", fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "08_sensibilidade_hd_hm.png"), dpi=150)

# ---------------------------------------------------------------------------
# 4. Sensibilidade do heave a γ e ξ (geometria fixa)
# ---------------------------------------------------------------------------
hid = m.hidrostatica(xK)
lin = []
xi0 = m.XI_HEAVE
for xi in (0.03, 0.05, 0.08):
    m.XI_HEAVE = xi
    for g in (1.0, 3.3):
        hv = m.heave(xK, hid, m.CEN_G02, gamma=g)
        lin.append(dict(xi=xi, gamma=g, Hz=hv["Hz"], RAO_max=hv["RAO"].max(),
                        a_min=m.CEN_G02.eta_max + 1.86 * hv["Hz"] / 2))
m.XI_HEAVE = xi0
df_h = pd.DataFrame(lin)
df_h.to_csv(os.path.join(OUT, "sensibilidade_heave.csv"), index=False)
print("\nSensibilidade do heave (solução final):\n", df_h.round(3).to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Conferência do η_max do enunciado (Hs = 12,2 m -> 11,35 m)
# ---------------------------------------------------------------------------
print(f"\nη_max da plataforma de referência = {m.CEN_EX.eta_max:.3f} m (enunciado: 11,35 m)")
