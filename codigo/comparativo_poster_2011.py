# -*- coding: utf-8 -*-
"""
PNV3425 - Grupo 02 - Comparativo com o pôster "2011 Worldwide Survey of
Semi-FPSs and FPUs" (Offshore Magazine / Mustang Engineering, jan. 2011),
referência [6] do enunciado.

Os valores foram lidos da tabela do pôster (unidades originais: pés e
toneladas). Só entram as unidades cuja linha da tabela tem a sequência de
campos inequívoca; campos ausentes ou ambíguos ficam vazios (NaN).

Gera em resultados/complementar/:
  poster2011_unidades.csv ......... dados lidos do pôster, convertidos para SI
  poster2011_validacao_casco.csv .. modelo paramétrico aplicado a semis reais
                                    de 2 pontoons e 4 colunas
  10_poster2011.png ............... dimensões da solução final x frota real
e apresentacao/figuras/f_poster2011.png
Uso (na raiz do repositório): python codigo/comparativo_poster_2011.py
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "codigo"))
os.environ.setdefault("OUT_DIR", os.path.join(RAIZ, "resultados"))
import pnv3425_grupo02 as m  # noqa: E402

RES = os.path.join(RAIZ, "resultados")
OUT = os.path.join(RES, "complementar")
FIGP = os.path.join(RAIZ, "apresentacao", "figuras")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIGP, exist_ok=True)
FT = 0.3048
nan = np.nan

# nome, local, lâmina [ft], óleo [mil bopd], nº pontoons, pontoon L, B, H [ft],
# nº colunas, coluna (lado) [ft], altura da coluna [ft], calado [ft],
# deslocamento [t], peso operacional do topside [t], nº de níveis de convés
COLS = ["nome", "local", "lamina_ft", "oleo_kbopd", "n_pont", "pont_L_ft", "pont_B_ft", "pont_H_ft",
        "n_col", "col_B_ft", "col_H_ft", "calado_ft", "desloc_t", "topside_t", "n_conves"]
DADOS = [
    ("Atlantis", "Golfo do México", 7072, 200, 4, 294, 65, 33, 4, 65, 109, 85, 89000, 25500, 2),
    ("P-52", "Brasil (Roncador)", 5888, 180, 4, nan, nan, nan, 4, 58, nan, 89, nan, 24170, nan),
    ("Troll C", "Noruega", 1115, 190, 4, 298, 55, 28, 4, 55, 130, 69, 54377, 18963, nan),
    ("Visund", "Noruega", 1099, 100, 4, 298, 55, 28, 4, 55, 130, 69, 52600, 25200, nan),
    ("Thunder Hawk", "Golfo do México", 6050, 60, 4, 140, 38, 26, 4, 46, 144, 105, 42000, 9305, 2),
    ("Opti-Ex", "Golfo do México", nan, 60, 4, 252, 30, 20, 4, 40, 138, 85, 24994, nan, 1),
    ("Blind Faith", "Golfo do México", 6494, 45, 4, 218, 44, 22, 4, nan, nan, nan, 40000, 9600, nan),
    ("Gjøa", "Noruega", 1181, nan, 4, 280, 58, 29, 4, 58, 131, nan, 58400, 22000, nan),
    ("Independence Hub", "Golfo do México (gás)", 7918, nan, 4, 141, 38, 26, 4, 46, 134, 105, 46160, 10250, 2),
    ("Veslefrikk B", "Noruega", 574, 63, 2, 353, 47, 31, 4, 41, nan, 85, 43305, nan, nan),
    ("Njord A", "Noruega", 1083, nan, 2, 328, 58, 30, 4, 52, nan, 76, 45077, nan, nan),
    ("P-20", "Brasil (Marlim)", 2051, nan, 2, 264, 52, 25, 4, 42, nan, 67, 25983, nan, nan),
]
df = pd.DataFrame(DADOS, columns=COLS)
for c in ("lamina", "pont_L", "pont_B", "pont_H", "col_B", "col_H", "calado"):
    df[c + "_m"] = df[c + "_ft"] * FT
df["desloc_por_kbopd"] = df.desloc_t / df.oleo_kbopd
df["topside_por_kbopd"] = df.topside_t / df.oleo_kbopd
df.to_csv(os.path.join(OUT, "poster2011_unidades.csv"), index=False)

# ---------------------------------------------------------------------------
# 1. Validação do casco: modelo aplicado às semis de 2 pontoons e 4 colunas
# ---------------------------------------------------------------------------
val = []
for _, r in df[df.n_pont == 2].iterrows():
    hc = r.calado_m - r.pont_H_m + 15.0        # altura da coluna não informada: irrelevante p/ ∇ e Tn
    x = [r.pont_L_m, r.pont_B_m, r.pont_H_m, r.col_B_m, hc, r.calado_m]
    h = m.hidrostatica(x)
    hv = m.heave(x, h, m.CEN_G02)
    val.append(dict(nome=r.nome, Lp_m=x[0], bp_m=x[1], hp_m=x[2], bc_m=x[3], T_m=x[5],
                    desloc_poster_t=r.desloc_t, desloc_modelo_t=h["Delta"],
                    erro_pct=100 * (h["Delta"] / r.desloc_t - 1), Tn_modelo_s=hv["Tn"],
                    Hz_mar_KZ_m=hv["Hz"]))
dv = pd.DataFrame(val)
dv.to_csv(os.path.join(OUT, "poster2011_validacao_casco.csv"), index=False)
print("Validação do casco (2 pontoons, 4 colunas):")
print(dv.round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# 2. Solução final x frota do pôster
# ---------------------------------------------------------------------------
ficha = pd.read_csv(os.path.join(RES, "ficha_tecnica_3_cenarios.csv"), index_col=0)
f3 = ficha.iloc[:, 2]
Q = 158.894
g02 = dict(calado_m=f3["T [m]"], col_B_m=f3["bc [m]"], col_H_m=f3["hc [m]"], pont_B_m=f3["bp [m]"],
           pont_H_m=f3["hp [m]"], desloc_por_kbopd=f3["Δ [t]"] / Q,
           topside_por_kbopd=f3["Peso topside [t]"] / Q)
sens = os.path.join(RES, "sensibilidade_lastro10", "ficha_tecnica_3_cenarios.csv")
g02_l = pd.read_csv(sens, index_col=0).iloc[:, 2]["Δ [t]"] / Q if os.path.exists(sens) else nan

resumo = []
for chave, rot in (("calado_m", "Calado T [m]"), ("col_B_m", "Lado da coluna b_c [m]"),
                   ("col_H_m", "Altura da coluna h_c [m]"), ("pont_B_m", "Largura do pontoon b_p [m]"),
                   ("pont_H_m", "Altura do pontoon h_p [m]"),
                   ("desloc_por_kbopd", "Δ por mil bopd [t]"), ("topside_por_kbopd", "Topside por mil bopd [t]")):
    s = df[chave].dropna()
    resumo.append(dict(grandeza=rot, n=len(s), minimo=s.min(), mediana=s.median(), maximo=s.max(),
                       G02=g02[chave]))
dr = pd.DataFrame(resumo)
dr.to_csv(os.path.join(OUT, "poster2011_resumo.csv"), index=False)
print("\nSolução escolhida x frota do pôster:")
print(dr.round(1).to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Figura
# ---------------------------------------------------------------------------
NAVY, ORANGE, BLUE, TEAL, GRAY = "#0B2E40", "#E36C1E", "#2E75B6", "#1A9E8A", "#8A99A6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#E3E8ED",
                     "axes.labelcolor": NAVY, "axes.titlecolor": NAVY, "axes.edgecolor": "#4A5A66"})
br = lambda v, k=0: f"{v:,.{k}f}".replace(",", "X").replace(".", ",").replace("X", ".")

fig = plt.figure(figsize=(15, 5.2))
gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1, 1])
ax = fig.add_subplot(gs[0])
itens = [("calado_m", "calado T"), ("col_H_m", "altura da coluna $h_c$"), ("col_B_m", "lado da coluna $b_c$"),
         ("pont_B_m", "largura do pontoon $b_p$"), ("pont_H_m", "altura do pontoon $h_p$")]
for y, (k, rot) in enumerate(itens):
    s = df[[k, "nome"]].dropna()
    ax.plot([s[k].min(), s[k].max()], [y, y], c="#C9D3DC", lw=8, solid_capstyle="round", zorder=1)
    ax.scatter(s[k], [y] * len(s), s=36, c=BLUE, ec="white", zorder=2,
               label="semis do pôster" if y == 0 else None)
    ax.scatter([g02[k]], [y], s=150, marker="D", c=ORANGE, ec="white", zorder=3,
               label="G02 · solução escolhida" if y == 0 else None)
    ax.text(g02[k], y + 0.28, br(g02[k], 1), ha="center", color=ORANGE, fontsize=10, fontweight="bold")
ax.set_yticks(range(len(itens))); ax.set_yticklabels([r for _, r in itens])
ax.set_xlabel("dimensão [m]"); ax.set_ylim(-0.6, len(itens) - 0.3); ax.invert_yaxis()
ax.set_title("(a) Dimensões do casco", loc="left", fontsize=12); ax.grid(axis="y", visible=False)
ax.legend(fontsize=9, loc="lower right")

ax = fig.add_subplot(gs[1])
s = df.dropna(subset=["topside_por_kbopd"]).sort_values("topside_por_kbopd")
ax.barh(s.nome, s.topside_por_kbopd, color=BLUE)
ax.barh(["G02 (correlação da aula)"], [g02["topside_por_kbopd"]], color=ORANGE)
for yy, v in enumerate(list(s.topside_por_kbopd) + [g02["topside_por_kbopd"]]):
    ax.text(v + 4, yy, br(v), va="center", fontsize=10, color=NAVY)
ax.set_xlabel("peso de topside por mil bopd [t]"); ax.set_xlim(0, 300)
ax.set_title("(b) Topside", loc="left", fontsize=12); ax.grid(axis="y", visible=False)

ax = fig.add_subplot(gs[2])
s = df.dropna(subset=["desloc_por_kbopd"]).sort_values("desloc_por_kbopd")
nomes = list(s.nome) + ["G02 · lastro ≥ 10%", "G02 · escolhida"]
vals = list(s.desloc_por_kbopd) + [g02_l, g02["desloc_por_kbopd"]]
ordem = np.argsort(vals)
cores = [ORANGE if nomes[i].startswith("G02") else BLUE for i in ordem]
ax.barh([nomes[i] for i in ordem], [vals[i] for i in ordem], color=cores)
for yy, i in enumerate(ordem):
    ax.text(vals[i] + 8, yy, br(vals[i]), va="center", fontsize=10, color=NAVY)
ax.set_xlabel("deslocamento por mil bopd [t]"); ax.set_xlim(0, 1000)
ax.set_title("(c) Deslocamento", loc="left", fontsize=12); ax.grid(axis="y", visible=False)
fig.tight_layout()
for p in (os.path.join(OUT, "10_poster2011.png"), os.path.join(FIGP, "f_poster2011.png")):
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
print("Figuras salvas.")
