# -*- coding: utf-8 -*-
"""
Figuras e equações das apresentações, no estilo do layout do grupo
(azul-marinho, laranja, azul e verde-água).

Uso (na raiz do repositório), depois de rodar o modelo:
    python apresentacao/figuras_apresentacao.py
Saída: apresentacao/figuras/*.png
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "codigo"))
os.environ.setdefault("OUT_DIR", os.path.join(RAIZ, "resultados"))
import pnv3425_grupo02 as m  # noqa: E402

RES = os.path.join(RAIZ, "resultados")
FIG = os.path.join(RAIZ, "apresentacao", "figuras")
os.makedirs(FIG, exist_ok=True)

NAVY, ORANGE, BLUE, TEAL = "#0B2E40", "#E36C1E", "#2E75B6", "#1A9E8A"
GRAY, LIGHT, DECK, WATER = "#8A99A6", "#C9D3DC", "#F2B134", "#E8F0F7"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": "#4A5A66",
    "axes.labelcolor": NAVY, "axes.titlecolor": NAVY, "xtick.color": "#4A5A66",
    "ytick.color": "#4A5A66", "axes.grid": True, "grid.color": "#E3E8ED",
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": True, "legend.framealpha": 0.95, "legend.edgecolor": "#D5DCE2",
    "mathtext.fontset": "cm", "savefig.dpi": 200, "savefig.bbox": "tight",
    "axes.formatter.use_locale": False,
})


def salvar(fig, nome):
    fig.savefig(os.path.join(FIG, nome), facecolor="white")
    plt.close(fig)


def virgula(ax, eixo="both", casas=None):
    """Separador decimal com vírgula nos rótulos dos eixos."""
    from matplotlib.ticker import FuncFormatter

    def fmt(v, _):
        s = f"{v:.{casas}f}" if casas is not None else f"{v:g}"
        return s.replace(".", ",")
    if eixo in ("x", "both"):
        ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    if eixo in ("y", "both"):
        ax.yaxis.set_major_formatter(FuncFormatter(fmt))


def br(v, casas=0):
    """Número no formato brasileiro (1.234,56)."""
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def milhar(ax, eixo="x"):
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    (ax.xaxis if eixo == "x" else ax.yaxis).set_major_formatter(f)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
ficha = pd.read_csv(os.path.join(RES, "ficha_tecnica_3_cenarios.csv"), index_col=0)
DIM = ["Lp [m]", "bp [m]", "hp [m]", "bc [m]", "hc [m]", "T [m]"]
CEN = {"1": ficha.iloc[:, 0], "2": ficha.iloc[:, 1], "3": ficha.iloc[:, 2]}
X = {k: v.loc[DIM].values.astype(float) for k, v in CEN.items()}
R = {k: m.avaliar(x, dphi=m.DPHI_FINAL) for k, x in X.items()}
RV = m.avaliar(m.X_REF, m.CEN_EX, dphi=m.DPHI_FINAL)
front = pd.read_csv(os.path.join(RES, "fronteira_pareto.csv"))
am = pd.read_csv(os.path.join(RES, "amostras_variacao_sistematica.csv"))
ws = pd.read_csv(os.path.join(RES, "pareto_soma_ponderada.csv"))
eps = pd.read_csv(os.path.join(RES, "pareto_epsilon_restrito.csv"))

# ---------------------------------------------------------------------------
# 1. Curva de produção
# ---------------------------------------------------------------------------
bpd = np.array([0, 39723.62, 79447.24, 119170.86, 143005.03, 158894.48, 158894.48,
                158894.48, 150949.76, 143005.03, 127115.58, 111226.14, 95336.69,
                79447.24, 63557.79, 50846.23, 39723.62, 30189.95, 22245.23,
                15889.45, 11122.61, 6355.78, 3177.89])
fig, ax = plt.subplots(figsize=(7.2, 4.0))
cores = [ORANGE if v == bpd.max() else BLUE for v in bpd]
ax.bar(np.arange(23), bpd / 1e3, color=cores, width=0.75)
ax.axhline(bpd.max() / 1e3, c=NAVY, ls="--", lw=1)
ax.text(11.5, 166, "pico: 158.894 bpd (anos 5 a 7)", color=NAVY, ha="center", fontsize=11)
ax.set_xlabel("ano de produção"); ax.set_ylabel("produção de óleo [mil bpd]")
ax.set_ylim(0, 185); ax.set_xlim(-0.7, 22.7); ax.grid(axis="x", visible=False)
salvar(fig, "f_producao.png")

# ---------------------------------------------------------------------------
# 2. Geometria paramétrica (planta e vista lateral)
# ---------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.3), gridspec_kw=dict(width_ratios=[1, 1.15]))
for a in (a1, a2):
    a.set_aspect("equal"); a.axis("off")
L, bp, bc = 10, 1.6, 1.4
a1.add_patch(Rectangle((-L / 2, -L / 2), L, L, fc="none", ec=GRAY, ls="--", lw=1))
for y in (L / 2 - bp, -L / 2):
    a1.add_patch(Rectangle((-L / 2, y), L, bp, fc=NAVY, ec=NAVY))
for x in (-L / 2, L / 2 - bc):
    for y in (L / 2 - bp + (bp - bc) / 2, -L / 2 + (bp - bc) / 2):
        a1.add_patch(Rectangle((x, y), bc, bc, fc=TEAL, ec="white", lw=1.2))
kw = dict(arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1), color=NAVY)
a1.annotate("", (-L / 2, -L / 2 - 0.8), (L / 2, -L / 2 - 0.8), **kw)
a1.text(0, -L / 2 - 1.5, "$L_p$", ha="center", fontsize=15, color=NAVY)
a1.annotate("", (L / 2 + 0.5, L / 2 - bp), (L / 2 + 0.5, L / 2), **kw)
a1.text(L / 2 + 0.8, L / 2 - bp / 2, "$b_p$", va="center", fontsize=15, color=NAVY)
a1.annotate("", (-L / 2, L / 2 + 0.5), (-L / 2 + bc, L / 2 + 0.5), **kw)
a1.text(-L / 2 + bc / 2, L / 2 + 0.8, "$b_c$", ha="center", fontsize=15, color=NAVY)
a1.annotate("", (0, 0), (2.4, 0), arrowprops=dict(arrowstyle="<-", color=GRAY))
a1.annotate("", (0, 0), (0, 2.4), arrowprops=dict(arrowstyle="<-", color=GRAY))
a1.text(2.6, -0.1, "$x$", color=GRAY, fontsize=13); a1.text(-0.15, 2.6, "$y$", color=GRAY, fontsize=13)
a1.text(0, -L / 2 - 2.6, "planta", ha="center", color=GRAY, fontsize=12)
a1.set_xlim(-7, 7.5); a1.set_ylim(-8.3, 6.5)
hp, hc, T, hd, hm = 1.6, 4.6, 3.6, 0.9, 1.4
a2.add_patch(Rectangle((-7.2, -0.6), 14.4, T + 0.6, fc=WATER, ec="none"))
a2.add_patch(Rectangle((-L / 2, 0), L, hp, fc=NAVY))
for x in (-L / 2, L / 2 - bc):
    a2.add_patch(Rectangle((x, hp), bc, hc, fc=TEAL))
a2.add_patch(Rectangle((-L / 2, hp + hc), L, hd, fc=DECK))
a2.add_patch(Rectangle((-L / 2, hp + hc + hd), L, hm, fc=LIGHT, hatch="//", ec="white"))
a2.plot([-7.2, 7.2], [T, T], c=BLUE, ls="--", lw=1.3)
a2.text(7.3, T, "LA", color=BLUE, va="center", fontsize=11)
a2.text(0, hp + hc + hd / 2, "deck box $h_d$", ha="center", va="center", fontsize=11, color=NAVY)
a2.text(0, hp + hc + hd + hm / 2, "módulos $h_m$", ha="center", va="center", fontsize=11, color=NAVY)
a2.annotate("", (-L / 2 - 0.5, 0), (-L / 2 - 0.5, hp), **kw)
a2.text(-L / 2 - 0.8, hp / 2, "$h_p$", ha="right", va="center", fontsize=15, color=NAVY)
a2.annotate("", (-L / 2 - 0.5, hp), (-L / 2 - 0.5, hp + hc), **kw)
a2.text(-L / 2 - 0.8, hp + hc * 0.72, "$h_c$", ha="right", va="center", fontsize=15, color=NAVY)
a2.annotate("", (L / 2 + 0.5, 0), (L / 2 + 0.5, T), **kw)
a2.text(L / 2 + 0.8, T / 2, "$T$", va="center", fontsize=15, color=NAVY)
a2.annotate("", (0, T), (0, hp + hc), **kw)
a2.text(0.25, (T + hp + hc) / 2, "$a$", va="center", fontsize=15, color=NAVY)
a2.text(0, -1.5, "vista lateral", ha="center", color=GRAY, fontsize=12)
a2.set_xlim(-7.4, 8); a2.set_ylim(-2.2, 9.6)
salvar(fig, "f_geometria_param.png")

# ---------------------------------------------------------------------------
# 3. Curvas GZ e HA
# ---------------------------------------------------------------------------
VEN = list(m.VENTOS)
EST = {VEN[0]: (ORANGE, "tempestade 51,5 m/s"), VEN[1]: (BLUE, "operação 36 m/s")}


def painel_gz(ax, r, plano, phimax=45):
    e = r["est"][plano]
    ph, GZ, phal = e["phi"], e["GZ"], e["phi_al"]
    sel = ph <= phimax
    msk = ph <= phal
    ax.fill_between(ph[msk], 0, GZ[msk], color=BLUE, alpha=0.10, label="área A (0 a $\\varphi_{al}$)")
    ax.plot(ph[sel], GZ[sel], c=NAVY, lw=2.4, label="GZ")
    for nome, c in e["casos"].items():
        cor, rot = EST[nome]
        ax.plot(ph[sel], c["HA"][sel], "--", c=cor, lw=1.8, label=f"HA {rot}")
        for k, mk in (("phi1", "o"), ("phi2", "s")):
            if c[k] is not None and c[k] <= phimax:
                ax.plot(c[k], np.interp(c[k], ph, GZ), mk, c=cor, ms=7, mec="white", zorder=5)
    ax.axvline(phal, c=GRAY, ls=":", lw=1.5)
    ytop = GZ[sel].max() * 1.15
    ax.text(phal + 0.6, ytop * 0.93, f"$\\varphi_{{al}}$ = {phal:.1f}°".replace(".", ","),
            color=NAVY, fontsize=11)
    ab = min(c["AB"] for c in e["casos"].values())
    ax.set_title(f"{plano} · A/B mínimo = {br(ab, 3)}", fontsize=12, loc="left")
    ax.set_xlim(0, phimax); ax.set_ylim(-1.0, ytop)
    ax.set_xlabel("ângulo de inclinação φ [°]")
    ax.axhline(0, c="#4A5A66", lw=0.8)
    virgula(ax, "y")


def fig_gz(r, nome, phimax=45):
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.3))
    for ax, plano in zip(axs, m.PLANOS):
        painel_gz(ax, r, plano, phimax)
    axs[0].set_ylabel("GZ, HA [m]")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.07), fontsize=10)
    fig.tight_layout()
    salvar(fig, nome)


fig_gz(RV, "f_gz_validacao.png")
fig_gz(R["3"], "f_gz_final.png")
fig_gz(R["1"], "f_gz_cen1.png", phimax=25)
fig_gz(R["2"], "f_gz_cen2.png")

# ---------------------------------------------------------------------------
# 4. Pareto
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.2, 5.4))
inv = am[~am.pre_viavel]; inv2 = am[am.pre_viavel & ~am.viavel]; ok = am[am.viavel]
ax.scatter(inv.W_casco, inv.Hz, s=3, c="#D9DFE4", label="amostras inviáveis", rasterized=True)
ax.scatter(inv2.W_casco, inv2.Hz, s=9, c="#F4B183", label="reprovadas só no critério de vento")
ax.scatter(ok.W_casco, ok.Hz, s=14, c="#9DC3E6", ec=BLUE, lw=0.4, label="viáveis (LHS): 227")
ax.plot(ws.W_casco, ws.Hz, "s", c=NAVY, ms=5, label="soma ponderada (SLSQP)")
ax.plot(eps.W_casco, eps.Hz, "^", c=TEAL, ms=6, label="ε-restrito (SLSQP)")
ax.plot(front.W_casco, front.Hz, "-", c=ORANGE, lw=2.4, label="fronteira de Pareto (25 pontos)", zorder=4)
rot = {"1": ("1 · mín. peso", "#C0392B", (14, 10)), "2": ("2 · mín. heave", "#1E8449", (18, 6)),
       "3": ("3 · escolhida", ORANGE, (18, 12))}
for k, (txt, cor, off) in rot.items():
    W, H = R[k]["pes"]["W_casco"], R[k]["hv"]["Hz"]
    ax.plot(W, H, "o", ms=13, c=cor, mec="white", mew=2, zorder=6)
    ax.annotate(f"{txt}\n{br(W)} t · {br(H, 2)} m",
                (W, H), textcoords="offset points", xytext=off, fontsize=10, color=NAVY,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=cor))
ax.set_xlim(9000, 45000); ax.set_ylim(0.8, 3.0)
ax.set_xlabel("peso estrutural do casco [t]"); ax.set_ylabel("$H_{1/3,z}$ de heave [m]")
milhar(ax, "x"); virgula(ax, "y", 1)
ax.legend(fontsize=9, loc="upper right")
salvar(fig, "f_pareto.png")

# Zoom da fronteira com custo marginal
fig, ax = plt.subplots(figsize=(7.4, 4.6))
ax.plot(front.W_casco, front.Hz, "-o", c=ORANGE, ms=4, lw=2)
P = {k: (R[k]["pes"]["W_casco"], R[k]["hv"]["Hz"]) for k in R}
for k, (txt, cor, off) in rot.items():
    ax.plot(*P[k], "o", ms=12, c=cor, mec="white", mew=2, zorder=6)
for a_, b_, txt in (("1", "3", "5,7 t por mm"), ("3", "2", "17,0 t por mm")):
    (x0, y0), (x1, y1) = P[a_], P[b_]
    ax.plot([x0, x1], [y0, y1], ":", c=NAVY, lw=1.3)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.08, txt, color=NAVY, fontsize=12, ha="left",
            fontweight="bold")
for k, (txt, cor, off) in rot.items():
    ax.annotate(txt, P[k], textcoords="offset points", xytext=(10, 8), fontsize=10, color=cor)
ax.set_xlabel("peso estrutural do casco [t]"); ax.set_ylabel("$H_{1/3,z}$ [m]")
milhar(ax, "x"); virgula(ax, "y", 1); ax.set_ylim(0.9, 2.55)
salvar(fig, "f_custo_marginal.png")

# Variáveis ao longo da fronteira
fig, ax = plt.subplots(figsize=(8.6, 4.5))
cv = [NAVY, BLUE, TEAL, ORANGE, "#8E44AD", "#7F8C8D"]
for nome, (lo, hi), c in zip(m.NOMES_X, m.BOUNDS, cv):
    sub = {"Lp": "L_p", "bp": "b_p", "hp": "h_p", "bc": "b_c", "hc": "h_c", "T": "T"}[nome]
    ax.plot(front.W_casco, (front[nome] - lo) / (hi - lo), "o-", ms=3.5, lw=1.6, c=c, label=f"${sub}$")
ax.axvspan(13700, 14200, color=ORANGE, alpha=0.12)
ax.text(11300, 1.08, "rasa e larga", color=NAVY, ha="center", fontsize=11, fontweight="bold")
ax.text(19000, 1.08, "compacta e profunda", color=NAVY, ha="center", fontsize=11, fontweight="bold")
ax.set_ylim(-0.05, 1.15); ax.set_xlabel("peso estrutural do casco [t]")
ax.set_ylabel("posição no domínio (0 = mín., 1 = máx.)")
milhar(ax, "x"); virgula(ax, "y", 1)
ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=11)
salvar(fig, "f_variaveis_fronteira.png")

# ---------------------------------------------------------------------------
# 5. Geometria dos três cenários
# ---------------------------------------------------------------------------
fig, axs = plt.subplots(1, 3, figsize=(13, 4.6), sharey=True)
tit = {"1": "1 · mínimo peso", "2": "2 · mínimo heave", "3": "3 · solução escolhida"}
for ax, k in zip(axs, ("1", "2", "3")):
    Lp, bp_, hp_, bc_, hc_, T_ = X[k]
    ax.add_patch(Rectangle((-80, -5), 160, T_ + 5, fc=WATER, ec="none"))
    ax.add_patch(Rectangle((-Lp / 2, 0), Lp, hp_, fc=NAVY))
    for xc in (-Lp / 2, Lp / 2 - bc_):
        ax.add_patch(Rectangle((xc, hp_), bc_, hc_, fc=TEAL))
    ax.add_patch(Rectangle((-Lp / 2, hp_ + hc_), Lp, m.HD, fc=DECK))
    ax.add_patch(Rectangle((-Lp / 2, hp_ + hc_ + m.HD), Lp, m.HM, fc=LIGHT, hatch="//", ec="white"))
    ax.axhline(T_, c=BLUE, ls="--", lw=1.2)
    ax.axhline(T_ + m.CEN_G02.eta_max, c=ORANGE, ls=":", lw=1.4)
    ax.set_aspect("equal"); ax.set_xlim(-78, 78); ax.set_ylim(-5, 92)
    ax.set_title(tit[k], loc="left", fontsize=13, fontweight="bold")
    txt = (f"$L_p$ = {br(Lp, 1)}  $T$ = {br(T_, 1)}  $h_c$ = {br(hc_, 1)} m\n"
           f"$W_{{casco}}$ = {br(R[k]['pes']['W_casco'])} t · $H_{{1/3,z}}$ = {br(R[k]['hv']['Hz'], 2)} m")
    ax.text(0, 84, txt, ha="center", va="top",
            fontsize=10.5, color=NAVY)
    ax.set_xlabel("x [m]")
axs[0].set_ylabel("z a partir da quilha [m]")
axs[0].plot([], [], c=BLUE, ls="--", label="linha d'água")
axs[0].plot([], [], c=ORANGE, ls=":", label="crista máxima $\\eta_{max}$")
axs[0].legend(loc="center left", fontsize=9)
fig.tight_layout()
salvar(fig, "f_geometria_3.png")

# ---------------------------------------------------------------------------
# 6. Heave da solução final
# ---------------------------------------------------------------------------
hv = R["3"]["hv"]; w = hv["omega"]; sel = w <= 1.5
fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.plot(w[sel], hv["F_col"][sel] / 1e3, c=TEAL, lw=1.8, label="Froude-Krylov colunas")
ax.plot(w[sel], hv["F_pont"][sel] / 1e3, c=BLUE, lw=1.8, label="Froude-Krylov pontoons")
ax.plot(w[sel], hv["F_dif"][sel] / 1e3, c=ORANGE, lw=1.8, label="massa adicional")
ax.plot(w[sel], hv["F3"][sel] / 1e3, c=NAVY, lw=2.6, label="$F_3$ total")
ax.axvline(hv["w_cancel"], c=GRAY, ls="--", lw=1.2)
ax.text(hv["w_cancel"] + 0.02, 8.6, f"$F_3$ = 0 em {hv['w_cancel']:.3f}".replace(".", ","), color=GRAY)
ax.axhline(0, c="#4A5A66", lw=0.8)
ax.set_xlabel("frequência ω [rad/s]"); ax.set_ylabel("força por amplitude [MN/m]")
virgula(ax, "both"); ax.legend(fontsize=9, loc="upper right")
salvar(fig, "f_forcas_heave.png")

fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.plot(w[sel], hv["RAO"][sel], c=NAVY, lw=2.6, label="RAO de heave")
ax.axvline(hv["wn"], c=ORANGE, ls="--", lw=1.4, label=f"$\\omega_n$ = {hv['wn']:.3f} rad/s".replace(".", ","))
ax.axvline(hv["w_cancel"], c=GRAY, ls="--", lw=1.2, label=f"$F_3$ = 0 em {hv['w_cancel']:.3f} rad/s".replace(".", ","))
ax.axvline(2 * np.pi / m.CEN_G02.Tp, c=BLUE, ls=":", lw=1.4, label="$\\omega_p$ do mar = 0,413 rad/s")
ax.set_xlabel("frequência ω [rad/s]"); ax.set_ylabel("RAO [m/m]")
ax.set_title(f"RAO máximo {hv['RAO'].max():.2f} m/m".replace(".", ","), loc="left", fontsize=12)
virgula(ax, "both"); ax.legend(fontsize=9.5)
salvar(fig, "f_rao.png")

fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax2 = ax.twinx()
ax2.fill_between(w[sel], 0, hv["S"][sel], color=BLUE, alpha=0.12)
ax2.plot(w[sel], hv["S"][sel], c=BLUE, lw=1.2, ls=":")
ax2.set_ylabel("$S_\\zeta$ do mar [m²s]", color=BLUE); ax2.grid(False)
ax2.spines["right"].set_visible(True); ax2.tick_params(axis="y", colors=BLUE)
ax.plot(w[sel], hv["Sz"][sel], c=NAVY, lw=2.6, label="$S_z = RAO^2 S_\\zeta$")
ax.axvline(hv["wn"], c=ORANGE, ls="--", lw=1.3, label="$\\omega_n$")
ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
ax.set_xlabel("frequência ω [rad/s]"); ax.set_ylabel("$S_z$ [m²s]")
ax.set_title(f"$m_{{0z}}$ = {hv['m0z']:.4f} m² · $H_{{1/3,z}}$ = {hv['Hz']:.3f} m".replace(".", ","),
             loc="left", fontsize=12)
virgula(ax, "both"); virgula(ax2, "y"); ax.legend(fontsize=10, loc="upper right")
salvar(fig, "f_espectros.png")

# RAO dos três cenários (comparação)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.6, 5.6), sharex=True)
cc = {"1": "#C0392B", "2": "#1E8449", "3": ORANGE}
for k in ("1", "2", "3"):
    h = R[k]["hv"]
    lab = f"{tit[k]} · $T_n$ = {h['Tn']:.1f} s".replace(".", ",")
    a1.plot(w[sel], h["RAO"][sel], c=cc[k], lw=2, label=lab)
    a2.plot(w[sel], h["Sz"][sel], c=cc[k], lw=2,
            label=f"$H_{{1/3,z}}$ = {h['Hz']:.2f} m".replace(".", ","))
a2b = a2.twinx(); a2b.fill_between(w[sel], 0, hv["S"][sel], color=BLUE, alpha=0.10); a2b.grid(False)
a2b.set_yticks([])
a2.set_zorder(a2b.get_zorder() + 1); a2.patch.set_visible(False)
a1.set_ylabel("RAO [m/m]"); a2.set_ylabel("$S_z$ [m²s]"); a2.set_xlabel("frequência ω [rad/s]")
a1.legend(fontsize=9); a2.legend(fontsize=9)
for a in (a1, a2):
    virgula(a, "both")
salvar(fig, "f_heave_3cenarios.png")

# ---------------------------------------------------------------------------
# 7. Sensibilidade hd/hm
# ---------------------------------------------------------------------------
s = pd.read_csv(os.path.join(RES, "complementar", "sensibilidade_hd_hm.csv"))
fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.9))
cs = {6.0: BLUE, 8.0: NAVY, 10.0: ORANGE}
for hd, g in s.groupby("hd"):
    axs[0].plot(g.hm, g.AB_min, "o-", c=cs[hd], lw=2, label=f"$h_d$ = {hd:g} m")
    axs[1].plot(g.hm, g.GM_T, "o-", c=cs[hd], lw=2, label=f"$h_d$ = {hd:g} m")
axs[0].axhline(1.3, c="#C0392B", ls="--", lw=1.3); axs[0].text(10.1, 1.32, "A/B = 1,3", color="#C0392B")
axs[1].axhspan(1, 4, color=TEAL, alpha=0.10); axs[1].text(10.1, 3.75, "1 ≤ $GM_T$ ≤ 4 m", color=TEAL)
axs[0].set_ylabel("A/B mínimo"); axs[1].set_ylabel("$GM_T$ [m]")
for a in axs:
    a.set_xlabel("$h_m$ [m]"); virgula(a, "y"); a.legend(fontsize=9)
axs[0].plot(12, 1.303, "*", ms=16, c=ORANGE, mec="white", zorder=6)
axs[1].plot(12, 4.0, "*", ms=16, c=ORANGE, mec="white", zorder=6)
fig.tight_layout()
salvar(fig, "f_sens_hdhm.png")

# ---------------------------------------------------------------------------
# 8. Equações (mathtext)
# ---------------------------------------------------------------------------
EQ = {
    "eq_hidro": r"$\nabla = 2L_pb_ph_p + 4b_c^2\,(T-h_p) \qquad BM = \dfrac{I}{\nabla} \qquad GM = KB + BM - KG$",
    "eq_gz": r"$\sum_i t_i\,A_i^{sub}(\alpha,\varphi)=\nabla \qquad GZ(\varphi)=u_B\cos\varphi+(z_B-KG)\sin\varphi$",
    "eq_ha": r"$HA(\varphi)=\dfrac{HM_0\cos\varphi+HM_{ud}\sin\varphi}{\Delta\, g} \qquad A=\int_0^{\varphi_{al}}GZ\,d\varphi\ \geq\ 1{,}3\int_0^{\varphi_{al}}HA\,d\varphi$",
    "eq_f3": r"$\dfrac{F_3}{\zeta_a}=\cos\left(\dfrac{\omega^2 d_p}{2g}\right)\left[\rho g A_{wp}\,e^{-k(T-h_p)}-\rho g A_p\left(e^{-k(T-h_p)}-e^{-kT}\right)-A_{33}\,\omega^2 e^{-k(T-h_p/2)}\right]$",
    "eq_a33": r"$A_{33}=2\,l_d\,C_A\,\rho\pi\left(\dfrac{b_p}{2}\right)^2 \qquad C_{33}=\rho g\,4b_c^2 \qquad T_n=2\pi\sqrt{\dfrac{\Delta+A_{33}}{C_{33}}}$",
    "eq_rao": r"$RAO=\dfrac{|F_3/\zeta_a|}{|C_{33}-(\Delta+A_{33})\,\omega^2+i\,B_{33}\,\omega|} \qquad S_z=RAO^2\,S_\zeta \qquad H_{1/3,z}=4\sqrt{m_{0z}}$",
    "eq_airgap": r"$a_{min}=\dfrac{1{,}86\,H_s}{2}+\dfrac{1{,}86\,H_{1/3,z}}{2}\ \leq\ a=h_p+h_c-T$",
    "eq_obj": r"$F=w_1\,H_{1/3,z}+w_2\,\dfrac{W_{casco}}{10\,000}, \qquad w_1+w_2=1$",
    "eq_eps": r"$\min\ W_{casco}\quad \mathrm{sujeito\ a}\quad H_{1/3,z}\leq\varepsilon$",
}
for nome, tex in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1))
    f.text(0, 0, tex, fontsize=24, color=NAVY)
    f.savefig(os.path.join(FIG, nome + ".png"), dpi=220, bbox_inches="tight", pad_inches=0.04,
              transparent=True)
    plt.close(f)

print("Figuras salvas em", FIG)
