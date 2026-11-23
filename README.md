# PNV3425 – Projeto de Sistemas Oceânicos

Trabalho final do 2º semestre de 2026 (Escola Politécnica da USP, Departamento de Engenharia
Naval e Oceânica): **projeto paramétrico de uma plataforma semissubmersível de produção** para o
bloco KZ-2026-B, na bacia do Baixo Congo (Angola). Grupo 02.

A plataforma tem 2 pontoons retangulares e 4 colunas quadradas em planta quadrada de lado `Lp`.
O modelo calcula hidrostática, pesos e centros, curva GZ por projeções 2D, critério de áreas
para o momento de vento (DNV-OS-C301 / MODU 2009), resposta em heave no mar de 100 anos e air
gap mínimo, e otimiza o peso estrutural do casco e o Hs de heave (fronteira de Pareto).

## Solução escolhida

| Lp | bp | hp | bc | hc | T | Peso do casco | Hs de heave | Tn | min A/B |
|---|---|---|---|---|---|---|---|---|---|
| 111,8 m | 13,4 m | 10,2 m | 12,6 m | 39,6 m | 24,0 m | 14.998 t | 1,55 m | 21,8 s | 1,303 |

## Conteúdo

| Pasta | Conteúdo |
|---|---|
| `codigo/pnv3425_grupo02.py` | Modelo paramétrico, validação e otimização (LHS + soma ponderada + ε-restrito) |
| `codigo/analises_complementares.py` | Curva de produção, restrições ativas na fronteira, sensibilidade a hd/hm, ξ e γ |
| `resultados/` | Figuras, tabelas CSV e log da rodada do caso-base |
| `resultados/complementar/` | Saídas de `analises_complementares.py` |
| `resultados/sensibilidade_*` | Reotimizações com hm = 15 m, gás no BOE e lastro mínimo de 10% |
| `relatorio/` | Relatório em LaTeX (`relatorio.tex`) e PDF compilado |
| `apresentacao/` | Apresentações em PPTX e PDF: versão completa (35 slides) e versão de 15 minutos (14 slides, com notas do apresentador e tempos) |
| `apresentacao/figuras_apresentacao.py` | Figuras e equações das apresentações, no layout do grupo |
| `apresentacao/gerar_apresentacoes.py` | Gera os dois PPTX (python-pptx) |

## Como rodar

Na raiz do repositório:

```bash
pip install -r requirements.txt
python codigo/pnv3425_grupo02.py          # ~4 min em 8 núcleos
python codigo/analises_complementares.py
```

Variáveis de ambiente opcionais:

| Variável | Padrão | Efeito |
|---|---|---|
| `OUT_DIR` | `resultados` | Pasta de saída |
| `HD`, `HM` | `8`, `12` | Alturas do deck box e dos módulos [m] |
| `INCLUIR_GAS` | `0` | `1` soma o gás convertido em boe à produção |
| `LASTRO_MIN_FRAC` | `0` | Lastro mínimo como fração do volume dos pontoons |
| `PASSO_W` | `0.05` | Passo de w1 na soma ponderada |
| `N_AMOSTRAS` | `20000` | Amostras do hipercubo latino |
| `N_PROCESSOS` | nº de núcleos | Processos paralelos do SLSQP |
| `REAPROVEITAR` | `0` | `1` retoma etapas já salvas em `OUT_DIR` |
| `MOSTRAR_GRAFICOS` | `1` | `0` não abre as figuras ao final |

Exemplo de sensibilidade: `OUT_DIR=resultados/sensibilidade_hm15 HM=15 python codigo/pnv3425_grupo02.py`.

## Gerar as apresentações

```bash
pip install python-pptx
python apresentacao/figuras_apresentacao.py
python apresentacao/gerar_apresentacoes.py
soffice --headless --convert-to pdf --outdir apresentacao apresentacao/*.pptx   # ou exportar pelo PowerPoint
```

## Compilar o relatório

O relatório usa `fontspec` e deve ser compilado com XeLaTeX ou
[Tectonic](https://tectonic-typesetting.github.io/), a partir da pasta `relatorio/` (as figuras
são lidas de `../resultados/`):

```bash
cd relatorio && tectonic relatorio.tex
```

No Overleaf, envie o repositório inteiro e selecione o compilador XeLaTeX.

Grupo 02: Felipe Perpétuo Simões (11263255), Gustavo Guilherme Silva (11820555) e
João Marcos Magalhães Moura (12554693).
