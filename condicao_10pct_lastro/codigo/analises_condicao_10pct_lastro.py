# -*- coding: utf-8 -*-
"""
PNV3425 - Grupo 02 - Condição de 10% de lastro: análises complementares.

Roda DEPOIS de pnv3425_grupo02_condicao_10pct_lastro.py (lê resultados_lastro10/)
e da versão caso-base (lê ../caso_base/resultados/). Gera:

  resultados_lastro10/complementar/
    11_fronteiras_base_x_lastro10.png ... as duas fronteiras de Pareto
    12_variaveis_fronteira.png .......... variáveis ao longo da fronteira
    13_poster2011.png ................... solução escolhida x frota do pôster
    restricoes_ativas_fronteira.csv, comparacao_base_x_lastro10.csv,
    custo_marginal.csv, poster2011_resumo.csv
  relatorio/tabelas/*.tex ............... tabelas do relatório desta versão

Uso (na pasta condicao_10pct_lastro/):
    python codigo/analises_condicao_10pct_lastro.py
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
RES = os.path.join(RAIZ, "resultados_lastro10")
BASE = os.path.join(RAIZ, "..", "caso_base", "resultados")
os.environ["OUT_DIR"] = RES
sys.path.insert(0, os.path.join(RAIZ, "codigo"))
import pnv3425_grupo02_condicao_10pct_lastro as m  # noqa: E402

OUT = os.path.join(RES, "complementar")
TEX = os.path.join(RAIZ, "relatorio", "tabelas")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TEX, exist_ok=True)
DIM = ["Lp [m]", "bp [m]", "hp [m]", "bc [m]", "hc [m]", "T [m]"]
NOMES = ("1. Mín. peso", "2. Mín. heave", "3. Intermediária (escolhida)")


def br(v, k=0):
    """Número no formato brasileiro (1.234,56)."""
    return f"{v:,.{k}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tex(nome, linhas):
    with open(os.path.join(TEX, nome), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


# ---------------------------------------------------------------------------
# Dados das duas versões
# ---------------------------------------------------------------------------
fic = pd.read_csv(os.path.join(RES, "ficha_tecnica_3_cenarios.csv"), index_col=0)
fic_b = pd.read_csv(os.path.join(BASE, "ficha_tecnica_3_cenarios.csv"), index_col=0)
front = pd.read_csv(os.path.join(RES, "fronteira_pareto.csv"))
front_b = pd.read_csv(os.path.join(BASE, "fronteira_pareto.csv"))
R = {k: m.avaliar(fic[k].loc[DIM].values.astype(float), dphi=m.DPHI_FINAL) for k in NOMES}
r1, r2, r3 = (R[k] for k in NOMES)
Q = m.CEN_G02.Q

# ---------------------------------------------------------------------------
# 1. Restrições ativas e variáveis no limite ao longo da fronteira
# ---------------------------------------------------------------------------
lin = []
for _, p in front.iterrows():
    r = m.avaliar(p[m.NOMES_X].values.astype(float), dphi=m.DPHI_FINAL)
    at = r["restr"].loc[r["restr"].Ativa == "ATIVA", "Restrição"].tolist()
    lin.append(dict(W_casco=r["pes"]["W_casco"], Hz=r["hv"]["Hz"], Tn=r["hv"]["Tn"],
                    W_lastro=r["pes"]["W_lastro"], ativas="; ".join(at),
                    no_limite="; ".join(m.variaveis_no_limite(r["x"]))))
df_at = pd.concat([front[m.NOMES_X + ["origem"]], pd.DataFrame(lin)], axis=1)
df_at.to_csv(os.path.join(OUT, "restricoes_ativas_fronteira.csv"), index=False)
cont = pd.Series([a for s in df_at.ativas for a in s.split("; ") if a]).value_counts()
print("Restrições ativas ao longo da fronteira:\n", cont.to_string())
rot = {"GM_T máximo": "$GM_T = 4$~m", "Critério de áreas min(A/B), 4 casos": "$A/B = 1{,}30$",
       "V_lastro ≥ 10%·V_pontoons (obrigatório)": "$V_{lastro} = 0{,}10\\,V_{pontoons}$",
       "bc ≤ bp": "$b_c = b_p$", "Área de convés Lp²": "área de convés mínima",
       "Peso de lastro positivo": "lastro positivo"}
L = ["\\begin{tabular}{lr}", "\\toprule", "Restrição ativa & Pontos \\\\", "\\midrule"]
for k, v in cont.items():
    L.append(f"{rot.get(k, k)} & {v} / {len(df_at)} \\\\")
L += ["\\emph{Air gap} e $T_n$ & 0 / %d \\\\" % len(df_at), "\\bottomrule", "\\end{tabular}"]
tex("tab_ativas.tex", L)

# ---------------------------------------------------------------------------
# 2. Ficha técnica dos três cenários
# ---------------------------------------------------------------------------
def col(k):
    return fic[k]


L = []
lin_f = [("$L_p$ [m]", "Lp [m]", 2), ("$b_p$ [m]", "bp [m]", 2), ("$h_p$ [m]", "hp [m]", 2),
         ("$b_c$ [m]", "bc [m]", 2), ("$h_c$ [m]", "hc [m]", 2), ("$T$ [m]", "T [m]", 2),
         ("Área de convés [m$^2$]", "Área de convés [m²]", 0), None,
         ("$\\nabla$ [m$^3$]", "∇ [m³]", 0), ("$\\Delta$ [t]", "Δ [t]", 0), ("KB [m]", "KB [m]", 2),
         None, ("\\textbf{Peso do casco [t]}", "Peso casco [t]", 0),
         ("Peso do \\emph{topside} [t]", "Peso topside [t]", 0),
         ("\\emph{Risers} + amarração [t]", "Risers + amarração [t]", 0),
         ("\\textbf{Lastro [t]}", "Peso lastro [t]", 0),
         ("$V_{lastro}/V_{pontoons}$", "V lastro / V pontoons [-]", 3), ("KG [m]", "KG [m]", 2),
         ("$GM_T$ [m]", "GM_T [m]", 2), ("$GM_L$ [m]", "GM_L [m]", 2), None,
         ("$\\phial$ transversal [$^\\circ$]", "φal transversal [°]", 2),
         ("$\\phial$ longitudinal [$^\\circ$]", "φal longitudinal [°]", 2),
         ("$\\min A/B$ (4 casos)", "min A/B (4 casos) [-]", 3), None,
         ("$A_{33}$ [t]", "A33 [t]", 0), ("$C_{33}$ [kN/m]", "C33 [kN/m]", 0), ("$T_n$ [s]", "Tn [s]", 2),
         ("\\textbf{$\\Hz$, $\\gamma = 3{,}3$ [m]}", "H1/3 heave γ=3.3 [m]", 3),
         ("$\\Hz$, $\\gamma = 1$ [m]", "H1/3 heave γ=1 [m]", 3), None,
         ("$\\eta_{max}$ [m]", "η_max [m]", 2), ("$z_{min}$ [m]", "z_min [m]", 2),
         ("$a_{\\text{mín}}$ [m]", "a_mín [m]", 2), ("$a$ [m]", "a [m]", 2)]
for item in lin_f:
    if item is None:
        L.append("\\midrule")
        continue
    rotulo, chave, k = item
    vals = [br(fic[n][chave], k) for n in NOMES]
    if rotulo.startswith("\\textbf"):
        vals = [f"\\textbf{{{v}}}" for v in vals]
    L.append(f"{rotulo} & " + " & ".join(vals) + " \\\\")


def ativas(r):
    t = r["restr"]
    nomes = t.loc[t.Ativa == "ATIVA", "Restrição"].tolist()
    curto = {"GM_T máximo": "$GM_T$", "Critério de áreas min(A/B), 4 casos": "$A/B$",
             "V_lastro ≥ 10%·V_pontoons (obrigatório)": "lastro 10\\%", "bc ≤ bp": "$b_c{=}b_p$",
             "Área de convés Lp²": "área"}
    return ", ".join(curto.get(n, n) for n in nomes)


def limites(r):
    s = m.variaveis_no_limite(r["x"])
    if not s:
        return "nenhuma"
    sub = {"Lp": "$L_p$", "bp": "$b_p$", "hp": "$h_p$", "bc": "$b_c$", "hc": "$h_c$", "T": "$T$"}
    return ", ".join(f"{sub[i.split()[0]]} {'mín.' if 'mín' in i else 'máx.'}" for i in s)


L += ["\\midrule", "Restrições ativas & " + " & ".join(ativas(R[n]) for n in NOMES) + " \\\\",
      "Variáveis no limite & " + " & ".join(limites(R[n]) for n in NOMES) + " \\\\"]
tex("tab_ficha_linhas.tex", L)

# ---------------------------------------------------------------------------
# 3. Solução final: pesos, vento, critério, heave, air gap, restrições
# ---------------------------------------------------------------------------
tp = m.tabela_pesos(r3["pes"])
L = ["\\begin{tabular}{lrrr}", "\\toprule", "Item & Peso [t] & VCG [m] & Momento [t$\\cdot$m] \\\\",
     "\\midrule"]
for _, l in tp.iterrows():
    nome = l.Item.replace("Pontoons", "\\emph{Pontoons}").replace("Risers", "\\emph{Risers}")
    if l.Item.startswith("TOTAL"):
        L += ["\\midrule", f"\\textbf{{Total ($=\\Delta$)}} & \\textbf{{{br(l.Peso_t, 1)}}} & "
                           f"\\textbf{{{br(l.VCG_m, 2)}}} & \\textbf{{{br(l.Momento_tm)}}} \\\\"]
    else:
        L.append(f"{nome} & {br(l.Peso_t, 1)} & {br(l.VCG_m, 2)} & {br(l.Momento_tm)} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
tex("tab_pesos.tex", L)

ven = r3["est"]["vento"]
kT, kL = ven["Transversal"], ven["Longitudinal"]
V1, V2 = list(m.VENTOS)
nomes_p = ["Colunas (4)", "\\emph{Deck box}", "Módulos", "Face inferior"]
L = ["\\begin{tabular}{lrrrrrrrr}", "\\toprule",
     " & & & & & \\multicolumn{2}{c}{Força [kN]} & \\multicolumn{2}{c}{Braço [m]} \\\\",
     "\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}",
     "Parcela & Área [m$^2$] & $z$ [m] & $C_s$ & $C_h$ & 51,5 m/s & 36 m/s & Transv. & Long. \\\\",
     "\\midrule"]
for i, nome in enumerate(nomes_p):
    a, b, c = kT[V1][0][i], kT[V2][0][i], kL[V1][0][i]
    L.append(f"{nome} & {br(a['Area_m2'], 1)} & {br(a['z_LA_m'], 2)} & {br(a['Cs'], 1)} & "
             f"{br(a['Ch'], 2)} & {br(a['Forca_kN'], 1)} & {br(b['Forca_kN'], 1)} & "
             f"{br(a['Braco_m'], 2)} & {br(c['Braco_m'], 2)} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
tex("tab_vento_forcas.tex", L)

L = ["\\begin{tabular}{lrrrr}", "\\toprule",
     " & \\multicolumn{2}{c}{Transversal} & \\multicolumn{2}{c}{Longitudinal} \\\\",
     "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
     "Parcela & 51,5 m/s & 36 m/s & 51,5 m/s & 36 m/s \\\\", "\\midrule"]
for i, nome in enumerate(nomes_p[:3]):
    L.append(f"{nome} & " + " & ".join(br(d[v][0][i]["Momento_kNm"]) for d in (kT, kL)
                                       for v in (V1, V2)) + " \\\\")
L += ["\\midrule",
      "$HM_0$ & " + " & ".join(br(d[v][1]) for d in (kT, kL) for v in (V1, V2)) + " \\\\",
      "$HM_{ud}$ (face inferior) & " + " & ".join(br(d[v][2]) for d in (kT, kL) for v in (V1, V2)) + " \\\\",
      "\\bottomrule", "\\end{tabular}"]
tex("tab_vento_momentos.tex", L)

crit = m.tabela_criterio(r3)
L = []
for _, c in crit.iterrows():
    ab = br(c["A/B"], 3)
    if c["A/B"] < 1.35:
        ab = f"\\textbf{{{ab}}}"
    phi2 = br(c["φ2 [°]"], 2) if pd.notna(c["φ2 [°]"]) else "--"
    L.append(f"{'Transv.' if c.Plano == 'Transversal' else 'Long.'} & {c.Vento.split()[-2]} m/s & "
             f"{br(c['z_CLR [m]'], 2)} & {br(c['HA(0) [m]'], 3)} & {br(c['φ1 [°]'], 2)} & {phi2} & "
             f"{br(c['φal [°]'], 2)} & {br(c['A [m·rad]'], 3)} & {br(c['B [m·rad]'], 3)} & {ab} \\\\")
tex("tab_criterio_linhas.tex", L)

hv = r3["hv"]
wp = 2 * np.pi / m.CEN_G02.Tp
jp = int(np.argmin(np.abs(hv["omega"] - wp)))
L = ["\\begin{tabular}{lr@{\\hspace{1.5cm}}lr}", "\\toprule", "Grandeza & Valor & Grandeza & Valor \\\\",
     "\\midrule",
     f"$\\Delta$ [t] & {br(hv['M'])} & $\\omega_n$ [rad/s] & {br(hv['wn'], 4)} \\\\",
     f"$C_A$ & {br(hv['CA'], 3)} & $T_n$ [s] & {br(hv['Tn'], 2)} \\\\",
     f"$l_d$ [m] & {br(hv['ld'], 2)} & $\\omega$ de cancelamento [rad/s] & {br(hv['w_cancel'], 3)} \\\\",
     f"$A_{{33}}$ [t] & {br(hv['A33'])} & RAO máximo & {br(hv['RAO'].max(), 2)} \\\\",
     f"$C_{{33}}$ [kN/m] & {br(hv['C33'])} & RAO no pico do mar & {br(hv['RAO'][jp], 2)} \\\\",
     f"$B_{{33}}$ [kN$\\cdot$s/m] & {br(hv['B33'])} & $m_{{0z}}$ [m$^2$] & {br(hv['m0z'], 4)} \\\\",
     f" & & $\\Hz$ ($\\gamma = 3{{,}}3$ / $\\gamma = 1$) [m] & {br(hv['Hz'], 3)} / {br(hv['Hz_alt'], 3)} \\\\",
     "\\bottomrule", "\\end{tabular}"]
tex("tab_heave.tex", L)

L = ["\\begin{tabular}{lr}", "\\toprule", "Grandeza & Valor [m] \\\\", "\\midrule",
     f"$\\eta_{{max}} = 1{{,}}86 \\times 5{{,}}6/2$ & {br(r3['eta_max'], 3)} \\\\",
     f"$z_{{min}} = -1{{,}}86 \\times {br(hv['Hz'], 3)}/2$ & $-{br(-r3['z_min'], 3)}$ \\\\",
     f"$a_{{\\text{{mín}}}} = \\eta_{{max}} - z_{{min}}$ & {br(r3['a_min'], 3)} \\\\",
     f"$a = h_p + h_c - T$ & {br(r3['a'], 3)} \\\\",
     f"Folga $a - a_{{\\text{{mín}}}}$ & {br(r3['a'] - r3['a_min'], 3)} \\\\",
     "\\bottomrule", "\\end{tabular}"]
tex("tab_airgap.tex", L)

nomes_r = {"Área de convés Lp²": "Área de convés $L_p^2$", "GM_T mínimo": "$GM_T$ mínimo",
           "GM_T máximo": "$GM_T$ máximo", "Período natural de heave Tn": "$T_n$",
           "Peso de lastro positivo": "Lastro positivo",
           "V_lastro ≤ 0,9·V_pontoons": "$V_{lastro} \\le 0{,}9 V_{pontoons}$",
           "bc ≤ bp": "$b_c \\le b_p$", "Air gap a ≥ a_mín": "\\emph{Air gap} $a \\ge a_{\\text{mín}}$",
           "Imersão das colunas T−hp (geométrica)": "$T - h_p$ (geométrica)",
           "V_lastro ≥ 10%·V_pontoons (obrigatório)": "\\textbf{$V_{lastro} \\ge 0{,}10 V_{pontoons}$}",
           "Critério de áreas min(A/B), 4 casos": "$\\min A/B$ (4 casos)",
           "GZ>0 até φ2/φal: min(GZ/senφ)": "$GZ > 0$: $\\min(GZ/\\sin\\varphi)$"}
sent = {"≥": "$\\ge$", "≤": "$\\le$", ">": "$>$"}
ATIVA = "\\textbf{ativa}"
L = []
for _, l in r3["restr"].iterrows():
    k = 1 if abs(l.Valor) >= 100 else 3
    L.append(f"{nomes_r[l['Restrição']]} & {l.Unid.replace('m²', 'm$^2$').replace('m³', 'm$^3$')} & "
             f"{br(l.Valor, k)} & {sent[l.Sentido]} & {br(l.Limite, k)} & {br(l.Folga, k)} & "
             f"{br(l.Folga_pct, 1)} & {ATIVA if l.Ativa else ''} \\\\")
tex("tab_restricoes_linhas.tex", L)

# ---------------------------------------------------------------------------
# 4. Custo marginal e comparação com o caso-base
# ---------------------------------------------------------------------------
W = [R[n]["pes"]["W_casco"] for n in NOMES]
H = [R[n]["hv"]["Hz"] for n in NOMES]
cm = pd.DataFrame([("Cenário 1 → 3", W[2] - W[0], H[0] - H[2]), ("Cenário 3 → 2", W[1] - W[2], H[2] - H[1])],
                  columns=["Trecho", "dW_t", "dHz_m"])
cm["t_por_mm"] = cm.dW_t / (cm.dHz_m * 1000)
cm.to_csv(os.path.join(OUT, "custo_marginal.csv"), index=False)
SETA = "$\\to$"
L = []
for _, l in cm.iterrows():
    trecho = l.Trecho.replace("→", SETA)
    L.append(f"{trecho} & {br(l.dW_t)} t & {br(l.dHz_m, 2)} m & {br(l.t_por_mm, 1)} \\\\")
tex("tab_custo_linhas.tex", L)
print("\nCusto marginal:\n", cm.round(2).to_string(index=False))
trade = dict(corte_heave=100 * (1 - H[1] / H[0]), acrescimo_W=100 * (W[1] / W[0] - 1),
             ganho_capturado=100 * (H[0] - H[2]) / (H[0] - H[1]),
             massa_usada=100 * (W[2] - W[0]) / (W[1] - W[0]))
print("Trade-off:", {k: round(v, 1) for k, v in trade.items()})

b3 = fic_b.iloc[:, 2]
c3 = fic.iloc[:, 2]
comp = [("Peso do casco [t]", "Peso casco [t]", 0), ("Peso de lastro [t]", "Peso lastro [t]", 0),
        ("$\\Delta$ [t]", "Δ [t]", 0), ("$L_p$ [m]", "Lp [m]", 2), ("$T$ [m]", "T [m]", 2),
        ("$h_c$ [m]", "hc [m]", 2), ("$b_c$ [m]", "bc [m]", 2), ("$h_p$ [m]", "hp [m]", 2),
        ("KG [m]", "KG [m]", 2), ("BM$_T$ [m]", "BM_T [m]", 2), ("$GM_T$ [m]", "GM_T [m]", 2),
        ("$\\phial$ transversal [$^\\circ$]", "φal transversal [°]", 2),
        ("$\\min A/B$", "min A/B (4 casos) [-]", 3), ("$T_n$ [s]", "Tn [s]", 2),
        ("$\\Hz$ [m]", "H1/3 heave γ=3.3 [m]", 3), ("Folga de \\emph{air gap} [m]", "Folga air gap [m]", 2)]
L, regs = [], []
for rotulo, chave, k in comp:
    vb, vl = b3[chave], c3[chave]
    d = vl - vb
    if round(d, k) == 0:
        var = "0"
    elif abs(vb) > 50:
        var = f"{100 * (vl / vb - 1):+.1f}\\%".replace(".", ",")
    else:
        var = ("+" if d > 0 else "$-$") + br(abs(d), k)
    L.append(f"{rotulo} & {br(vb, k)} & {br(vl, k)} & {var} \\\\")
    regs.append(dict(grandeza=chave, caso_base=vb, lastro10=vl))
L.append(f"$\\Delta$ por mil bopd [t] & {br(b3['Δ [t]'] / Q)} & {br(c3['Δ [t]'] / Q)} & "
         f"{100 * (c3['Δ [t]'] / b3['Δ [t]'] - 1):+.1f}\\% \\\\".replace(".", ",", 1))
pd.DataFrame(regs).to_csv(os.path.join(OUT, "comparacao_base_x_lastro10.csv"), index=False)
tex("tab_comparacao_linhas.tex", L)

L = ["\\begin{tabular}{lrrrr}", "\\toprule",
     "Cenário & \\multicolumn{2}{c}{Peso do casco [t]} & \\multicolumn{2}{c}{$\\Hz$ [m]} \\\\",
     "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}", " & Caso-base & Lastro $\\ge$ 10\\% & Caso-base & Lastro $\\ge$ 10\\% \\\\",
     "\\midrule"]
for i, n in enumerate(NOMES):
    rot_c = ["1 · Mín. peso", "2 · Mín. \\emph{heave}", "3 · Escolhida"][i]
    L.append(f"{rot_c} & {br(fic_b.iloc[:, i]['Peso casco [t]'])} & {br(fic[n]['Peso casco [t]'])} & "
             f"{br(fic_b.iloc[:, i]['H1/3 heave γ=3.3 [m]'], 3)} & {br(fic[n]['H1/3 heave γ=3.3 [m]'], 3)} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
tex("tab_cenarios_base_x_lastro.tex", L)

# ---------------------------------------------------------------------------
# 5. Fronteira completa (apêndice)
# ---------------------------------------------------------------------------
L = []
i3 = int(np.argmin(np.abs(front.W_casco - r3["pes"]["W_casco"])))
for i, p in front.iterrows():
    orig = "SP" if p.origem.startswith("Soma") else "$\\varepsilon$"
    extra = " (cen. 1)" if i == front.W_casco.idxmin() else (
        " (cen. 2)" if i == front.Hz.idxmin() else (" (cen. 3)" if i == i3 else ""))
    L.append(f"{i + 1} & " + " & ".join(br(p[c], 2) for c in m.NOMES_X) +
             f" & {br(p.W_casco)} & {br(p.Hz, 3)} / {orig}{extra} \\\\")
tex("tab_fronteira_linhas.tex", L)

# ---------------------------------------------------------------------------
# 6. Pôster de 2011
# ---------------------------------------------------------------------------
pst = pd.read_csv(os.path.join(BASE, "complementar", "poster2011_unidades.csv"))
x3 = dict(calado_m=c3["T [m]"], col_H_m=c3["hc [m]"], col_B_m=c3["bc [m]"], pont_B_m=c3["bp [m]"],
          pont_H_m=c3["hp [m]"], desloc_por_kbopd=c3["Δ [t]"] / Q, topside_por_kbopd=c3["Peso topside [t]"] / Q)
itens = [("calado_m", "Calado $T$ [m]", 1), ("col_H_m", "Altura da coluna $h_c$ [m]", 1),
         ("col_B_m", "Lado da coluna $b_c$ [m]", 1), ("pont_B_m", "Largura do \\emph{pontoon} $b_p$ [m]", 1),
         ("pont_H_m", "Altura do \\emph{pontoon} $h_p$ [m]", 1),
         ("topside_por_kbopd", "\\emph{Topside} por mil bopd [t]", 0),
         ("desloc_por_kbopd", "$\\Delta$ por mil bopd [t]", 0)]
L, regs = [], []
for k, rotulo, d in itens:
    s = pst[k].dropna()
    L.append(f"{rotulo} & {len(s)} & {br(s.min(), d)} & {br(s.median(), d)} & {br(s.max(), d)} & {br(x3[k], d)} \\\\")
    regs.append(dict(grandeza=k, n=len(s), minimo=s.min(), mediana=s.median(), maximo=s.max(), lastro10=x3[k]))
pd.DataFrame(regs).to_csv(os.path.join(OUT, "poster2011_resumo.csv"), index=False)
tex("tab_poster_linhas.tex", L)

# ---------------------------------------------------------------------------
# 7. Figuras
# ---------------------------------------------------------------------------
NAVY, ORANGE, BLUE, TEAL, GRAY = "#0B2E40", "#E36C1E", "#2E75B6", "#1A9E8A", "#8A99A6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#E3E8ED",
                     "axes.labelcolor": NAVY, "axes.titlecolor": NAVY, "axes.edgecolor": "#4A5A66"})
fmt_m = FuncFormatter(lambda v, _: br(v))
fmt_d = FuncFormatter(lambda v, _: br(v, 1))

fig, ax = plt.subplots(figsize=(9.5, 5.4))
ax.plot(front_b.W_casco, front_b.Hz, "-o", c=GRAY, ms=4, lw=2, label="caso-base (lastro > 0)")
ax.plot(front.W_casco, front.Hz, "-o", c=ORANGE, ms=4, lw=2.4, label="condição de 10% de lastro")
for i in range(3):
    ax.plot(fic_b.iloc[:, i]["Peso casco [t]"], fic_b.iloc[:, i]["H1/3 heave γ=3.3 [m]"], "s", ms=10,
            c="white", mec=GRAY, mew=2, zorder=5)
    ax.plot(fic.iloc[:, i]["Peso casco [t]"], fic.iloc[:, i]["H1/3 heave γ=3.3 [m]"], "o", ms=11,
            c=ORANGE, mec="white", mew=2, zorder=6)
ax.annotate(f"escolhida (10% lastro)\n{br(W[2])} t · {br(H[2], 2)} m", (W[2], H[2]), xytext=(25, 22),
            textcoords="offset points", color=NAVY, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=ORANGE))
wb, hb = fic_b.iloc[:, 2]["Peso casco [t]"], fic_b.iloc[:, 2]["H1/3 heave γ=3.3 [m]"]
ax.annotate(f"escolhida (caso-base)\n{br(wb)} t · {br(hb, 2)} m", (wb, hb), xytext=(-150, -45),
            textcoords="offset points", color=GRAY, fontsize=10, arrowprops=dict(arrowstyle="-", color=GRAY))
ax.set_xlabel("peso estrutural do casco [t]"); ax.set_ylabel("$H_{1/3,z}$ de heave [m]")
ax.xaxis.set_major_formatter(fmt_m); ax.yaxis.set_major_formatter(fmt_d)
ax.legend(fontsize=10, loc="upper right")
ax.set_title("Fronteiras de Pareto: caso-base × condição de 10% de lastro", loc="left", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "11_fronteiras_base_x_lastro10.png"), dpi=200)

fig, ax = plt.subplots(figsize=(10, 5))
cv = [NAVY, BLUE, TEAL, ORANGE, "#8E44AD", "#7F8C8D"]
for nome, (lo, hi), c in zip(m.NOMES_X, m.BOUNDS, cv):
    sub = {"Lp": "L_p", "bp": "b_p", "hp": "h_p", "bc": "b_c", "hc": "h_c", "T": "T"}[nome]
    ax.plot(front.W_casco, (front[nome] - lo) / (hi - lo), "o-", ms=3.5, lw=1.6, c=c, label=f"${sub}$")
ax.set_ylim(-0.05, 1.05); ax.set_xlabel("peso estrutural do casco [t]")
ax.set_ylabel("posição no domínio (0 = mín., 1 = máx.)")
ax.xaxis.set_major_formatter(fmt_m); ax.yaxis.set_major_formatter(fmt_d)
ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.15), fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "12_variaveis_fronteira.png"), dpi=200)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw=dict(width_ratios=[1.3, 1]))
itens_f = [("calado_m", "calado T"), ("col_H_m", "altura da coluna $h_c$"), ("col_B_m", "lado da coluna $b_c$"),
           ("pont_B_m", "largura do pontoon $b_p$"), ("pont_H_m", "altura do pontoon $h_p$")]
for y, (k, rr) in enumerate(itens_f):
    s = pst[k].dropna()
    a1.plot([s.min(), s.max()], [y, y], c="#C9D3DC", lw=8, solid_capstyle="round", zorder=1)
    a1.scatter(s, [y] * len(s), s=36, c=BLUE, ec="white", zorder=2, label="semis do pôster" if y == 0 else None)
    a1.scatter([x3[k]], [y], s=150, marker="D", c=ORANGE, ec="white", zorder=3,
               label="G02 · escolhida (10% lastro)" if y == 0 else None)
    a1.text(x3[k], y + 0.3, br(x3[k], 1), ha="center", color=ORANGE, fontsize=10, fontweight="bold")
a1.set_yticks(range(len(itens_f))); a1.set_yticklabels([r for _, r in itens_f]); a1.invert_yaxis()
a1.set_xlabel("dimensão [m]"); a1.grid(axis="y", visible=False); a1.legend(fontsize=9, loc="lower right")
a1.set_title("(a) Dimensões do casco", loc="left", fontsize=12)
s = pst.dropna(subset=["desloc_por_kbopd"])
nomes = list(s.nome) + ["G02 · caso-base", "G02 · 10% lastro"]
vals = list(s.desloc_por_kbopd) + [b3["Δ [t]"] / Q, x3["desloc_por_kbopd"]]
ordem = np.argsort(vals)
a2.barh([nomes[i] for i in ordem], [vals[i] for i in ordem],
        color=[ORANGE if nomes[i] == "G02 · 10% lastro" else (GRAY if nomes[i].startswith("G02") else BLUE)
               for i in ordem])
for yy, i in enumerate(ordem):
    a2.text(vals[i] + 8, yy, br(vals[i]), va="center", fontsize=10, color=NAVY)
a2.set_xlim(0, 1000); a2.set_xlabel("deslocamento por mil bopd [t]"); a2.grid(axis="y", visible=False)
a2.set_title("(b) Deslocamento específico", loc="left", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "13_poster2011.png"), dpi=200)
print("\nTabelas em", TEX, "| figuras em", OUT)
