# -*- coding: utf-8 -*-
"""
PNV3425 - Grupo 02 - Comparativo com plataformas reais.

Dados públicos (ver coluna "fonte" do CSV gerado):
  * CLOV FPSO (TotalEnergies, Bloco 17, Angola): análogo regional do campo.
  * Scarabeo 5 FPU (Eni, Congo LNG, Rep. do Congo): única semissubmersível de
    produção na região do Baixo Congo.
  * Semissubmersíveis de produção do Golfo do México com capacidade e lâmina
    d'água semelhantes: Argos, King's Quay, Vito, Anchor e Shenandoah.

Roda depois de pnv3425_grupo02.py. Gera:
  resultados/complementar/plataformas_reais.csv
  resultados/complementar/09_comparativo_reais.png
  resultados/figuras_apresentacao/f_comparativo_reais.png
Uso (na pasta caso_base/): python codigo/comparativo_plataformas_reais.py
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
OUT = os.path.join(RES, "complementar")
FIGP = os.path.join(RAIZ, "resultados", "figuras_apresentacao")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIGP, exist_ok=True)

OM = "https://www.offshore-mag.com/regional-reports/us-gulf-of-mexico/article/14213384/"
OM2 = "https://www.offshore-mag.com/field-development/article/14072694/"
REAIS = pd.DataFrame([
    dict(nome="CLOV FPSO", tipo="FPSO", local="Bloco 17, Angola (Baixo Congo)", lamina_m=1291,
         capacidade_kbpd=160, deslocamento_t=np.nan, peso_t=110000, area_conves_m2=305 * 61,
         dimensoes="305 × 61 m, calado 24,4 m, armazenamento 1,8 milhão bbl",
         fonte="https://www.offshore-technology.com/projects/clov-development-project-angola/"),
    dict(nome="Scarabeo 5 FPU", tipo="Semi (2 pontoons, 6 colunas)", local="Congo LNG, Rep. do Congo",
         lamina_m=35, capacidade_kbpd=np.nan, deslocamento_t=np.nan, peso_t=np.nan,
         area_conves_m2=np.nan, dimensoes="111 × 73 m (AIS); sonda de 1990 convertida, gás",
         fonte="https://www.saipem.com/en/media/press-releases/2025-08-26/"
               "saipem-completes-conversion-scarabeo-5-drilling-unit-floating"),
    dict(nome="Argos", tipo="Semi (4 colunas)", local="Mad Dog 2, Golfo do México", lamina_m=1372,
         capacidade_kbpd=140, deslocamento_t=101000, peso_t=60000 * 0.907,
         area_conves_m2=109.7 * 48.8, dimensoes="convés ≈ campo de futebol americano; 27 andares",
         fonte=OM),
    dict(nome="King's Quay", tipo="Semi (4 colunas)", local="Golfo do México", lamina_m=np.nan,
         capacidade_kbpd=80, deslocamento_t=38000, peso_t=21498, area_conves_m2=np.nan,
         dimensoes="topside de 10.000 t; projetada para tempestade de 1.000 anos", fonte=OM + " ; " + OM2),
    dict(nome="Vito", tipo="Semi (4 colunas)", local="Golfo do México", lamina_m=1220,
         capacidade_kbpd=100, deslocamento_t=38000, peso_t=np.nan, area_conves_m2=np.nan,
         dimensoes="topside de 9.200 t", fonte=OM + " ; " + OM2),
    dict(nome="Anchor", tipo="Semi (4 colunas)", local="Golfo do México", lamina_m=1500,
         capacidade_kbpd=75, deslocamento_t=69000, peso_t=np.nan, area_conves_m2=np.nan,
         dimensoes="alta pressão (20.000 psi)", fonte=OM),
    dict(nome="Shenandoah", tipo="Semi (4 colunas)", local="Golfo do México", lamina_m=np.nan,
         capacidade_kbpd=100, deslocamento_t=np.nan, peso_t=np.nan, area_conves_m2=91 * 91,
         dimensoes="91 × 91 × 90 m", fonte=OM),
])

ficha = pd.read_csv(os.path.join(RES, "ficha_tecnica_3_cenarios.csv"), index_col=0)
Q = 158.894
lin = []
for c, nome in zip(ficha.columns, ("G02 · mín. peso", "G02 · mín. heave", "G02 · escolhida")):
    f = ficha[c]
    lin.append(dict(nome=nome, tipo="Semi (2 pontoons, 4 colunas)", local="KZ-2026-B (projeto)",
                    lamina_m=1450, capacidade_kbpd=Q, deslocamento_t=f["Δ [t]"],
                    peso_t=f["Peso casco [t]"] + f["Peso topside [t]"],
                    area_conves_m2=f["Área de convés [m²]"],
                    dimensoes=f"Lp = {f['Lp [m]']:.1f} m, T = {f['T [m]']:.1f} m, "
                              f"altura = {f['hp [m]'] + f['hc [m]'] + 20:.1f} m", fonte="este trabalho"))
sens = os.path.join(RAIZ, "..", "condicao_10pct_lastro", "resultados_lastro10", "ficha_tecnica_3_cenarios.csv")
if os.path.exists(sens):
    f = pd.read_csv(sens, index_col=0).iloc[:, 2]
    lin.append(dict(nome="G02 · escolhida, lastro ≥ 10%", tipo="Semi (2 pontoons, 4 colunas)",
                    local="KZ-2026-B (sensibilidade)", lamina_m=1450, capacidade_kbpd=Q,
                    deslocamento_t=f["Δ [t]"], peso_t=f["Peso casco [t]"] + f["Peso topside [t]"],
                    area_conves_m2=f["Área de convés [m²]"], dimensoes="", fonte="este trabalho"))
df = pd.concat([REAIS, pd.DataFrame(lin)], ignore_index=True)
df["desloc_por_kbpd"] = df.deslocamento_t / df.capacidade_kbpd
df["peso_sobre_desloc"] = df.peso_t / df.deslocamento_t
df["area_correlacao_m2"] = 42.246 * df.capacidade_kbpd + 4850.1
df.to_csv(os.path.join(OUT, "plataformas_reais.csv"), index=False)
print(df[["nome", "capacidade_kbpd", "deslocamento_t", "peso_t", "desloc_por_kbpd",
          "peso_sobre_desloc", "area_conves_m2", "area_correlacao_m2"]].round(2).to_string(index=False))

# ---------------------------------------------------------------------------
NAVY, ORANGE, BLUE, TEAL, GRAY = "#0B2E40", "#E36C1E", "#2E75B6", "#1A9E8A", "#8A99A6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#E3E8ED",
                     "axes.labelcolor": NAVY, "axes.titlecolor": NAVY, "axes.edgecolor": "#4A5A66"})
br = lambda v, k=0: f"{v:,.{k}f}".replace(",", "X").replace(".", ",").replace("X", ".")

fig, axs = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw=dict(width_ratios=[1.15, 1, 1]))

# (a) deslocamento por mil bpd
a = df.dropna(subset=["desloc_por_kbpd"]).copy()
a = a[a.nome != "G02 · mín. peso"].sort_values("desloc_por_kbpd")
cores = [ORANGE if n.startswith("G02") else BLUE for n in a.nome]
axs[0].barh(a.nome, a.desloc_por_kbpd, color=cores)
for y, v in enumerate(a.desloc_por_kbpd):
    axs[0].text(v + 12, y, br(v), va="center", fontsize=10, color=NAVY)
axs[0].set_xlabel("deslocamento por mil bpd de capacidade [t]")
axs[0].set_title("(a) Deslocamento específico", loc="left", fontsize=12)
axs[0].grid(axis="y", visible=False); axs[0].set_xlim(0, 1050)

# (b) área de convés x capacidade
q = np.linspace(60, 180, 50)
axs[1].plot(q, 42.246 * q + 4850.1, c=NAVY, lw=2, label="correlação da aula (1 nível)")
for _, r in df.dropna(subset=["area_conves_m2"]).iterrows():
    if r.tipo == "FPSO":
        continue
    g02 = r.nome.startswith("G02")
    axs[1].plot(r.capacidade_kbpd, r.area_conves_m2, "o" if g02 else "s", ms=9,
                c=ORANGE if g02 else BLUE, mec="white")
    if r.nome in ("G02 · escolhida", "G02 · mín. peso", "Argos", "Shenandoah"):
        dy = {"Argos": -900, "Shenandoah": 700, "G02 · escolhida": -1500, "G02 · mín. peso": 600}[r.nome]
        rot = r.nome + (" (planta do convés)" if r.nome == "Argos" else "")
        axs[1].annotate(rot, (r.capacidade_kbpd, r.area_conves_m2), xytext=(-8, 0),
                        textcoords="offset points", ha="right", fontsize=9.5, color=NAVY,
                        va="center") if r.nome != "G02 · escolhida" else axs[1].annotate(
            rot, (r.capacidade_kbpd, r.area_conves_m2), xytext=(-8, -14), textcoords="offset points",
            ha="right", fontsize=9.5, color=NAVY)
axs[1].set_xlabel("capacidade [mil bpd]"); axs[1].set_ylabel("área de convés [m²]")
axs[1].set_title("(b) Área de convés", loc="left", fontsize=12)
axs[1].yaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v)))
axs[1].legend(fontsize=9, loc="upper left"); axs[1].set_ylim(3000, 21000)

# (c) composição do deslocamento
c = df.dropna(subset=["peso_sobre_desloc"]).copy()
c = c[c.nome.isin(["King's Quay", "Argos", "G02 · escolhida", "G02 · escolhida, lastro ≥ 10%"])]
x = np.arange(len(c))
axs[2].bar(x, c.peso_sobre_desloc, color=[ORANGE if n.startswith("G02") else BLUE for n in c.nome],
           label="casco + topside")
axs[2].bar(x, 1 - c.peso_sobre_desloc, bottom=c.peso_sobre_desloc, color="#D9DFE4",
           label="lastro, risers, amarração e cargas")
for i, v in enumerate(c.peso_sobre_desloc):
    axs[2].text(i, v / 2, f"{br(100 * v)}%", ha="center", color="white", fontweight="bold")
axs[2].set_xticks(x)
axs[2].set_xticklabels([n.replace("G02 · escolhida, lastro ≥ 10%", "G02 lastro\n≥ 10%")
                        .replace("G02 · escolhida", "G02\nescolhida") for n in c.nome], fontsize=10)
axs[2].set_ylim(0, 1.0); axs[2].set_ylabel("fração do deslocamento")
axs[2].yaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 1)))
axs[2].set_title("(c) Composição do deslocamento", loc="left", fontsize=12)
axs[2].legend(fontsize=9, loc="lower right"); axs[2].grid(axis="x", visible=False)
fig.tight_layout()
for p in (os.path.join(OUT, "09_comparativo_reais.png"), os.path.join(FIGP, "f_comparativo_reais.png")):
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
print("Figuras salvas.")
