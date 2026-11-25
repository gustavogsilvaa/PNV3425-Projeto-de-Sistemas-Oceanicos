# PNV3425 – Projeto de Sistemas Oceânicos

Trabalho final do 2º semestre de 2026 (Escola Politécnica da USP, Departamento de Engenharia
Naval e Oceânica): **projeto paramétrico de uma plataforma semissubmersível de produção** para o
bloco KZ-2026-B, na bacia do Baixo Congo (Angola), em 1.450 m de lâmina d'água.

A plataforma tem 2 pontoons retangulares e 4 colunas quadradas em planta quadrada de lado `Lp`.
O modelo calcula hidrostática, pesos e centros, curva GZ por projeções 2D, critério de áreas para
o momento de vento (DNV-OS-C301 / MODU 2009), resposta em heave no mar de 100 anos e air gap
mínimo, e otimiza o peso estrutural do casco e o H1/3 de heave (fronteira de Pareto).

**Grupo 02:** Felipe Perpétuo Simões (11263255), Gustavo Guilherme Silva (11820555) e
João Marcos Magalhães Moura (12554693).

## Duas versões do projeto

| | [`caso_base/`](caso_base) | [`condicao_10pct_lastro/`](condicao_10pct_lastro) — **Condição de 10% de lastro** |
|---|---|---|
| Restrição de lastro | lastro positivo (enunciado) | lastro positivo **e** `V_lastro ≥ 0,10·V_pontoons` |
| Código | `codigo/pnv3425_grupo02.py` | `codigo/pnv3425_grupo02_condicao_10pct_lastro.py` |
| Resultados | `resultados/` | `resultados_lastro10/` |
| Relatório | [`relatorio/relatorio.pdf`](relatorio/relatorio.pdf) (Seções 2 a 11) | [`relatorio/relatorio.pdf`](relatorio/relatorio.pdf) (Seção 12) |
| Fronteira de Pareto | 25 pontos, 10.346 t a 23.634 t | 23 pontos, 11.892 t a 23.634 t |
| Solução escolhida | Lp = 111,8 m · T = 24,0 m | Lp = 107,5 m · T = 25,9 m |
| Peso do casco | 14.998 t | 16.026 t (+6,9%) |
| Lastro | 11 t | 3.611 t |
| KG · GM_T | 42,82 m · 4,00 m | 38,38 m · 4,00 m |
| H1/3 de heave · Tn | 1,552 m · 21,85 s | 1,549 m · 21,73 s |
| min A/B | 1,303 | 1,303 |
| Folga de air gap | 19,2 m | 16,4 m |

Os dois códigos são os mesmos do desenvolvimento do trabalho; o da condição de 10% de lastro
difere do caso-base apenas nas linhas marcadas com `[LASTRO 10%]` (lastro mínimo obrigatório,
pasta de saída e rótulos).

## Estrutura

```
caso_base/
  codigo/pnv3425_grupo02.py              modelo, validação e otimização (caso-base)
  codigo/analises_complementares.py      curva de produção, restrições ativas, sensibilidade hd/hm, ξ, γ
  codigo/comparativo_plataformas_reais.py CLOV, Scarabeo 5 e semis de produção do Golfo do México
  codigo/comparativo_poster_2011.py      validação do casco e comparação com o pôster de 2011
  codigo/figuras_apresentacao.py         figuras no padrão visual da apresentação
  resultados/                            figuras, tabelas CSV, logs e sensibilidades (hm = 15 m, gás)
condicao_10pct_lastro/
  codigo/pnv3425_grupo02_condicao_10pct_lastro.py   modelo e otimização com lastro ≥ 10%
  codigo/analises_condicao_10pct_lastro.py           comparação com o caso-base e com o pôster;
                                                     gera relatorio/tabelas_lastro10/
  resultados_lastro10/                   figuras, tabelas CSV e log
relatorio/                               relatório único (caso-base + condição de 10% de lastro)
  relatorio.tex · relatorio.pdf          teoria, aplicação e resultados; código no Apêndice A
  tabelas_lastro10/                      tabelas geradas pelo script de análise da condição de 10%
  gerar_trechos.py · trechos/            trechos do código real citados no Apêndice A
apresentacao/                            apresentação final (PNV3425_Apresentação_Final_G2_V2.pdf e .pptx)
```

## Como rodar

```bash
pip install -r requirements.txt

cd caso_base
python codigo/pnv3425_grupo02.py                 # ~4 min em 8 núcleos
python codigo/analises_complementares.py
python codigo/comparativo_plataformas_reais.py
python codigo/comparativo_poster_2011.py

cd ../condicao_10pct_lastro
python codigo/pnv3425_grupo02_condicao_10pct_lastro.py   # ~3 min em 8 núcleos
python codigo/analises_condicao_10pct_lastro.py           # usa também ../caso_base/resultados
```

Variáveis de ambiente opcionais dos dois modelos: `OUT_DIR`, `HD`, `HM`, `INCLUIR_GAS`,
`LASTRO_MIN_FRAC`, `PASSO_W`, `N_AMOSTRAS`, `N_EPSILON`, `N_PROCESSOS`, `REAPROVEITAR` e
`MOSTRAR_GRAFICOS` (descritas no cabeçalho de cada código).

## Relatório

Um único relatório cobre as duas versões, na sequência da apresentação final: dados do campo,
modelo paramétrico (teoria e equações de cada etapa), validação, procedimento de otimização,
fronteira de Pareto, escolha da solução, três cenários, plataformas reais, solução final,
sensibilidade, condição de 10% de lastro, discussão das hipóteses e conclusões. O Apêndice A traz
a implementação: funções × equações, desempenho, trechos do código real com a numeração de
linhas original e o *diff* entre as duas versões. O Apêndice B traz as duas fronteiras de Pareto
completas.

O relatório usa `fontspec` e deve ser compilado com XeLaTeX ou
[Tectonic](https://tectonic-typesetting.github.io/), dentro da pasta `relatorio/` (as figuras são
lidas das pastas de resultados das duas versões):

```bash
cd condicao_10pct_lastro && python codigo/analises_condicao_10pct_lastro.py   # tabelas da Seção 12
cd ../relatorio && python gerar_trechos.py                                    # trechos do Apêndice A
tectonic relatorio.tex
```

No Overleaf, envie o repositório inteiro e selecione o compilador XeLaTeX.
