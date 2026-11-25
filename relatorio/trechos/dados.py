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
