# -*- coding: utf-8 -*-
"""
===============================================================================
PNV3425 - Projeto de Sistemas Oceânicos - Trabalho Final (2º semestre 2026)
GRUPO 02 - Bloco KZ-2026-B - Bacia do Baixo Congo (Angola)
Projeto paramétrico de uma semissubmersível (2 pontoons + 4 colunas, planta
quadrada de lado Lp) e otimização multiobjetivo Peso do casco x Hs de heave.
===============================================================================

VARIÁVEIS DE PROJETO:  x = [Lp, bp, hp, bc, hc, T]

FLUXO DE CÁLCULO (cada etapa usa as saídas da anterior)
  1) Hidrostática (Ex.7) ...... ∇, Δ, KB, BM_T, BM_L, KM_T, KM_L, A_wp
  2) Pesos e centros (Ex.8) ... W_casco, W_planta, W_topside, W_risers, W_amarr.,
                                W_lastro = Δ - ΣW, KG, GM_T, GM_L
  3) Convés e air gap (Ex.8) .. A_conv = Lp², a = hp + hc - T
  4) Curva GZ 0-50° (Ex.9) .... projeções 2D, equilíbrio a volume constante
  5) Vento (Ex.9) ............. por plano: 4 colunas (sem sombra), z_CLR do
                                plano, HM0, HMud, HA(φ), φal, φ1, φ2, A, B, A/B
  6) Heave (Ex.10) ............ F3(ω)·cos(ω²dp/2g), A33 (ld = Lp-2bc), C33,
                                B33, ωn, Tn, RAO
  7) Resposta (Ex.10) ......... Sζ(ω) JONSWAP γ=3,3, Sz = RAO²·Sζ, m0z, H1/3,z
  8) Air gap mínimo ........... ηmax = 1,86Hs/2, zmin = -1,86H1/3z/2,
                                a_min = ηmax - zmin
  9) Restrições + objetivos -> variação sistemática + soma ponderada +
                                ε-restrito + filtro de não dominados (Pareto)

REVISÃO (marcadores [REV n] no código = item n da revisão do grupo)
  [REV 1] Vento pelo modelo do Ex. 9: 4·bc·a nas colunas e braço até z_CLR
          do plano; tabela de vento montada dentro do loop de planos.
  [REV 2] Heave pelo modelo do Ex. 10: fator cos(ω²dp/2g), dp = Lp - bp, e
          massa adicional com ld = Lp - 2bc; γ = 3,3 (também reporta γ = 1).
  [REV 3] Otimização: sem retorno silencioso ao ponto de partida, res.success
          impresso, continuação entre pesos e extremos da fronteira sem
          restrição ε ativa.
  [REV 4] Hipóteses parametrizadas: lastro mínimo, inclusão do gás no BOE,
          hd/hm por cenário.
  [REV 5] Validação comparada com os valores das aulas.
  [REV 6] Rótulos com quebra de linha; γ lido em tempo de execução.
"""

import os
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize, brentq
from scipy.integrate import trapezoid
from scipy.stats import qmc

# ============================================================================
# 0. CONFIGURAÇÃO GERAL
# ============================================================================
# (variáveis de ambiente opcionais permitem rodadas rápidas de teste)
OUT_DIR = os.environ.get("OUT_DIR", "resultados")           # figuras e tabelas
MOSTRAR_GRAFICOS = os.environ.get("MOSTRAR_GRAFICOS", "1") == "1"  # plt.show()
SEMENTE = 2026                          # reprodutibilidade da amostragem
N_AMOSTRAS = int(os.environ.get("N_AMOSTRAS", 20000))       # variação sistemática (LHS)
PASSO_W = float(os.environ.get("PASSO_W", 0.05))            # passo de w1 na soma ponderada
N_PARTIDAS = 5                          # pontos iniciais do LHS por valor de w1
MAXITER = 200                           # iterações máximas do SLSQP
DPHI_OTIM = 1.0                         # passo angular da GZ na otimização [°]
DPHI_FINAL = 0.25                       # passo angular da GZ no relatório [°]

pd.options.display.float_format = "{:,.3f}".format
pd.options.display.width = 200
pd.options.display.max_columns = 30
pd.options.display.max_rows = 200

# ============================================================================
# 1. DADOS FIXOS, CENÁRIOS E LIMITES
# ============================================================================
RHO = 1.025            # água do mar [t/m³]
G = 9.81               # [m/s²]
RHO_AR = 1.222         # ar [kg/m³]
GAMMA_E = 0.270        # peso específico estrutural [t/m³]
XI_HEAVE = 0.05        # fator de amortecimento em heave
# [REV 2] γ = 3,3 como na disciplina. O H1/3 de heave com γ = 1 (Pierson-
# Moskowitz) também é calculado e reportado para comparação.
GAMMA_JONSWAP = 3.3

# [REV 4] hd e hm agora pertencem ao cenário (ver Cenario). Valores do G02:
HD = float(os.environ.get("HD", 8.0))   # altura do deck box [m] (estimada por semelhantes)
HM = float(os.environ.get("HM", 12.0))  # altura média dos módulos [m] (estimada por semelhantes)
FRAC_LARG_MODULOS = 1.0  # fração de Lp ocupada pelos módulos na vista lateral

PESO_PLANTA_T_BOE = 0.083   # 83 kg/BOE
F_CONVES, F_OPER = 0.35, 0.35
F_RISERS, F_AMARR = 0.04, 0.03

VENTOS = {"Tempestade 51,5 m/s": 51.5, "Operação 36 m/s": 36.0}
PLANOS = ("Transversal", "Longitudinal")

# Coeficientes de forma Cs (MODU Code 2009, 3.2.4)
CS_COLUNAS = 1.0       # colunas quadradas -> superfície tipo casco
CS_DECKBOX = 1.0       # deck box -> casco/superfície
CS_MODULOS = 1.1       # agrupamento de deckhouses/módulos
CS_UNDERDECK = 1.0     # face inferior do convés (lisa)

# Coeficiente de altura Ch (MODU Code 2009, tabela 3.2.4) - altura acima da LA
CH_TAB = [(15.3, 1.00), (30.5, 1.10), (46.0, 1.20), (61.0, 1.30), (76.0, 1.37),
          (91.5, 1.43), (106.5, 1.48), (122.0, 1.52), (137.0, 1.56),
          (152.5, 1.60), (167.5, 1.63), (183.0, 1.67), (198.0, 1.70),
          (213.5, 1.72), (228.5, 1.75), (244.0, 1.77), (256.0, 1.79)]

# Limites das restrições
GM_MIN, GM_MAX = 1.0, 4.0
TN_MIN = 20.0
FRAC_LASTRO = 0.9
AB_MIN = 1.3
IMERSAO_MIN_COL = 1.0  # T - hp >= 1 m: linha d'água nas colunas (consistência)
# [REV 4] Lastro mínimo como fração do volume dos pontoons. 0 = só "lastro
# positivo" (enunciado). Ex.: 0.10 reserva lastro para ajuste de calado/trim.
LASTRO_MIN_FRAC = float(os.environ.get("LASTRO_MIN_FRAC", 0.0))
MARGEM_OTIM = 1e-4     # [REV 3] margem em todas as restrições no SLSQP
MARGEM_AB_OTIM = 0.005 # margem extra no A/B durante a otimização (passo 1°)
N_EPSILON = int(os.environ.get("N_EPSILON", 12))  # níveis do ε-restrito

# [REV 4] Produção: só óleo (padrão) ou óleo + gás convertido em boe.
# Hipótese: o gás segue o mesmo perfil da curva de produção do óleo.
BOE_PICO_OLEO = 158894.48               # pico da curva de produção [bpd]
OLEO_RECUP_BBL = 2.2e9 * 0.30           # 660 milhões de bbl recuperáveis
GAS_RECUP_M3 = 30e9                     # 30 bilhões de m³ recuperáveis
M3_GAS_POR_BOE = 5800 * 0.0283168       # 5,8 mil pés³/boe = 164,2 m³/boe
FATOR_GAS = 1 + GAS_RECUP_M3 / M3_GAS_POR_BOE / OLEO_RECUP_BBL
INCLUIR_GAS = os.environ.get("INCLUIR_GAS", "0") == "1"   # caso-base: só óleo


@dataclass(frozen=True)
class Cenario:
    nome: str
    BOE: float      # produção de pico [boe/dia]
    Hs: float       # mar de projeto (100 anos) [m]
    Tp: float       # [s]
    hd: float = HD  # altura do deck box [m]
    hm: float = HM  # altura média dos módulos [m]

    @property
    def Q(self):            # mil BOE/dia
        return self.BOE / 1000.0

    @property
    def area_req(self):     # área mínima de convés [m²]
        return 42.246 * self.Q + 4850.1

    @property
    def eta_max(self):      # crista máxima (Rayleigh, 3 h) [m]
        return 1.86 * self.Hs / 2.0


# Grupo 02: pico da curva de produção; mar de 100 anos
CEN_G02 = Cenario("Grupo 02 - KZ-2026-B (Baixo Congo)",
                  BOE_PICO_OLEO * (FATOR_GAS if INCLUIR_GAS else 1.0), 5.6, 15.2)
# Cenário dos Exercícios 7 a 10 (usado na validação).
# [REV 4/5] hm = 15 m como no Ex. 9; hd mantido em 8 m -> KG 33,21 m e
# A/B 2,31/2,27 (aula: 33,00 e 2,33/2,36). Com hd = 7 m: KG 32,99 m e
# A/B 2,42/2,39. Confirmar o hd usado no Ex. 8/9.
CEN_EX = Cenario("Exercícios 7-10 (referência)", 120000.0, 12.2, 14.6, hd=8.0, hm=15.0)

# Limites das variáveis: Lp, bp, hp, bc, hc, T
BOUNDS = [(np.sqrt(CEN_G02.area_req), 150.0),  # Lp
          (8.0, 25.0),                          # bp
          (6.0, 20.0),                          # hp
          (8.0, 25.0),                          # bc
          (20.0, 50.0),                         # hc
          (12.0, 40.0)]                         # T
NOMES_X = ["Lp", "bp", "hp", "bc", "hc", "T"]


def coef_altura(h):
    for lim, ch in CH_TAB:
        if h <= lim:
            return ch
    return 1.80

# ============================================================================
# 2. HIDROSTÁTICA (Exercício 7)
# ============================================================================
def hidrostatica(x):
    Lp, bp, hp, bc, hc, T = map(float, x)
    t_p = min(T, hp)                 # calado nos pontoons
    t_c = max(T - hp, 0.0)           # calado nas colunas
    V_pont = 2 * Lp * bp * t_p
    V_col = 4 * bc**2 * t_c
    V = V_pont + V_col
    KB = (V_pont * t_p / 2 + V_col * (hp + t_c / 2)) / V

    yc = (Lp - bp) / 2               # coluna -> eixo longitudinal (plano T)
    xc = (Lp - bc) / 2               # coluna -> eixo transversal (plano L)
    if t_c > 0:
        A_wp = 4 * bc**2
        I_T = 4 * (bc**4 / 12 + bc**2 * yc**2)
        I_L = 4 * (bc**4 / 12 + bc**2 * xc**2)
    else:                            # linha d'água nos pontoons (robustez)
        A_wp = 2 * Lp * bp
        I_T = 2 * (Lp * bp**3 / 12 + Lp * bp * yc**2)
        I_L = 2 * (bp * Lp**3 / 12)
    BM_T, BM_L = I_T / V, I_L / V
    return dict(V=V, Delta=RHO * V, V_pont_sub=V_pont, V_col_sub=V_col,
                KB=KB, I_T=I_T, I_L=I_L, BM_T=BM_T, BM_L=BM_L,
                KM_T=KB + BM_T, KM_L=KB + BM_L, A_wp=A_wp)

# ============================================================================
# 3. PESOS, CENTROS E GM (Exercício 8)
# ============================================================================
def pesos(x, hid, cen):
    Lp, bp, hp, bc, hc, T = map(float, x)
    D = hid["Delta"]
    z_top = hp + hc                                  # fundo do convés
    hd, hm = cen.hd, cen.hm

    W_planta = PESO_PLANTA_T_BOE * cen.BOE
    W_conv = F_CONVES * W_planta
    W_oper = F_OPER * W_planta
    V_pont = 2 * Lp * bp * hp
    V_colunas = 4 * bc**2 * hc
    W_pont = GAMMA_E * V_pont
    W_col = GAMMA_E * V_colunas
    W_ris = F_RISERS * D
    W_amr = F_AMARR * D

    itens = [("Planta de produção", W_planta, z_top + hd + hm / 2),
             ("Estrutura do convés", W_conv, z_top + hd / 2),
             ("Carga operacional", W_oper, z_top + hd / 2),
             ("Pontoons", W_pont, hp / 2),
             ("Colunas", W_col, hp + hc / 2),
             ("Risers", W_ris, z_top),
             ("Amarração", W_amr, z_top)]
    W_sem_lastro = sum(w for _, w, _ in itens)
    W_lastro = D - W_sem_lastro
    V_lastro = W_lastro / RHO
    nivel = float(np.clip(V_lastro / (2 * Lp * bp), 0.0, hp))
    itens.append(("Lastro (nos pontoons)", W_lastro, nivel / 2))

    W_tot = sum(w for _, w, _ in itens)              # = Δ
    M_tot = sum(w * z for _, w, z in itens)
    KG = M_tot / W_tot
    W_top = W_planta + W_conv + W_oper
    VCG_top = (W_planta * (z_top + hd + hm / 2) + (W_conv + W_oper) * (z_top + hd / 2)) / W_top
    return dict(W_planta=W_planta, W_conves=W_conv, W_oper=W_oper, W_topside=W_top,
                VCG_topside=VCG_top, W_pontoons=W_pont, W_colunas=W_col,
                W_casco=W_pont + W_col, W_risers=W_ris, W_amarracao=W_amr,
                W_lastro=W_lastro, V_lastro=V_lastro, V_pont=V_pont,
                nivel_lastro=nivel, KG=KG, W_total=W_tot, M_total=M_tot, itens=itens,
                GM_T=hid["KM_T"] - KG, GM_L=hid["KM_L"] - KG)


def tabela_pesos(pes):
    """Tabela de pesos e centros (montada só para o relatório: o pandas é
    lento demais para entrar em cada avaliação da otimização)."""
    tabela = pd.DataFrame([dict(Item=n, Peso_t=w, VCG_m=z, Momento_tm=w * z)
                           for n, w, z in pes["itens"]])
    tabela.loc[len(tabela)] = dict(Item="TOTAL (= Δ)", Peso_t=pes["W_total"], VCG_m=pes["KG"],
                                   Momento_tm=pes["M_total"])
    return tabela

# ============================================================================
# 4. CURVA GZ PELO MÉTODO DE PROJEÇÕES 2D (Exercício 9)
# ============================================================================
def caixas_2d(x, plano):
    """Retângulos da projeção 2D: (u0, u1, z0, z1, espessura fora do plano)."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    if plano == "Transversal":       # inclinação em torno do eixo longitudinal
        yc = (Lp - bp) / 2
        cx = [(-Lp / 2, -Lp / 2 + bp, 0.0, hp, Lp),
              (Lp / 2 - bp, Lp / 2, 0.0, hp, Lp),
              (-yc - bc / 2, -yc + bc / 2, hp, hp + hc, 2 * bc),
              (yc - bc / 2, yc + bc / 2, hp, hp + hc, 2 * bc)]
    else:                            # inclinação em torno do eixo transversal
        cx = [(-Lp / 2, Lp / 2, 0.0, hp, 2 * bp),
              (-Lp / 2, -Lp / 2 + bc, hp, hp + hc, 2 * bc),
              (Lp / 2 - bc, Lp / 2, hp, hp + hc, 2 * bc)]
    return np.array(cx, float).T


def _integrais_submersas(cx, alpha, beta):
    """Área e momentos exatos dos retângulos abaixo da linha z = alpha + beta·u
    (coordenadas do corpo). Vetorizado em ângulos (linhas) x caixas (colunas)."""
    u0, u1, z0, z1, t = cx
    a = alpha[:, None]
    b = beta[:, None]
    H = z1 - z0
    p = np.clip((z0 - a) / b, u0, u1)
    q = np.clip((z1 - a) / b, u0, u1)
    zp, zq = a + b * p, a + b * q
    L = q - p
    area = ((zp + zq) / 2 - z0) * L + (u1 - q) * H
    mu = (a - z0) * (q**2 - p**2) / 2 + b * (q**3 - p**3) / 3 + H * (u1**2 - q**2) / 2
    mz = L * ((zp**2 + zp * zq + zq**2) / 3 - z0**2) / 2 + (u1 - q) * (z1**2 - z0**2) / 2
    return (t * area).sum(1), (t * mu).sum(1), (t * mz).sum(1)


def _volume_e_derivada(cx, alpha, beta):
    """Volume submerso e dV/dα. A derivada é exata: Σ t·(comprimento da linha
    d'água dentro de cada retângulo)."""
    u0, u1, z0, z1, t = cx
    a = alpha[:, None]
    b = beta[:, None]
    p = np.clip((z0 - a) / b, u0, u1)
    q = np.clip((z1 - a) / b, u0, u1)
    L = q - p
    area = (a + b * (p + q) / 2 - z0) * L + (u1 - q) * (z1 - z0)
    return (t * area).sum(1), (t * L).sum(1)


def equilibrio_2d(cx, V0, phis_rad, alpha0=None, tol=1e-10, n_max=100):
    """Para cada ângulo, acha a linha d'água que mantém ∇ = V0.
    Newton com salvaguarda: mantém o intervalo [lo, hi] da bissecção e usa
    bissecção sempre que o passo de Newton sai dele. alpha0 (ex.: o calado T)
    é o chute inicial; sem ele, parte do meio do intervalo."""
    beta = np.maximum(np.tan(phis_rad), 1e-12)
    u0, u1, z0, z1, _ = cx
    lo = z0.min() - beta * u1.max() - 1.0
    hi = z1.max() - beta * u0.min() + 1.0
    alpha = 0.5 * (lo + hi) if alpha0 is None else np.clip(np.broadcast_to(alpha0, lo.shape), lo, hi)
    tol_V = tol * V0                                   # tolerância em volume [m³]
    for _ in range(n_max):
        V, dV = _volume_e_derivada(cx, alpha, beta)
        ok = np.abs(V - V0) <= tol_V                   # convergência por ângulo
        if ok.all():
            break
        acima = V > V0
        hi = np.where(acima, alpha, hi)
        lo = np.where(acima, lo, alpha)
        with np.errstate(divide="ignore", invalid="ignore"):
            novo = alpha - (V - V0) / dV
        # Newton só se cair estritamente dentro de (lo, hi); senão bissecção.
        # Isso impede o ciclo entre as duas pontas do intervalo, que acontece
        # quando V(α) tem quinas (linha d'água passando por cantos).
        fora = ~np.isfinite(novo) | (novo <= lo) | (novo >= hi)
        novo = np.where(fora, 0.5 * (lo + hi), novo)
        alpha = np.where(ok, alpha, novo)              # convergidos ficam parados
    else:                                              # garantia: bissecção pura
        for _ in range(60):
            V, _ = _volume_e_derivada(cx, alpha, beta)
            ok = np.abs(V - V0) <= tol_V
            if ok.all():
                break
            acima = V > V0
            hi = np.where(acima, alpha, hi)
            lo = np.where(acima, lo, alpha)
            alpha = np.where(ok, alpha, 0.5 * (lo + hi))
    V, Mu, Mz = _integrais_submersas(cx, alpha, beta)
    return alpha, Mu / V, Mz / V


def curva_gz(x, KG, V0, plano, phis_deg):
    cx = caixas_2d(x, plano)
    ph = np.radians(phis_deg)
    alpha, uB, zB = equilibrio_2d(cx, V0, ph, alpha0=float(x[5]))
    GZ = uB * np.cos(ph) + (zB - KG) * np.sin(ph)
    return GZ, alpha


def angulo_alagamento(x, V0, plano, phis_deg, alpha):
    """φal: fundo do convés (u = Lp/2, z = hp+hc) toca a água na borda."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    zd = hp + hc
    cx = caixas_2d(x, plano)

    def folga(phd):
        a, _, _ = equilibrio_2d(cx, V0, np.radians([phd]), alpha0=T)
        return zd - (a[0] + np.tan(np.radians(phd)) * Lp / 2)

    f = zd - (alpha + np.tan(np.radians(phis_deg)) * Lp / 2)
    idx = np.where(f <= 0)[0]
    if len(idx) == 0:
        ph_prev = phis_deg[-1]
        for phd in np.arange(phis_deg[-1] + 2.0, 86.0, 2.0):
            if folga(phd) <= 0:
                return brentq(folga, ph_prev, phd, xtol=1e-7)
            ph_prev = phd
        return 85.0
    i = idx[0]
    if i == 0:
        return 0.0
    return brentq(folga, phis_deg[i - 1], phis_deg[i], xtol=1e-7)

# ============================================================================
# 5. VENTO E CRITÉRIO DE ÁREAS (Exercício 9)
# ============================================================================
def z_clr(x, plano):
    """[REV 1] Centro de resistência lateral: centroide da silhueta submersa
    vista na direção do vento (medido a partir da quilha).
      Transversal : Lp·hp (pontoons sobrepostos) + 2·bc·(T−hp)
      Longitudinal: 2·bp·hp (topos dos pontoons) + 2·bc·(T−hp)"""
    Lp, bp, hp, bc, hc, T = map(float, x)
    t_p, t_c = min(T, hp), max(T - hp, 0.0)
    A_pont = Lp * t_p if plano == "Transversal" else 2 * bp * t_p
    A_col = 2 * bc * t_c
    return (A_pont * t_p / 2 + A_col * (hp + t_c / 2)) / (A_pont + A_col)


def tabela_vento(x, V, plano, cen):
    """Forças, braços e momentos por parcela no plano dado.
    [REV 1] Colunas: 4·bc·a (Ex. 9: sem efeito de sombra). Braço medido do
    centroide da parcela até o z_CLR do plano. Deck box e módulos têm a mesma
    projeção nos dois planos (planta quadrada)."""
    Lp, bp, hp, bc, hc, T = map(float, x)
    hd, hm = cen.hd, cen.hm
    a = max(hp + hc - T, 0.0)
    q = 0.5 * RHO_AR * V**2 / 1000.0          # pressão dinâmica [kPa]
    zclr = z_clr(x, plano)
    prof_clr = T - zclr                         # z_CLR abaixo da LA [m]
    parcelas = [("Colunas (4, sem sombra)", 4 * bc * a, a / 2, CS_COLUNAS),
                ("Deck box", Lp * hd, a + hd / 2, CS_DECKBOX),
                ("Módulos de topside", FRAC_LARG_MODULOS * Lp * hm, a + hd + hm / 2, CS_MODULOS),
                ("Face inferior do convés (HMud)", Lp * Lp, a, CS_UNDERDECK)]
    linhas = []
    for nome, A, zc, cs in parcelas:
        ch = coef_altura(zc)
        F = q * cs * ch * A
        braco = zc + prof_clr
        linhas.append(dict(Parcela=nome, Area_m2=A, z_LA_m=zc, Cs=cs, Ch=ch,
                           Forca_kN=F, Braco_m=braco, Momento_kNm=F * braco))
    HM0 = sum(l["Momento_kNm"] for l in linhas[:3])
    HMud = linhas[3]["Momento_kNm"]
    return linhas, HM0, HMud, zclr          # linhas -> pd.DataFrame no relatório


def criterio_areas(phd, GZ, HA, phal):
    d = GZ - HA
    phi1 = phi2 = None
    for i in range(1, len(phd)):
        if phi1 is None and d[i - 1] < 0 <= d[i]:
            phi1 = phd[i - 1] + (phd[i] - phd[i - 1]) * d[i - 1] / (d[i - 1] - d[i])
        elif phi1 is not None and d[i - 1] > 0 >= d[i]:
            phi2 = phd[i - 1] + (phd[i] - phd[i - 1]) * d[i - 1] / (d[i - 1] - d[i])
            break
    if phal <= 0:
        return dict(phi1=phi1, phi2=phi2, A=0.0, B=0.0, AB=0.0, GZ_min=0.0,
                    GZsen_min=-1.0, lim_gz=0.0)
    m = phd < phal
    xs = np.radians(np.append(phd[m], phal))
    A = trapezoid(np.append(GZ[m], np.interp(phal, phd, GZ)), xs)
    B = trapezoid(np.append(HA[m], np.interp(phal, phd, HA)), xs)
    lim = phi2 if (phi2 is not None and phi2 < phal) else phal
    sel = (phd > 0) & (phd <= lim)
    if not sel.any():
        sel = (phd > 0) & (phd <= phd[1])
    gz_sel = GZ[sel]
    gzsen = gz_sel / np.sin(np.radians(phd[sel]))
    return dict(phi1=phi1, phi2=phi2, A=A, B=B, AB=A / B if B > 0 else np.inf,
                GZ_min=gz_sel.min(), GZsen_min=gzsen.min(), lim_gz=lim)


def estabilidade(x, hid, pes, cen, dphi=1.0, phimax=50.0):
    V0, KG, Dg = hid["V"], pes["KG"], hid["Delta"] * G
    out = dict(vento={})
    AB_min, gzsen_min = np.inf, np.inf
    for plano in PLANOS:
        # [REV 1] tabela de vento depende do plano (z_CLR)
        ventos = {nome: tabela_vento(x, V, plano, cen) for nome, V in VENTOS.items()}
        out["vento"][plano] = ventos
        phd = np.arange(0.0, phimax + 1e-9, dphi)
        GZ, alpha = curva_gz(x, KG, V0, plano, phd)
        phal = angulo_alagamento(x, V0, plano, phd, alpha)
        if phal > phd[-1]:                       # estende a curva até φal
            extra = np.arange(phd[-1] + dphi, phal + dphi + 1e-9, dphi)
            GZe, _ = curva_gz(x, KG, V0, plano, extra)
            phd, GZ = np.append(phd, extra), np.append(GZ, GZe)
        casos = {}
        for nome, (df, HM0, HMud, zclr) in ventos.items():
            ph = np.radians(phd)
            HA = (HM0 * np.cos(ph) + HMud * np.sin(ph)) / Dg
            c = criterio_areas(phd, GZ, HA, phal)
            c.update(HA=HA, HM0=HM0, HMud=HMud, HA0=HM0 / Dg, z_CLR=zclr)
            casos[nome] = c
            AB_min = min(AB_min, c["AB"])
            gzsen_min = min(gzsen_min, c["GZsen_min"])
        out[plano] = dict(phi=phd, GZ=GZ, phi_al=phal, casos=casos)
    out["AB_min"], out["GZsen_min"] = AB_min, gzsen_min
    return out

# ============================================================================
# 6. HEAVE, ESPECTROS E AIR GAP (Exercício 10)
# ============================================================================
OMEGAS = np.linspace(0.02, 2.5, 1500)        # [rad/s] malha fina p/ ressonância


def ca_retangulo(a_sobre_b):
    """CA 2D de retângulo (DNV-RP-C205, Tab. A-1); a = meia-largura normal ao
    movimento (bp/2), b = meia-altura na direção do movimento (hp/2)."""
    tab_ab = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 1e6])
    tab_ca = np.array([2.23, 1.98, 1.70, 1.51, 1.36, 1.21, 1.14, 1.00])
    return float(np.interp(np.log(a_sobre_b), np.log(tab_ab), tab_ca))


def espectro_mar(w, Hs, Tp, gamma=None):
    """JONSWAP (DNV-RP-C205). [REV 6] γ = None -> lê GAMMA_JONSWAP na chamada."""
    gamma = GAMMA_JONSWAP if gamma is None else gamma
    wp = 2 * np.pi / Tp
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        S = (5.0 / 16.0) * Hs**2 * wp**4 * w**-5 * np.exp(-1.25 * (wp / w)**4)
        if gamma != 1.0:
            sig = np.where(w <= wp, 0.07, 0.09)
            S = S * (1 - 0.287 * np.log(gamma)) * gamma**np.exp(-0.5 * ((w - wp) / (sig * wp))**2)
    return np.nan_to_num(S)


def heave(x, hid, cen, gamma=None):
    Lp, bp, hp, bc, hc, T = map(float, x)
    gamma = GAMMA_JONSWAP if gamma is None else gamma
    M = hid["Delta"]
    A_wp = hid["A_wp"]
    A_p = 2 * Lp * bp                                   # área em planta dos pontoons
    CA = ca_retangulo(bp / hp)
    ld = Lp - 2 * bc                                    # [REV 2] comprimento livre
    A33 = 2 * ld * CA * RHO * np.pi * (bp / 2)**2       # massa adicional [t]
    C33 = RHO * G * A_wp                                # [kN/m]
    wn = np.sqrt(C33 / (M + A33))
    Tn = 2 * np.pi / wn
    B33 = 2 * XI_HEAVE * np.sqrt(C33 * (M + A33))       # [kN·s/m]

    w = OMEGAS
    k = w**2 / G
    dp = Lp - bp                                        # distância entre pontoons
    fase = np.cos(k * dp / 2)                           # [REV 2] cos(ω²dp/2g)
    d_top = max(T - hp, 0.0)                            # prof. do topo do pontoon
    F_col = RHO * G * A_wp * np.exp(-k * d_top) * fase
    F_pont = -RHO * G * A_p * (np.exp(-k * d_top) - np.exp(-k * T)) * fase
    F_dif = -A33 * w**2 * np.exp(-k * (T - hp / 2)) * fase
    F3 = F_col + F_pont + F_dif                         # [kN/m de amplitude]
    RAO = np.abs(F3) / np.abs(C33 - (M + A33) * w**2 + 1j * B33 * w)

    S = espectro_mar(w, cen.Hs, cen.Tp, gamma)
    Sz = RAO**2 * S
    m0z = trapezoid(Sz, w)
    Hz = 4 * np.sqrt(m0z)
    # H1/3 de heave com o outro γ (1,0 <-> 3,3), só para comparação
    gamma_alt = 1.0 if gamma != 1.0 else 3.3
    Hz_alt = 4 * np.sqrt(trapezoid(RAO**2 * espectro_mar(w, cen.Hs, cen.Tp, gamma_alt), w))
    troca = np.where(np.sign(F3[1:]) != np.sign(F3[:-1]))[0]   # 1ª troca de sinal
    i_canc = troca[0] + 1 if len(troca) else len(w) - 1
    return dict(M=M, A33=A33, CA=CA, ld=ld, C33=C33, B33=B33, wn=wn, Tn=Tn,
                omega=w, fase=fase, F_col=F_col, F_pont=F_pont, F_dif=F_dif, F3=F3,
                RAO=RAO, S=S, Sz=Sz, m0z=m0z, Hz=Hz, gamma=gamma,
                gamma_alt=gamma_alt, Hz_alt=Hz_alt,
                Hs_check=4 * np.sqrt(trapezoid(S, w)), w_cancel=w[i_canc])

# ============================================================================
# 7. MODELO COMPLETO, RESTRIÇÕES E VIABILIDADE
# ============================================================================
def avaliar(x, cen=CEN_G02, com_estab=True, dphi=DPHI_OTIM):
    x = np.asarray(x, float)
    Lp, bp, hp, bc, hc, T = x
    hid = hidrostatica(x)
    pes = pesos(x, hid, cen)
    hv = heave(x, hid, cen)
    a = hp + hc - T
    z_min = -1.86 * hv["Hz"] / 2
    r = dict(x=x, cen=cen, hid=hid, pes=pes, hv=hv, a=a, area=Lp**2,
             eta_max=cen.eta_max, z_min=z_min, a_min=cen.eta_max - z_min)
    if com_estab:
        r["est"] = estabilidade(x, hid, pes, cen, dphi=dphi)
    r["restr"] = tabela_restricoes(r)
    return r


def tabela_restricoes(r):
    Lp, bp, hp, bc, hc, T = r["x"]
    cen, pes, hv = r["cen"], r["pes"], r["hv"]
    # (nome, unidade, valor, sentido, limite, escala p/ otimizador e "ativa")
    L = [("Área de convés Lp²", "m²", r["area"], "≥", cen.area_req, 1000.0),
         ("GM_T mínimo", "m", pes["GM_T"], "≥", GM_MIN, 1.0),
         ("GM_T máximo", "m", pes["GM_T"], "≤", GM_MAX, 1.0),
         ("Período natural de heave Tn", "s", hv["Tn"], ">", TN_MIN, 1.0),
         ("Peso de lastro positivo", "t", pes["W_lastro"], ">", 0.0, 1e4),
         ("V_lastro ≤ 0,9·V_pontoons", "m³", pes["V_lastro"], "≤", FRAC_LASTRO * pes["V_pont"], 1e4),
         ("bc ≤ bp", "m", bc, "≤", bp, 1.0),
         ("Air gap a ≥ a_mín", "m", r["a"], "≥", r["a_min"], 1.0),
         ("Imersão das colunas T−hp (geométrica)", "m", T - hp, "≥", IMERSAO_MIN_COL, 1.0)]
    if LASTRO_MIN_FRAC > 0:                                         # [REV 4]
        L.append((f"V_lastro ≥ {LASTRO_MIN_FRAC:g}·V_pontoons", "m³", pes["V_lastro"], "≥",
                  LASTRO_MIN_FRAC * pes["V_pont"], 1e4))
    if "est" in r:
        L += [("Critério de áreas min(A/B), 4 casos", "-", r["est"]["AB_min"], "≥", AB_MIN, 1.0),
              ("GZ>0 até φ2/φal: min(GZ/senφ)", "m", r["est"]["GZsen_min"], ">", 0.0, 1.0)]
    linhas = []
    for nome, un, val, sentido, lim, esc in L:
        folga = val - lim if sentido in ("≥", ">") else lim - val
        ref = max(abs(lim), esc if esc > 1 else 1.0)
        estrita = sentido == ">"
        atende = folga > 0 if estrita else folga >= -1e-6
        margem = (MARGEM_OTIM + (1e-3 if estrita else 0.0)
                  + (MARGEM_AB_OTIM if nome.startswith("Critério") else 0.0))
        linhas.append(dict(Restrição=nome, Unid=un, Valor=val, Sentido=sentido,
                           Limite=lim, Folga=folga, Folga_pct=100 * folga / ref,
                           Atende="SIM" if atende else "NÃO",
                           Ativa="ATIVA" if (atende and abs(folga) / ref < 0.01) else "",
                           _g=folga / esc - margem))
    return pd.DataFrame(linhas)


def viavel(r):
    return bool((r["restr"].Atende == "SIM").all())

# ============================================================================
# 8. VALIDAÇÃO DO MODELO
# ============================================================================
X_REF = [100.0, 15.0, 15.0, 15.0, 45.0, 30.0]       # plataforma dos Ex. 7 a 10

# [REV 5] Valores obtidos em aula para a plataforma de referência
VALORES_AULA = {"KG [m]": 33.00, "min A/B transversal [-]": 2.33,
                "min A/B longitudinal [-]": 2.36, "Tn [s]": 20.70,
                "H1/3 heave [m]": 2.98}


def validacao():
    print("\n" + "=" * 90)
    print("VALIDAÇÃO DO MODELO")
    print("=" * 90)
    print("(a) Plataforma de referência dos Exercícios 7-10: Lp=100, bp=hp=bc=15, hc=45, T=30 m,")
    print(f"    BOE=120.000, Hs=12,2 m, Tp=14,6 s, hd={CEN_EX.hd:g} m, hm={CEN_EX.hm:g} m, "
          f"γ={GAMMA_JONSWAP:g}.")
    r = avaliar(X_REF, CEN_EX, dphi=DPHI_FINAL)
    h, p, hv, e = r["hid"], r["pes"], r["hv"], r["est"]
    ab_plano = {pl: min(c["AB"] for c in e[pl]["casos"].values()) for pl in PLANOS}
    ref = pd.Series({
        "∇ [m³]": h["V"], "Δ [t]": h["Delta"], "KB [m]": h["KB"],
        "BM_T [m]": h["BM_T"], "BM_L [m]": h["BM_L"], "KM_T [m]": h["KM_T"], "KM_L [m]": h["KM_L"],
        "W_casco [t]": p["W_casco"], "W_planta [t]": p["W_planta"], "W_topside [t]": p["W_topside"],
        "W_lastro [t]": p["W_lastro"], "KG [m]": p["KG"], "GM_T [m]": p["GM_T"], "GM_L [m]": p["GM_L"],
        "φal T [°]": e["Transversal"]["phi_al"], "φal L [°]": e["Longitudinal"]["phi_al"],
        "z_CLR T [m]": e["Transversal"]["casos"][next(iter(VENTOS))]["z_CLR"],
        "z_CLR L [m]": e["Longitudinal"]["casos"][next(iter(VENTOS))]["z_CLR"],
        "min A/B transversal [-]": ab_plano["Transversal"],
        "min A/B longitudinal [-]": ab_plano["Longitudinal"],
        "A33 [t]": hv["A33"], "Tn [s]": hv["Tn"],
        "H1/3 heave [m]": hv["Hz"], f"H1/3 heave γ={hv['gamma_alt']:g} [m]": hv["Hz_alt"],
        "a [m]": r["a"], "a_mín [m]": r["a_min"]})
    print(ref.to_string(float_format=lambda v: f"{v:,.3f}"))

    # [REV 5] comparação com os valores das aulas
    print("\n(b) Comparação com os resultados das aulas:")
    cmp_aula = pd.DataFrame([(k, ref[k], v) for k, v in VALORES_AULA.items()],
                            columns=["Grandeza", "Modelo", "Aula"])
    cmp_aula["Erro_%"] = 100 * (cmp_aula.Modelo - cmp_aula.Aula) / cmp_aula.Aula
    print(cmp_aula.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))

    # (c) verificações internas (consistência analítica)
    print("\n(c) Verificações de consistência:")
    chk = []
    for plano, GM in (("Transversal", p["GM_T"]), ("Longitudinal", p["GM_L"])):
        ph = np.array([0.0, 0.05])
        GZ, _ = curva_gz(X_REF, p["KG"], h["V"], plano, ph)
        inclinacao = GZ[1] / np.radians(0.05)
        chk.append((f"dGZ/dφ em 0° ({plano}) x GM", inclinacao, GM))
    chk.append(("RAO(ω→0) x 1,0 (corpo segue a onda)", hv["RAO"][0], 1.0))
    chk.append(("Hs recuperado do espectro x Hs", hv["Hs_check"], CEN_EX.Hs))
    chk.append(("Σ pesos x Δ [t]", sum(w for _, w, _ in p["itens"]), h["Delta"]))
    df = pd.DataFrame(chk, columns=["Verificação", "Modelo", "Esperado"])
    df["Erro_%"] = 100 * (df.Modelo - df.Esperado) / df.Esperado
    print(df.to_string(index=False))
    print("    Observação: dGZ/dφ ≈ GM confirma que a GZ 2D reproduz a hidrostática do Ex.7;")
    print("    RAO→1 em ω→0 e Hs recuperado validam força de excitação e integração espectral.")
    print("    (com γ = 3,3 a normalização aproximada 1 − 0,287·ln γ da DNV dá ~1% de erro no Hs)")
    return r, ref, cmp_aula, df

# ============================================================================
# 9. VARIAÇÃO SISTEMÁTICA (LHS) E FRONTEIRA DE PARETO
# ============================================================================
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


def _mapear(tarefas):
    """Roda as tarefas em paralelo (fork, Linux/Colab) ou em série."""
    if N_PROCESSOS > 1 and len(tarefas) > 1:
        import multiprocessing as mp
        if "fork" in mp.get_all_start_methods():
            with mp.get_context("fork").Pool(min(N_PROCESSOS, len(tarefas))) as pool:
                return pool.map(_tarefa_slsqp, tarefas)
    return [_tarefa_slsqp(t) for t in tarefas]


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

# ============================================================================
# 10. RELATÓRIOS
# ============================================================================
def ficha_tecnica(r):
    x, h, p, hv, e = r["x"], r["hid"], r["pes"], r["hv"], r["est"]
    d = {"Lp [m]": x[0], "bp [m]": x[1], "hp [m]": x[2], "bc [m]": x[3], "hc [m]": x[4],
         "T [m]": x[5], "Área de convés [m²]": r["area"], "Área mínima [m²]": r["cen"].area_req,
         "∇ [m³]": h["V"], "Δ [t]": h["Delta"], "KB [m]": h["KB"],
         "BM_T [m]": h["BM_T"], "BM_L [m]": h["BM_L"], "KM_T [m]": h["KM_T"], "KM_L [m]": h["KM_L"],
         "Peso casco [t]": p["W_casco"], "  pontoons [t]": p["W_pontoons"], "  colunas [t]": p["W_colunas"],
         "Peso planta [t]": p["W_planta"], "Peso topside [t]": p["W_topside"],
         "Risers + amarração [t]": p["W_risers"] + p["W_amarracao"],
         "Peso lastro [t]": p["W_lastro"], "V lastro / V pontoons [-]": p["V_lastro"] / p["V_pont"],
         "KG [m]": p["KG"], "GM_T [m]": p["GM_T"], "GM_L [m]": p["GM_L"],
         "φal transversal [°]": e["Transversal"]["phi_al"], "φal longitudinal [°]": e["Longitudinal"]["phi_al"],
         "min A/B (4 casos) [-]": e["AB_min"],
         "A33 [t]": hv["A33"], "C33 [kN/m]": hv["C33"], "ωn [rad/s]": hv["wn"], "Tn [s]": hv["Tn"],
         f"H1/3 heave γ={hv['gamma']:g} [m]": hv["Hz"],
         f"H1/3 heave γ={hv['gamma_alt']:g} [m]": hv["Hz_alt"],
         "η_max [m]": r["eta_max"], "z_min [m]": r["z_min"],
         "a_mín [m]": r["a_min"], "a [m]": r["a"], "Folga air gap [m]": r["a"] - r["a_min"]}
    return pd.Series(d)


def tabela_criterio(r):
    linhas = []
    for plano in PLANOS:
        ep = r["est"][plano]
        for nome, c in ep["casos"].items():
            linhas.append({"Plano": plano, "Vento": nome, "z_CLR [m]": c["z_CLR"],
                           "HM0 [kN·m]": c["HM0"], "HMud [kN·m]": c["HMud"], "HA(0) [m]": c["HA0"],
                           "φ1 [°]": c["phi1"], "φ2 [°]": c["phi2"], "φal [°]": ep["phi_al"],
                           "A [m·rad]": c["A"], "B [m·rad]": c["B"], "A/B": c["AB"],
                           "A ≥ 1,3B": "SIM" if c["AB"] >= AB_MIN else "NÃO",
                           "GZ>0 até φ2/φal": "SIM" if c["GZsen_min"] > 0 else "NÃO"})
    return pd.DataFrame(linhas)


def imprimir_restricoes(r, titulo):
    df = r["restr"].drop(columns="_g")
    print(f"\n--- Tabela-resumo de restrições: {titulo} ---")
    print(df.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))


def salvar(fig, nome):
    fig.savefig(os.path.join(OUT_DIR, nome), dpi=150, bbox_inches="tight")

# ============================================================================
# 11. GRÁFICOS
# ============================================================================
def grafico_pareto(df_am, df_ws, df_eps, front, sols):
    fig, ax = plt.subplots(figsize=(11, 7))
    inv = df_am[df_am.pre_viavel & ~df_am.viavel]
    ok = df_am[df_am.viavel]
    ax.scatter(df_am.W_casco[~df_am.pre_viavel], df_am.Hz[~df_am.pre_viavel], s=4, c="lightgray",
               label="Amostras inviáveis")
    ax.scatter(inv.W_casco, inv.Hz, s=10, c="orange", alpha=0.6,
               label="Inviáveis só no critério de vento/GZ")
    ax.scatter(ok.W_casco, ok.Hz, s=14, c="tab:blue", alpha=0.7, label="Soluções viáveis (LHS)")
    ax.plot(df_ws.W_casco, df_ws.Hz, "s", c="k", ms=5, label="Ótimos da soma ponderada (SLSQP)")
    if len(df_eps):
        ax.plot(df_eps.W_casco, df_eps.Hz, "^", c="purple", ms=6, label="Ótimos ε-restrito (SLSQP)")
    ax.plot(front.W_casco, front.Hz, "-", c="crimson", lw=2, label="Fronteira de Pareto")
    cores = {"1. Mín. peso": "red", "2. Mín. heave": "green", "3. Intermediária (escolhida)": "gold"}
    for nome, r in sols.items():
        W, H = r["pes"]["W_casco"], r["hv"]["Hz"]
        ax.plot(W, H, "o", ms=12, mec="k", c=cores[nome], label=nome, zorder=5)
        ax.annotate(f"{W:,.0f} t\n{H:.3f} m", (W, H), textcoords="offset points",   # [REV 6]
                    xytext=(12, 8), fontsize=9, bbox=dict(boxstyle="round", fc="white", ec=cores[nome]))
    Wmax = max(front.W_casco.max(), ok.W_casco.max() if len(ok) else 0) * 1.25
    Hmax = max(front.Hz.max(), ok.Hz.max() if len(ok) else 0) * 1.3
    ax.set_xlim(front.W_casco.min() * 0.9, Wmax)
    ax.set_ylim(0, Hmax)
    ax.set_xlabel("Peso estrutural do casco [t]", fontweight="bold")
    ax.set_ylabel("Altura significativa de heave H1/3,z [m]", fontweight="bold")
    ax.set_title("Grupo 02 - Conjunto viável e fronteira de Pareto (Peso × Hs heave)", fontweight="bold")
    ax.grid(ls="--", alpha=0.6)
    ax.legend(fontsize=9, loc="upper right")
    salvar(fig, "01_pareto.png")


def grafico_gz(r, titulo, arq):
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.5))
    for ax, plano in zip(axs, PLANOS):
        ep = r["est"][plano]
        ph, GZ, phal = ep["phi"], ep["GZ"], ep["phi_al"]
        sel = ph <= max(50.0, phal)
        ax.plot(ph[sel], GZ[sel], "b", lw=2.2, label="GZ")
        estilos = {"Tempestade 51,5 m/s": "r", "Operação 36 m/s": "darkorange"}
        for nome, c in ep["casos"].items():
            ax.plot(ph[sel], c["HA"][sel], "--", c=estilos[nome], lw=1.8, label=f"HA - {nome}")
            for k, mk in (("phi1", "o"), ("phi2", "s")):
                if c[k] is not None and c[k] <= ph[sel][-1]:
                    ax.plot(c[k], np.interp(c[k], ph, GZ), mk, c=estilos[nome], ms=7)
        m = ph <= phal
        ax.fill_between(ph[m], 0, GZ[m], color="b", alpha=0.08, label="Área A (0 a φal)")
        ax.axvline(phal, c="k", ls=":", lw=1.5, label=f"φal = {phal:.2f}°")
        ax.set_title(f"{plano}  (min A/B = "
                     f"{min(c['AB'] for c in ep['casos'].values()):.2f})", fontweight="bold")
        ax.set_xlabel("Ângulo de inclinação φ [°]", fontweight="bold")
        ax.set_ylabel("GZ, HA [m]", fontweight="bold")
        ax.grid(ls="--", alpha=0.6)
        ax.legend(fontsize=8)
        ax.set_xlim(0, ph[sel][-1])
    fig.suptitle(titulo + "  (● φ1, ■ φ2)", fontweight="bold", fontsize=13)
    fig.tight_layout()
    salvar(fig, arq)


def grafico_heave(r, titulo, arq):
    hv = r["hv"]
    w = hv["omega"]
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    ax = axs[0, 0]
    ax.plot(w, hv["F_col"] / 1e3, label="Froude-Krylov colunas")
    ax.plot(w, hv["F_pont"] / 1e3, label="Froude-Krylov pontoons")
    ax.plot(w, hv["F_dif"] / 1e3, label="Difração (massa adicional)")
    ax.plot(w, hv["F3"] / 1e3, "k", lw=2, label="F3 total")
    ax.axvline(hv["w_cancel"], c="gray", ls=":", label=f"cancelamento ω={hv['w_cancel']:.3f}")
    ax.set_title("Força de excitação em heave por amplitude de onda\n(com fator cos(ω²dp/2g))",
                 fontweight="bold")
    ax.set_xlabel("ω [rad/s]"); ax.set_ylabel("F3/ζ [MN/m]"); ax.grid(ls="--", alpha=.6); ax.legend(fontsize=8)
    ax = axs[0, 1]
    ax.plot(w, hv["RAO"], "b", lw=2)
    ax.axvline(hv["wn"], c="r", ls="--", label=f"ωn = {hv['wn']:.3f} rad/s (Tn = {hv['Tn']:.2f} s)")
    ax.set_title("RAO de heave", fontweight="bold"); ax.set_xlabel("ω [rad/s]"); ax.set_ylabel("RAO [m/m]")
    ax.set_xlim(0, 1.5); ax.grid(ls="--", alpha=.6); ax.legend()
    ax = axs[1, 0]
    ax.plot(w, hv["S"], "teal", lw=2)
    ax.set_title(f"Espectro de mar JONSWAP γ={hv['gamma']:g}  Hs={r['cen'].Hs} m, Tp={r['cen'].Tp} s",
                 fontweight="bold")
    ax.set_xlabel("ω [rad/s]"); ax.set_ylabel("Sζ [m²·s/rad]"); ax.set_xlim(0, 1.5); ax.grid(ls="--", alpha=.6)
    ax = axs[1, 1]
    ax.plot(w, hv["Sz"], "purple", lw=2)
    ax.axvline(hv["wn"], c="r", ls="--", label="ωn")
    ax.set_title(f"Espectro de resposta Sz = RAO²·Sζ  →  H1/3,z = {hv['Hz']:.3f} m", fontweight="bold")
    ax.set_xlabel("ω [rad/s]"); ax.set_ylabel("Sz [m²·s/rad]"); ax.set_xlim(0, 1.5)
    ax.grid(ls="--", alpha=.6); ax.legend()
    fig.suptitle(titulo, fontweight="bold", fontsize=13)
    fig.tight_layout()
    salvar(fig, arq)


def grafico_geometria(sols):
    fig, axs = plt.subplots(1, 3, figsize=(17, 6))
    for ax, (nome, r) in zip(axs, sols.items()):
        Lp, bp, hp, bc, hc, T = r["x"]
        hd, hm = r["cen"].hd, r["cen"].hm
        ax.add_patch(plt.Rectangle((-Lp / 2, 0), Lp, hp, fc="steelblue", ec="k", label="Pontoon"))
        for xc in (-Lp / 2, Lp / 2 - bc):
            ax.add_patch(plt.Rectangle((xc, hp), bc, hc, fc="seagreen", ec="k"))
        ax.add_patch(plt.Rectangle((-Lp / 2, hp + hc), Lp, hd, fc="gray", ec="k"))
        ax.add_patch(plt.Rectangle((-Lp / 2 * FRAC_LARG_MODULOS, hp + hc + hd), Lp * FRAC_LARG_MODULOS, hm,
                                   fc="lightgray", ec="k", hatch="//"))
        ax.axhline(T, c="b", ls="--", label="LA de projeto")
        ax.axhline(T + r["eta_max"], c="c", ls=":", label="Crista máxima η_max")
        ax.set_xlim(-Lp / 2 - 10, Lp / 2 + 10); ax.set_ylim(-5, 110)
        ax.set_aspect("equal"); ax.grid(ls="--", alpha=.4)
        ax.set_title(f"{nome}\nLp={Lp:.1f} bp={bp:.1f} hp={hp:.1f} bc={bc:.1f} hc={hc:.1f} T={T:.1f} m",
                     fontsize=10, fontweight="bold")
        ax.set_xlabel("x [m]")
    axs[0].set_ylabel("z a partir da quilha [m]"); axs[0].legend(fontsize=8, loc="upper left")
    fig.suptitle("Vista lateral das três soluções (convés + módulos em cinza)", fontweight="bold")
    fig.tight_layout()
    salvar(fig, "05_geometria_3_cenarios.png")

# ============================================================================
# 12. EXECUÇÃO
# ============================================================================
if __name__ == "__main__":
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    cen = CEN_G02
    print("=" * 90)
    print(f"PNV3425 - TRABALHO FINAL - {cen.nome}")
    print("=" * 90)
    print(f"Produção de pico: {cen.BOE:,.2f} boe/dia (Q = {cen.Q:.3f} mil BOE/d) | "
          f"gás incluído: {'SIM' if INCLUIR_GAS else 'NÃO'} (fator óleo+gás = {FATOR_GAS:.3f})")
    print(f"Mar de projeto (100 anos): Hs = {cen.Hs} m, Tp = {cen.Tp} s | Tp/√Hs = {cen.Tp/np.sqrt(cen.Hs):.2f}"
          f" | γ = {GAMMA_JONSWAP:g}")
    print(f"Ventos de verificação: {list(VENTOS.values())} m/s | hd = {cen.hd} m, hm = {cen.hm} m")
    print(f"Área mínima de convés: {cen.area_req:,.1f} m² -> Lp ≥ {np.sqrt(cen.area_req):.2f} m")
    print(f"Crista máxima η_max = 1,86·Hs/2 = {cen.eta_max:.3f} m | lastro mínimo = "
          f"{LASTRO_MIN_FRAC:g}·V_pontoons")

    # ---------------- Validação ----------------
    r_val, s_val, cmp_aula, df_chk = validacao()
    s_val.to_csv(os.path.join(OUT_DIR, "validacao_plataforma_ref.csv"), header=["valor"])
    cmp_aula.to_csv(os.path.join(OUT_DIR, "validacao_vs_aula.csv"), index=False)
    grafico_gz(r_val, "Validação - plataforma dos Ex. 7-10: GZ e HA", "00_validacao_gz.png")

    # ---------------- Variação sistemática ----------------
    print("\n" + "=" * 90)
    print(f"VARIAÇÃO SISTEMÁTICA: {N_AMOSTRAS} combinações (Latin Hypercube) nos limites:")
    for n, b in zip(NOMES_X, BOUNDS):
        print(f"   {n:>2s}: {b[0]:7.2f} a {b[1]:7.2f} m")
    # REAPROVEITAR=1: recarrega as etapas já salvas em OUT_DIR (útil se a
    # sessão do Colab cair). Apague os CSVs ao mudar o modelo ou os limites.
    REAPROVEITAR = os.environ.get("REAPROVEITAR", "0") == "1"

    def etapa(arquivo, funcao):
        caminho = os.path.join(OUT_DIR, arquivo)
        if REAPROVEITAR and os.path.exists(caminho):
            print(f"   (reaproveitado de {caminho})")
            try:
                return pd.read_csv(caminho)
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
        t1 = time.time()
        df = funcao()
        df.to_csv(caminho, index=False)
        print(f"   [{time.time()-t1:.0f} s]")
        return df

    df_am = etapa("amostras_variacao_sistematica.csv", variacao_sistematica)
    n_pre, n_ok = int(df_am.pre_viavel.sum()), int(df_am.viavel.sum())
    print(f"   Atendem às restrições estáticas/heave/air gap: {n_pre}")
    print(f"   Viáveis (incluindo critério de áreas e GZ>0): {n_ok}")
    if n_ok == 0:
        raise SystemExit("Nenhuma amostra viável: amplie os limites ou N_AMOSTRAS.")

    # ---------------- Soma ponderada ----------------
    print("\nOTIMIZAÇÃO POR SOMA PONDERADA: F = w1·Hz + w2·W_casco/10000 (SLSQP, multi-start + continuação)")
    df_ws = etapa("pareto_soma_ponderada.csv", lambda: soma_ponderada(df_am))

    print("\nMÉTODO ε-RESTRITO: min W_casco sujeito a Hz ≤ ε (preenche trechos não convexos)")
    df_eps = etapa("pareto_epsilon_restrito.csv", lambda: epsilon_restrito(df_ws, df_am))

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
    print(f"\nFronteira de Pareto: {len(front)} pontos não dominados entre {len(viaveis)} soluções viáveis")
    print(front.to_string(float_format=lambda v: f"{v:,.3f}"))

    # ---------------- 3 cenários ----------------
    i_W, i_H = front.W_casco.idxmin(), front.Hz.idxmin()
    i_K = ponto_joelho(front.W_casco.values, front.Hz.values)
    sols = {}
    for nome, i in (("1. Mín. peso", i_W), ("2. Mín. heave", i_H), ("3. Intermediária (escolhida)", i_K)):
        r = avaliar(front.loc[i, NOMES_X].values.astype(float), cen, dphi=DPHI_FINAL)
        assert viavel(r), f"{nome} não confirmou viabilidade no passo angular fino"
        sols[nome] = r
        print(f"   {nome}: origem = {front.loc[i, 'origem']}")
    rW, rH, rK = sols.values()

    print("\n" + "=" * 90)
    print("JUSTIFICATIVA DA SOLUÇÃO FINAL (ponto 'joelho' da fronteira)")
    print("=" * 90)
    dW = 100 * (rK["pes"]["W_casco"] / rW["pes"]["W_casco"] - 1)
    dH_ganho = 100 * (1 - rK["hv"]["Hz"] / rW["hv"]["Hz"])
    dW_poup = 100 * (1 - rK["pes"]["W_casco"] / rH["pes"]["W_casco"])
    dH_perda = 100 * (rK["hv"]["Hz"] / rH["hv"]["Hz"] - 1)
    print("A solução escolhida é o ponto da fronteira mais próximo do ponto utópico (mín. peso, mín. Hz)")
    print("no plano normalizado. Em relação à solução de mínimo peso, ela aumenta o peso do casco em")
    print(f"{dW:.1f}% e reduz o Hs de heave em {dH_ganho:.1f}%. Em relação à de mínimo heave, ela economiza")
    print(f"{dW_poup:.1f}% do peso do casco, com Hs de heave {dH_perda:.1f}% maior. Como o ponto está no")
    print("'joelho', mover-se para qualquer lado custa mais em um objetivo do que se ganha no outro.")
    print(f"Atende a todas as restrições; folga de air gap = {rK['a'] - rK['a_min']:.2f} m.")

    # Ficha técnica comparativa
    ficha = pd.DataFrame({k: ficha_tecnica(v) for k, v in sols.items()})
    print("\n" + "=" * 90)
    print("FICHA TÉCNICA COMPARATIVA - 3 CENÁRIOS")
    print("=" * 90)
    print(ficha.to_string(float_format=lambda v: f"{v:,.3f}"))
    ficha.to_csv(os.path.join(OUT_DIR, "ficha_tecnica_3_cenarios.csv"))

    # Restrições e restrições ativas
    for nome, r in sols.items():
        imprimir_restricoes(r, nome)
        r["restr"].drop(columns="_g").to_csv(os.path.join(OUT_DIR, f"restricoes_{nome[:2].strip('.')}.csv"),
                                             index=False)
        ativas = r["restr"].loc[r["restr"].Ativa == "ATIVA", "Restrição"].tolist()
        print(f"   Restrições ativas (folga < 1%): {ativas if ativas else 'nenhuma'}")
        lim = variaveis_no_limite(r["x"])
        print(f"   Variáveis no limite do domínio: {lim if lim else 'nenhuma'}")

    # ---------------- Detalhamento da solução final ----------------
    print("\n" + "=" * 90)
    print("SOLUÇÃO FINAL - DETALHAMENTO")
    print("=" * 90)
    print("Pesos e centros:")
    print(tabela_pesos(rK["pes"]).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"KB = {rK['hid']['KB']:.3f} m | KG = {rK['pes']['KG']:.3f} m | GM_T = {rK['pes']['GM_T']:.3f} m |"
          f" GM_L = {rK['pes']['GM_L']:.3f} m | Área de convés = {rK['area']:,.1f} m²")

    print("\nForças, braços e momentos de vento por parcela (braço até o z_CLR de cada plano):")
    for plano in PLANOS:
        for nome, (linhas_v, HM0, HMud, zclr) in rK["est"]["vento"][plano].items():
            df_v = pd.DataFrame(linhas_v)
            print(f"  >> {plano} | {nome}:  z_CLR = {zclr:.2f} m | HM0 = {HM0:,.0f} kN·m | "
                  f"HMud = {HMud:,.0f} kN·m | HA(0) = {HM0/(rK['hid']['Delta']*G):.4f} m")
            print(df_v.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
            df_v.to_csv(os.path.join(OUT_DIR, f"vento_{plano.lower()}_{nome.split()[0].lower()}.csv"),
                        index=False)

    df_crit = tabela_criterio(rK)
    print("\nCritério de áreas (DNV-OS-C301 / MODU 2009):")
    print(df_crit.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
    df_crit.to_csv(os.path.join(OUT_DIR, "criterio_areas_solucao_final.csv"), index=False)

    hv = rK["hv"]
    print("\nHeave:")
    print(f"  M = {hv['M']:,.0f} t | CA = {hv['CA']:.3f} | ld = {hv['ld']:.2f} m | A33 = {hv['A33']:,.0f} t"
          f" | C33 = {hv['C33']:,.0f} kN/m | B33 = {hv['B33']:,.0f} kN·s/m")
    print(f"  ωn = {hv['wn']:.4f} rad/s | Tn = {hv['Tn']:.2f} s | ω de cancelamento = {hv['w_cancel']:.3f} rad/s")
    print(f"  m0z = {hv['m0z']:.5f} m² | H1/3,z = {hv['Hz']:.4f} m (γ={hv['gamma']:g}) | "
          f"{hv['Hz_alt']:.4f} m (γ={hv['gamma_alt']:g})")
    wp = 2 * np.pi / cen.Tp
    for rot, wv in (("ωp do mar", wp), ("ωn", hv["wn"])):
        j = np.argmin(np.abs(hv["omega"] - wv))
        print(f"  Em {rot} = {wv:.3f} rad/s: cos(ω²dp/2g) = {hv['fase'][j]:.3f}, F_col = {hv['F_col'][j]:,.0f}, "
              f"F_pont = {hv['F_pont'][j]:,.0f}, F_dif = {hv['F_dif'][j]:,.0f}, F3 = {hv['F3'][j]:,.0f} kN/m"
              f" | RAO = {hv['RAO'][j]:.3f}")
    pd.DataFrame({"omega": hv["omega"], "fase_cos": hv["fase"], "F_col_kN_m": hv["F_col"],
                  "F_pont_kN_m": hv["F_pont"], "F_dif_kN_m": hv["F_dif"], "F3_kN_m": hv["F3"],
                  "RAO": hv["RAO"], "S_mar": hv["S"], "S_resp": hv["Sz"]}).to_csv(
        os.path.join(OUT_DIR, "heave_solucao_final.csv"), index=False)

    print("\nVerificação do air gap:")
    print(f"  η_max = {rK['eta_max']:.3f} m | z_min = {rK['z_min']:.3f} m | a_mín = {rK['a_min']:.3f} m |"
          f" a = {rK['a']:.3f} m | folga = {rK['a'] - rK['a_min']:.3f} m")

    # ---------------- Gráficos ----------------
    grafico_pareto(df_am, df_ws, df_eps, front, sols)
    grafico_gz(rK, "Solução final - GZ e HA nos planos transversal e longitudinal", "02_gz_ha_solucao_final.png")
    grafico_heave(rK, "Solução final - Heave", "03_heave_solucao_final.png")
    grafico_gz(rW, "Cenário 1 (mín. peso) - GZ e HA", "04a_gz_min_peso.png")
    grafico_gz(rH, "Cenário 2 (mín. heave) - GZ e HA", "04b_gz_min_heave.png")
    grafico_geometria(sols)

    print(f"\nArquivos salvos em ./{OUT_DIR}/  |  tempo total: {time.time()-t0:.0f} s")
    if MOSTRAR_GRAFICOS:
        plt.show()
