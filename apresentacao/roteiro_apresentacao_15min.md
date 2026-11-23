# Roteiro da apresentação de 15 minutos · Grupo 02

PNV3425 – Projeto de Sistemas Oceânicos · arquivo `PNV3425_G02_apresentacao_15min.pptx`. O mesmo texto está nas notas do apresentador de cada slide.

## Divisão

| Membro | Slides | Tempo | Bloco |
|---|---|---|---|
| Felipe Perpétuo Simões | 1–5 | 5:00 | Abertura, campo, modelo, validação e otimização |
| Gustavo Guilherme Silva | 6–9 | 5:00 | Fronteira de Pareto, cenários e solução final (pesos e estabilidade) |
| João Marcos Magalhães Moura | 10–14 | 4:30 | Heave, escolha, plataformas reais, sensibilidade e conclusões |

Tempo total de fala: 14:30 (folga de 0:30 até 15:00).

## 1. Projeto paramétrico de uma semissubmersível · Felipe · 0:00–0:40

Bom dia. Somos o Grupo 02: eu sou o Felipe, e comigo estão o Gustavo e o João. Nosso trabalho é o projeto paramétrico da semissubmersível de produção do bloco KZ-2026-B, na bacia do Baixo Congo, em Angola. O objetivo é encontrar o casco de menor peso estrutural e de menor movimento de heave que atenda a todas as restrições do enunciado. Eu apresento o campo, o modelo e a validação; o Gustavo apresenta a fronteira de Pareto e a solução escolhida; e o João fecha com o heave, o comparativo com plataformas reais e as conclusões.

**Números-chave:** Bloco KZ-2026-B, Baixo Congo, 1.450 m · Dois objetivos: peso do casco e Hs de heave

**Deixa visual:** Olhar para a banca; apontar os colegas ao citar os blocos.

**Transição:** Começo pelo campo.

## 2. O campo KZ-2026-B · Felipe · 0:40–1:40

O campo fica a 190 km da costa, em 1.450 m de lâmina d'água. São 2,2 bilhões de barris de óleo original, com fator de recuperação de 30%, ou seja, 660 milhões de barris recuperáveis, além de 30 bilhões de metros cúbicos de gás. A curva de produção tem pico de 158.894 barris por dia entre os anos 5 e 7, e é esse pico que dimensiona a planta. Pela correlação da aula, isso dá uma área mínima de convés de 11.563 metros quadrados, ou seja, Lp de pelo menos 107,5 m, e uma planta de 13.188 t. O mar de 100 anos é brando: Hs de 5,6 m e Tp de 15,2 s, menos da metade do Hs dos exercícios. No caso-base usamos só o óleo; o caso com gás aparece na sensibilidade.

**Números-chave:** Pico: 158.894 bpd · Área mínima: 11.563 m² (Lp ≥ 107,5 m) · Planta: 13.188 t · Hs = 5,6 m, Tp = 15,2 s

**Deixa visual:** Apontar os três cartões à direita, de cima para baixo.

**Transição:** Com esses dados de entrada, montamos o modelo.

## 3. Modelo paramétrico: geometria e variáveis · Felipe · 1:40–3:00

As variáveis de projeto são o lado da planta Lp, a largura e a altura dos pontoons, o lado e a altura das colunas e o calado. Para cada combinação, o modelo encadeia os Exercícios 7 a 10: hidrostática; pesos, KG e GM; curva GZ por projeções 2D nos dois planos e critério de áreas para os ventos de 51,5 e 36 m/s; heave, com forças de Froude-Krylov e de massa adicional, RAO e espectro de resposta no mar de 100 anos; e por fim o air gap mínimo, que soma a crista máxima com a posição mais baixa da plataforma. Em relação aos exercícios, o braço de vento vai até o centro de resistência lateral de cada plano, e a força de heave inclui a defasagem da onda entre os dois pontoons. Uma avaliação leva cerca de 6 milissegundos, o que permite testar dezenas de milhares de cascos. A tabela mostra o domínio; o mínimo de Lp vem da área de convés.

**Números-chave:** 6 variáveis: Lp, bp, hp, bc, hc, T · Uma avaliação ≈ 6 ms · Domínio na tabela à direita

**Deixa visual:** Percorrer o desenho: planta, depois vista lateral (pontoon, colunas, deck box, módulos).

**Transição:** Antes de otimizar, validamos o modelo.

## 4. Validação: plataforma dos Exercícios 7 a 10 · Felipe · 3:00–4:00

Rodamos o modelo na plataforma dos exercícios. O período natural de 20,70 s e o Hs de heave de 2,98 m batem com a aula; o KG fica a 0,6%, e o A/B fica até 3,7% abaixo, do lado conservador. Também conferimos a coerência interna: a inclinação da GZ na origem é igual ao GM nos dois planos, o RAO tende a 1 em baixa frequência e a soma dos pesos fecha com o deslocamento. Mais adiante, o João mostra a validação com semissubmersíveis reais do pôster de 2011.

**Números-chave:** Tn 20,70 s e Hs de heave 2,98 m: iguais à aula · KG +0,6%; A/B até −3,7% · dGZ/dφ(0) = GM; RAO(ω→0) = 1

**Deixa visual:** Apontar a coluna 'Erro' da tabela e os dois cartões.

**Transição:** Com o modelo validado, partimos para a otimização.

## 5. Procedimento de variação sistemática · Felipe · 4:00–5:00

A otimização tem quatro etapas. Primeiro, 20.000 cascos amostrados por hipercubo latino: só 547 atendem às restrições sem o vento, e só 227, 1,1%, passam também no critério de áreas. Depois, a soma ponderada do enunciado, com SLSQP, variando w1 de 0 a 1 em passos de 0,05. Como a fronteira não é convexa, a soma ponderada para em ótimos locais em alguns pesos, então complementamos com o método épsilon-restrito: minimizar o peso com o heave limitado a épsilon. Por fim, filtramos os não dominados entre as 260 soluções viáveis. A rodada completa leva cerca de 4 minutos. Agora o Gustavo mostra o que essa busca encontrou.

**Números-chave:** 20.000 amostras → 547 → 227 viáveis (1,1%) · Soma ponderada: w1 de 0 a 1, passo 0,05 · ε-restrito em 12 níveis · 260 viáveis → 25 na fronteira

**Deixa visual:** Percorrer os quatro cartões da esquerda para a direita.

**Transição:** Passar a palavra: "Gustavo, com você."

## 6. Conjunto viável e fronteira de Pareto · Gustavo · 5:00–6:15

Obrigado, Felipe. Este é o plano peso estrutural por Hs de heave. Os pontos cinza são inviáveis, os laranja-claros só falham no critério de vento e os azuis são os viáveis do hipercubo. A linha laranja é a fronteira de Pareto, com 25 pontos, de 10.346 t e 2,37 m de heave até 23.634 t e 1,04 m. Nenhuma amostra aleatória ficou na fronteira: o otimizador encontrou um casco 14,9% mais leve que a melhor delas. O resultado mais importante está à direita: nos 25 pontos, o GM transversal está no máximo de 4 m e o A/B no mínimo de 1,30. O projeto é governado pela estabilidade; air gap e período natural sempre têm folga. É o conflito descrito no enunciado: o GM não pode subir, então a área A só cresce adiando o alagamento, com colunas mais altas e mais peso.

**Números-chave:** Fronteira: 10.346 t (2,37 m) a 23.634 t (1,04 m) · GM_T = 4 m e A/B = 1,30 ativos nos 25 pontos · Otimizador 14,9% mais leve que a melhor amostra

**Deixa visual:** Apontar a legenda, depois os três marcadores grandes (vermelho, laranja, verde).

**Transição:** Vamos ver os três cenários pedidos.

## 7. Ficha técnica comparativa dos três cenários · Gustavo · 6:15–7:35

O cenário 1, de mínimo peso, é uma semi rasa: calado de 12 m e colunas de 8 m por 20 m, no limite mínimo. É o mais leve, com 10.346 t, mas tem heave de 42% do Hs e ângulo de alagamento de só 9 graus. O cenário 2, de mínimo heave, vai ao outro extremo: calado de 40 m e colunas de 50 m, no limite máximo, com heave de 1,04 m, mas um casco 2,3 vezes mais pesado. É o único com lastro real, 18 mil toneladas. Os dois extremos encostam nos limites do domínio, então dependem dos limites que adotamos. O cenário 3, a nossa escolha, é o único com todas as variáveis no interior do domínio. Nos três, GM e A/B são as restrições ativas.

**Números-chave:** Cen. 1: 10.346 t, 2,37 m, φal = 9° · Cen. 2: 23.634 t, 1,04 m, lastro 18.081 t · Cen. 3: 14.998 t, 1,55 m, nenhuma variável no limite

**Deixa visual:** Apontar as linhas destacadas (peso e H1/3) e a última linha (variáveis no limite).

**Transição:** Agora o detalhe da solução escolhida.

## 8. Solução final: dimensões, pesos e centros · Gustavo · 7:35–8:35

A solução escolhida tem Lp de 111,8 m, pontoons de 13,4 por 10,2 m, colunas de 12,6 m de lado e 39,6 m de altura, e calado de 24 m. A área de convés fica 8% acima da mínima. O casco pesa 14.998 t, e o deslocamento é de 40.247 t. O KG é alto, 42,8 m, porque as 22.420 t de topside ficam no topo; o GM de 4 m vem do raio metacêntrico de 39 m, dado pelo afastamento das colunas. O ponto fraco é o lastro: são só 11 t, que são uma margem numérica. O João volta a isso na sensibilidade.

**Números-chave:** Lp 111,8 · T 24,0 · hc 39,6 m · Casco 14.998 t · Δ 40.247 t · KG 42,8 m · GM_T 4,00 m · Lastro 11 t (margem numérica)

**Deixa visual:** Apontar a tabela de pesos (planta e topside) e o cartão do peso do casco.

**Transição:** E a estabilidade, que é o que governa o projeto.

## 9. Solução final: estabilidade intacta · Gustavo · 8:35–10:00

Nos dois planos, a curva GZ está em azul-escuro, o braço de vento de tempestade em laranja e o de operação em azul. A linha pontilhada é o ângulo de alagamento: 21,6 graus no plano transversal e 23,9 no longitudinal; a área A vai de zero até ele. Na tabela, o caso crítico é a tempestade no plano transversal, com A/B de 1,303; o longitudinal fica quase igual, 1,304. Nos quatro casos, phi 2 vem depois do alagamento e a GZ é positiva até ele, então o critério é atendido. O transversal é mais crítico porque a silhueta dos pontoons baixa o centro de resistência lateral e alonga o braço. A maior parcela do momento é a face inferior do convés, 3,2 vezes as outras somadas. Sob tempestade a plataforma inclina 14 graus, valor a verificar numa fase seguinte. Passo para o João.

**Números-chave:** φal: 21,6° (transv.) e 23,9° (long.) · A/B: 1,303 (crítico) e 1,304 · HM_ud = 3,2 × HM_0 · Inclinação de 14° sob tempestade

**Deixa visual:** Apontar a linha pontilhada de φal, a área sombreada e a primeira linha da tabela.

**Transição:** Passar a palavra: "João, com você."

## 10. Solução final: heave e air gap · João · 10:00–11:10

Obrigado, Gustavo. À esquerda, o RAO de heave; à direita, o espectro do mar e o espectro de resposta. O período natural é 21,85 s, 9% acima do limite de 20 s. O pico do RAO fica em 1,47 porque a força de excitação se anula em 0,314 radiano por segundo, logo acima da frequência natural de 0,288: as forças nas colunas e nos pontoons se cancelam e cortam a ressonância. No pico do mar, em 0,413, o RAO é só 0,32. Por isso o espectro de resposta tem um pico pequeno na ressonância e o principal no pico da onda. O Hs de heave é 1,55 m, 28% do Hs do mar. O air gap tem 19 m de folga: quem define a altura das colunas é o critério de vento, e não a crista da onda.

**Números-chave:** Tn = 21,85 s · RAO máx. 1,47; no pico do mar 0,32 · Cancelamento em 0,314 rad/s · H1/3 = 1,55 m; folga de air gap 19,2 m

**Deixa visual:** Apontar no RAO as duas linhas verticais próximas (ωn e F3 = 0).

**Transição:** Por que escolhemos este ponto da fronteira?

## 11. Por que a solução intermediária · João · 11:10–12:10

O gráfico mostra o custo marginal ao longo da fronteira. Do cenário 1 até a solução escolhida, cada milímetro de redução no heave custa 5,7 t de casco. Daí até o cenário 2, custa 17 t, três vezes mais. A solução fica no joelho da fronteira. Além disso, é a única com todas as variáveis no interior do domínio, então não depende dos limites adotados, e tem ângulo de alagamento de 21,6 graus, contra 9 graus do cenário de mínimo peso.

**Números-chave:** 1 → 3: 5,7 t por mm · 3 → 2: 17,0 t por mm (3×) · Única no interior do domínio

**Deixa visual:** Apontar as duas retas tracejadas do gráfico.

**Transição:** Comparamos esse resultado com plataformas reais.

## 12. Comparativo com plataformas reais · João · 12:10–13:15

Usamos o pôster de semissubmersíveis de 2011, a referência 6 do enunciado. Aplicado a três semis reais de dois pontoons e quatro colunas, Veslefrikk B, Njord A e P-20, o modelo calcula o deslocamento com erro de até 10%. No gráfico, as dimensões da solução estão dentro da faixa da frota, e a altura das colunas coincide com a mediana. O topside por mil barris, 141 t, também bate com a mediana do pôster, 145 t. O deslocamento por mil barris é o menor da frota, e a causa é a falta de lastro: com 10% de lastro ele iguala o da Troll C. Na região, os análogos reais, o FPSO do CLOV e a Moho/Bilondo, têm casco de navio porque armazenam o óleo; uma semi exigiria um FSO ou um oleoduto de 190 km.

**Números-chave:** Δ de 3 semis reais com erro ≤ 10% · Topside: 141 t/mil bopd (mediana 145 t) · CLOV: 160 mil bpd, 1.291 m, FPSO

**Deixa visual:** Apontar os losangos laranja no painel (a) e as barras laranja nos painéis (b) e (c).

**Transição:** Por fim, a sensibilidade às hipóteses.

## 13. Sensibilidade às hipóteses · João · 13:15–14:00

Reotimizamos tudo para as hipóteses mais incertas. Com módulos de 15 m de altura, o casco fica 5% mais pesado; com lastro mínimo de 10%, 7%; com o mesmo heave. A hipótese de maior impacto é incluir o gás no BOE: mais 25% no casco, e ela precisa ser confirmada. Com a geometria fixa, mudar a altura do deck box ou dos módulos torna a solução inviável, porque ela está exatamente no limite de GM e de A/B.

**Números-chave:** hm = 15 m: +5,3% · Lastro ≥ 10%: +6,9% · Gás no BOE: +24,8%

**Deixa visual:** Apontar a linha do gás na tabela.

**Transição:** Fechando.

## 14. Conclusões e próximos passos · João · 14:00–14:30

Em resumo: o modelo cobre os oito itens do enunciado e está validado contra a aula e contra semis reais. O projeto é governado pela estabilidade. A solução escolhida tem 14.998 t de casco, 1,55 m de heave e 21,8 s de período natural, no joelho da fronteira. Os próximos passos são confirmar o gás, fundamentar a altura dos módulos, adotar lastro mínimo e comparar com um FPSO incluindo o armazenamento. Obrigado.

**Números-chave:** 14.998 t · 1,55 m · 21,8 s · A/B 1,303 · GM_T 4,00 m

**Deixa visual:** Apontar os quatro cartões à direita.

**Transição:** Abrir para perguntas.

## 15. Obrigado · João · perguntas

Obrigado pela atenção. Ficamos à disposição para perguntas.

**Deixa visual:** Todos à frente; quem responde segue a divisão abaixo.

## Perguntas prováveis

| Pergunta | Quem responde | Resposta curta |
|---|---|---|
| Por que o GM fica no máximo de 4 m em todas as soluções? | Felipe | Porque o A/B ≥ 1,3 exige área sob a GZ. Subir o GM é o jeito mais barato de aumentar a GZ; o limite de 4 m impede ir além, e daí a área extra só vem de colunas mais altas. |
| Por que o A/B longitudinal ficou 3,7% abaixo da aula? | Felipe | Diferenças de hipótese no vento (hd e braço até o z_CLR). O desvio é do lado conservador. |
| Por que a solução escolhida não tem lastro? | Gustavo | O enunciado só exige lastro positivo, e o lastro não reduz o peso do casco. Com lastro mínimo de 10% o casco sobe 6,9%, com o mesmo heave; recomendamos essa variante para a fase seguinte. |
| Os extremos da fronteira estão nos limites. Isso não invalida a fronteira? | Gustavo | Os extremos dependem dos limites adotados, mas a solução escolhida tem todas as variáveis no interior do domínio, então não depende deles. |
| Por que usar o ε-restrito além da soma ponderada? | Gustavo | A fronteira não é convexa: 7 dos 21 pesos levaram a ótimos dominados. O ε-restrito alcança esses trechos. |
| A inclinação de 14° sob tempestade é aceitável? | Gustavo | O critério da DNV/MODU é atendido, mas o valor é alto; deixamos como verificação para a próxima fase. |
| Por que γ = 3,3 no JONSWAP? | João | É o valor da disciplina. Com γ = 1 (Pierson-Moskowitz) o Hs de heave seria 1,45 m em vez de 1,55 m. |
| Por que o air gap tem tanta folga? | João | O mar é brando (crista máxima de 5,2 m). A altura das colunas é definida pelo ângulo de alagamento exigido pelo critério de vento. |
| Se a região usa FPSO, por que uma semi? | João | O enunciado define o conceito. Na região o FPSO é usado porque armazena o óleo; uma semi exigiria FSO ou oleoduto de 190 km, custo fora do escopo. |
| E se o gás entrar no BOE? | João | O pico vai a 202,9 mil boe/d, a planta a 16.838 t e o casco da solução escolhida a 18.718 t (+24,8%). |
