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
