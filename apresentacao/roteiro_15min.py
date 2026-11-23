# -*- coding: utf-8 -*-
"""
Roteiro da apresentação de 15 minutos para os três membros do Grupo 02.

aplicar(pptx): grava em cada slide
  * as notas do apresentador (fala completa, tempo, números-chave, deixa visual
    e transição);
  * um comentário do PowerPoint, com o membro que apresenta como autor.
exportar_md(md): grava o mesmo roteiro em Markdown, para ensaio.

É chamado por gerar_apresentacoes.py; também pode rodar sozinho:
    python apresentacao/roteiro_15min.py
"""
import os
from datetime import datetime
from xml.sax.saxutils import escape

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI

AQUI = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(AQUI, "PNV3425_G02_apresentacao_15min.pptx")
MD = os.path.join(AQUI, "roteiro_apresentacao_15min.md")

MEMBROS = {
    "Felipe": dict(nome="Felipe Perpétuo Simões", iniciais="FPS",
                   bloco="Abertura, campo, modelo, validação e otimização"),
    "Gustavo": dict(nome="Gustavo Guilherme Silva", iniciais="GGS",
                    bloco="Fronteira de Pareto, cenários e solução final (pesos e estabilidade)"),
    "João": dict(nome="João Marcos Magalhães Moura", iniciais="JMM",
                 bloco="Heave, escolha, plataformas reais, sensibilidade e conclusões"),
}

# (título esperado no slide, quem, duração [s], fala, números-chave, deixa visual, transição)
ROTEIRO = [
    ("Projeto paramétrico de uma semissubmersível", "Felipe", 40,
     "Bom dia. Somos o Grupo 02: eu sou o Felipe, e comigo estão o Gustavo e o João. Nosso trabalho é o "
     "projeto paramétrico da semissubmersível de produção do bloco KZ-2026-B, na bacia do Baixo Congo, em "
     "Angola. O objetivo é encontrar o casco de menor peso estrutural e de menor movimento de heave que atenda "
     "a todas as restrições do enunciado. Eu apresento o campo, o modelo e a validação; o Gustavo apresenta a "
     "fronteira de Pareto e a solução escolhida; e o João fecha com o heave, o comparativo com plataformas "
     "reais e as conclusões.",
     ["Bloco KZ-2026-B, Baixo Congo, 1.450 m", "Dois objetivos: peso do casco e Hs de heave"],
     "Olhar para a banca; apontar os colegas ao citar os blocos.",
     "Começo pelo campo."),
    ("O campo KZ-2026-B", "Felipe", 60,
     "O campo fica a 190 km da costa, em 1.450 m de lâmina d'água. São 2,2 bilhões de barris de óleo "
     "original, com fator de recuperação de 30%, ou seja, 660 milhões de barris recuperáveis, além de 30 "
     "bilhões de metros cúbicos de gás. A curva de produção tem pico de 158.894 barris por dia entre os anos 5 "
     "e 7, e é esse pico que dimensiona a planta. Pela correlação da aula, isso dá uma área mínima de convés de "
     "11.563 metros quadrados, ou seja, Lp de pelo menos 107,5 m, e uma planta de 13.188 t. O mar de 100 anos é "
     "brando: Hs de 5,6 m e Tp de 15,2 s, menos da metade do Hs dos exercícios. No caso-base usamos só o óleo; "
     "o caso com gás aparece na sensibilidade.",
     ["Pico: 158.894 bpd", "Área mínima: 11.563 m² (Lp ≥ 107,5 m)", "Planta: 13.188 t",
      "Hs = 5,6 m, Tp = 15,2 s"],
     "Apontar os três cartões à direita, de cima para baixo.",
     "Com esses dados de entrada, montamos o modelo."),
    ("Modelo paramétrico: geometria e variáveis", "Felipe", 80,
     "As variáveis de projeto são o lado da planta Lp, a largura e a altura dos pontoons, o lado e a altura "
     "das colunas e o calado. Para cada combinação, o modelo encadeia os Exercícios 7 a 10: hidrostática; "
     "pesos, KG e GM; curva GZ por projeções 2D nos dois planos e critério de áreas para os ventos de 51,5 e "
     "36 m/s; heave, com forças de Froude-Krylov e de massa adicional, RAO e espectro de resposta no mar de 100 "
     "anos; e por fim o air gap mínimo, que soma a crista máxima com a posição mais baixa da plataforma. Em "
     "relação aos exercícios, o braço de vento vai até o centro de resistência lateral de cada plano, e a força "
     "de heave inclui a defasagem da onda entre os dois pontoons. Uma avaliação leva cerca de 6 milissegundos, "
     "o que permite testar dezenas de milhares de cascos. A tabela mostra o domínio; o mínimo de Lp vem da área "
     "de convés.",
     ["6 variáveis: Lp, bp, hp, bc, hc, T", "Uma avaliação ≈ 6 ms", "Domínio na tabela à direita"],
     "Percorrer o desenho: planta, depois vista lateral (pontoon, colunas, deck box, módulos).",
     "Antes de otimizar, validamos o modelo."),
    ("Validação: plataforma dos Exercícios 7 a 10", "Felipe", 60,
     "Rodamos o modelo na plataforma dos exercícios. O período natural de 20,70 s e o Hs de heave de 2,98 m "
     "batem com a aula; o KG fica a 0,6%, e o A/B fica até 3,7% abaixo, do lado conservador. Também conferimos "
     "a coerência interna: a inclinação da GZ na origem é igual ao GM nos dois planos, o RAO tende a 1 em baixa "
     "frequência e a soma dos pesos fecha com o deslocamento. Mais adiante, o João mostra a validação com "
     "semissubmersíveis reais do pôster de 2011.",
     ["Tn 20,70 s e Hs de heave 2,98 m: iguais à aula", "KG +0,6%; A/B até −3,7%",
      "dGZ/dφ(0) = GM; RAO(ω→0) = 1"],
     "Apontar a coluna 'Erro' da tabela e os dois cartões.",
     "Com o modelo validado, partimos para a otimização."),
    ("Procedimento de variação sistemática", "Felipe", 60,
     "A otimização tem quatro etapas. Primeiro, 20.000 cascos amostrados por hipercubo latino: só 547 atendem "
     "às restrições sem o vento, e só 227, 1,1%, passam também no critério de áreas. Depois, a soma ponderada do "
     "enunciado, com SLSQP, variando w1 de 0 a 1 em passos de 0,05. Como a fronteira não é convexa, a soma "
     "ponderada para em ótimos locais em alguns pesos, então complementamos com o método épsilon-restrito: "
     "minimizar o peso com o heave limitado a épsilon. Por fim, filtramos os não dominados entre as 260 "
     "soluções viáveis. A rodada completa leva cerca de 4 minutos. Agora o Gustavo mostra o que essa busca "
     "encontrou.",
     ["20.000 amostras → 547 → 227 viáveis (1,1%)", "Soma ponderada: w1 de 0 a 1, passo 0,05",
      "ε-restrito em 12 níveis", "260 viáveis → 25 na fronteira"],
     "Percorrer os quatro cartões da esquerda para a direita.",
     "Passar a palavra: \"Gustavo, com você.\""),
    ("Conjunto viável e fronteira de Pareto", "Gustavo", 75,
     "Obrigado, Felipe. Este é o plano peso estrutural por Hs de heave. Os pontos cinza são inviáveis, os "
     "laranja-claros só falham no critério de vento e os azuis são os viáveis do hipercubo. A linha laranja é a "
     "fronteira de Pareto, com 25 pontos, de 10.346 t e 2,37 m de heave até 23.634 t e 1,04 m. Nenhuma amostra "
     "aleatória ficou na fronteira: o otimizador encontrou um casco 14,9% mais leve que a melhor delas. O "
     "resultado mais importante está à direita: nos 25 pontos, o GM transversal está no máximo de 4 m e o A/B "
     "no mínimo de 1,30. O projeto é governado pela estabilidade; air gap e período natural sempre têm folga. É "
     "o conflito descrito no enunciado: o GM não pode subir, então a área A só cresce adiando o alagamento, com "
     "colunas mais altas e mais peso.",
     ["Fronteira: 10.346 t (2,37 m) a 23.634 t (1,04 m)", "GM_T = 4 m e A/B = 1,30 ativos nos 25 pontos",
      "Otimizador 14,9% mais leve que a melhor amostra"],
     "Apontar a legenda, depois os três marcadores grandes (vermelho, laranja, verde).",
     "Vamos ver os três cenários pedidos."),
    ("Ficha técnica comparativa dos três cenários", "Gustavo", 80,
     "O cenário 1, de mínimo peso, é uma semi rasa: calado de 12 m e colunas de 8 m por 20 m, no limite mínimo. "
     "É o mais leve, com 10.346 t, mas tem heave de 42% do Hs e ângulo de alagamento de só 9 graus. O cenário 2, "
     "de mínimo heave, vai ao outro extremo: calado de 40 m e colunas de 50 m, no limite máximo, com heave de "
     "1,04 m, mas um casco 2,3 vezes mais pesado. É o único com lastro real, 18 mil toneladas. Os dois extremos "
     "encostam nos limites do domínio, então dependem dos limites que adotamos. O cenário 3, a nossa escolha, é "
     "o único com todas as variáveis no interior do domínio. Nos três, GM e A/B são as restrições ativas.",
     ["Cen. 1: 10.346 t, 2,37 m, φal = 9°", "Cen. 2: 23.634 t, 1,04 m, lastro 18.081 t",
      "Cen. 3: 14.998 t, 1,55 m, nenhuma variável no limite"],
     "Apontar as linhas destacadas (peso e H1/3) e a última linha (variáveis no limite).",
     "Agora o detalhe da solução escolhida."),
    ("Solução final: dimensões, pesos e centros", "Gustavo", 60,
     "A solução escolhida tem Lp de 111,8 m, pontoons de 13,4 por 10,2 m, colunas de 12,6 m de lado e 39,6 m de "
     "altura, e calado de 24 m. A área de convés fica 8% acima da mínima. O casco pesa 14.998 t, e o "
     "deslocamento é de 40.247 t. O KG é alto, 42,8 m, porque as 22.420 t de topside ficam no topo; o GM de 4 m "
     "vem do raio metacêntrico de 39 m, dado pelo afastamento das colunas. O ponto fraco é o lastro: são só 11 t, "
     "que são uma margem numérica. O João volta a isso na sensibilidade.",
     ["Lp 111,8 · T 24,0 · hc 39,6 m", "Casco 14.998 t · Δ 40.247 t", "KG 42,8 m · GM_T 4,00 m",
      "Lastro 11 t (margem numérica)"],
     "Apontar a tabela de pesos (planta e topside) e o cartão do peso do casco.",
     "E a estabilidade, que é o que governa o projeto."),
    ("Solução final: estabilidade intacta", "Gustavo", 85,
     "Nos dois planos, a curva GZ está em azul-escuro, o braço de vento de tempestade em laranja e o de "
     "operação em azul. A linha pontilhada é o ângulo de alagamento: 21,6 graus no plano transversal e 23,9 no "
     "longitudinal; a área A vai de zero até ele. Na tabela, o caso crítico é a tempestade no plano "
     "transversal, com A/B de 1,303; o longitudinal fica quase igual, 1,304. Nos quatro casos, phi 2 vem depois "
     "do alagamento e a GZ é positiva até ele, então o critério é atendido. O transversal é mais crítico porque "
     "a silhueta dos pontoons baixa o centro de resistência lateral e alonga o braço. A maior parcela do "
     "momento é a face inferior do convés, 3,2 vezes as outras somadas. Sob tempestade a plataforma inclina "
     "14 graus, valor a verificar numa fase seguinte. Passo para o João.",
     ["φal: 21,6° (transv.) e 23,9° (long.)", "A/B: 1,303 (crítico) e 1,304", "HM_ud = 3,2 × HM_0",
      "Inclinação de 14° sob tempestade"],
     "Apontar a linha pontilhada de φal, a área sombreada e a primeira linha da tabela.",
     "Passar a palavra: \"João, com você.\""),
    ("Solução final: heave e air gap", "João", 70,
     "Obrigado, Gustavo. À esquerda, o RAO de heave; à direita, o espectro do mar e o espectro de resposta. O "
     "período natural é 21,85 s, 9% acima do limite de 20 s. O pico do RAO fica em 1,47 porque a força de "
     "excitação se anula em 0,314 radiano por segundo, logo acima da frequência natural de 0,288: as forças nas "
     "colunas e nos pontoons se cancelam e cortam a ressonância. No pico do mar, em 0,413, o RAO é só 0,32. Por "
     "isso o espectro de resposta tem um pico pequeno na ressonância e o principal no pico da onda. O Hs de "
     "heave é 1,55 m, 28% do Hs do mar. O air gap tem 19 m de folga: quem define a altura das colunas é o "
     "critério de vento, e não a crista da onda.",
     ["Tn = 21,85 s", "RAO máx. 1,47; no pico do mar 0,32", "Cancelamento em 0,314 rad/s",
      "H1/3 = 1,55 m; folga de air gap 19,2 m"],
     "Apontar no RAO as duas linhas verticais próximas (ωn e F3 = 0).",
     "Por que escolhemos este ponto da fronteira?"),
    ("Por que a solução intermediária", "João", 60,
     "O gráfico mostra o custo marginal ao longo da fronteira. Do cenário 1 até a solução escolhida, cada "
     "milímetro de redução no heave custa 5,7 t de casco. Daí até o cenário 2, custa 17 t, três vezes mais. A "
     "solução fica no joelho da fronteira. Além disso, é a única com todas as variáveis no interior do domínio, "
     "então não depende dos limites adotados, e tem ângulo de alagamento de 21,6 graus, contra 9 graus do "
     "cenário de mínimo peso.",
     ["1 → 3: 5,7 t por mm", "3 → 2: 17,0 t por mm (3×)", "Única no interior do domínio"],
     "Apontar as duas retas tracejadas do gráfico.",
     "Comparamos esse resultado com plataformas reais."),
    ("Comparativo com plataformas reais", "João", 65,
     "Usamos o pôster de semissubmersíveis de 2011, a referência 6 do enunciado. Aplicado a três semis reais de "
     "dois pontoons e quatro colunas, Veslefrikk B, Njord A e P-20, o modelo calcula o deslocamento com erro de "
     "até 10%. No gráfico, as dimensões da solução estão dentro da faixa da frota, e a altura das colunas "
     "coincide com a mediana. O topside por mil barris, 141 t, também bate com a mediana do pôster, 145 t. O "
     "deslocamento por mil barris é o menor da frota, e a causa é a falta de lastro: com 10% de lastro ele "
     "iguala o da Troll C. Na região, os análogos reais, o FPSO do CLOV e a Moho/Bilondo, têm casco de navio "
     "porque armazenam o óleo; uma semi exigiria um FSO ou um oleoduto de 190 km.",
     ["Δ de 3 semis reais com erro ≤ 10%", "Topside: 141 t/mil bopd (mediana 145 t)",
      "CLOV: 160 mil bpd, 1.291 m, FPSO"],
     "Apontar os losangos laranja no painel (a) e as barras laranja nos painéis (b) e (c).",
     "Por fim, a sensibilidade às hipóteses."),
    ("Sensibilidade às hipóteses", "João", 45,
     "Reotimizamos tudo para as hipóteses mais incertas. Com módulos de 15 m de altura, o casco fica 5% mais "
     "pesado; com lastro mínimo de 10%, 7%; com o mesmo heave. A hipótese de maior impacto é incluir o gás no "
     "BOE: mais 25% no casco, e ela precisa ser confirmada. Com a geometria fixa, mudar a altura do deck box ou "
     "dos módulos torna a solução inviável, porque ela está exatamente no limite de GM e de A/B.",
     ["hm = 15 m: +5,3%", "Lastro ≥ 10%: +6,9%", "Gás no BOE: +24,8%"],
     "Apontar a linha do gás na tabela.",
     "Fechando."),
    ("Conclusões e próximos passos", "João", 30,
     "Em resumo: o modelo cobre os oito itens do enunciado e está validado contra a aula e contra semis reais. "
     "O projeto é governado pela estabilidade. A solução escolhida tem 14.998 t de casco, 1,55 m de heave e "
     "21,8 s de período natural, no joelho da fronteira. Os próximos passos são confirmar o gás, fundamentar a "
     "altura dos módulos, adotar lastro mínimo e comparar com um FPSO incluindo o armazenamento. Obrigado.",
     ["14.998 t · 1,55 m · 21,8 s", "A/B 1,303 · GM_T 4,00 m"],
     "Apontar os quatro cartões à direita.",
     "Abrir para perguntas."),
    ("Obrigado", "João", 0,
     "Obrigado pela atenção. Ficamos à disposição para perguntas.",
     [], "Todos à frente; quem responde segue a divisão abaixo.", ""),
]

# Perguntas prováveis: (pergunta, quem responde, resposta curta)
PERGUNTAS = [
    ("Por que o GM fica no máximo de 4 m em todas as soluções?", "Felipe",
     "Porque o A/B ≥ 1,3 exige área sob a GZ. Subir o GM é o jeito mais barato de aumentar a GZ; o limite de "
     "4 m impede ir além, e daí a área extra só vem de colunas mais altas."),
    ("Por que o A/B longitudinal ficou 3,7% abaixo da aula?", "Felipe",
     "Diferenças de hipótese no vento (hd e braço até o z_CLR). O desvio é do lado conservador."),
    ("Por que a solução escolhida não tem lastro?", "Gustavo",
     "O enunciado só exige lastro positivo, e o lastro não reduz o peso do casco. Com lastro mínimo de 10% o "
     "casco sobe 6,9%, com o mesmo heave; recomendamos essa variante para a fase seguinte."),
    ("Os extremos da fronteira estão nos limites. Isso não invalida a fronteira?", "Gustavo",
     "Os extremos dependem dos limites adotados, mas a solução escolhida tem todas as variáveis no interior "
     "do domínio, então não depende deles."),
    ("Por que usar o ε-restrito além da soma ponderada?", "Gustavo",
     "A fronteira não é convexa: 7 dos 21 pesos levaram a ótimos dominados. O ε-restrito alcança esses trechos."),
    ("A inclinação de 14° sob tempestade é aceitável?", "Gustavo",
     "O critério da DNV/MODU é atendido, mas o valor é alto; deixamos como verificação para a próxima fase."),
    ("Por que γ = 3,3 no JONSWAP?", "João",
     "É o valor da disciplina. Com γ = 1 (Pierson-Moskowitz) o Hs de heave seria 1,45 m em vez de 1,55 m."),
    ("Por que o air gap tem tanta folga?", "João",
     "O mar é brando (crista máxima de 5,2 m). A altura das colunas é definida pelo ângulo de alagamento "
     "exigido pelo critério de vento."),
    ("Se a região usa FPSO, por que uma semi?", "João",
     "O enunciado define o conceito. Na região o FPSO é usado porque armazena o óleo; uma semi exigiria FSO "
     "ou oleoduto de 190 km, custo fora do escopo."),
    ("E se o gás entrar no BOE?", "João",
     "O pico vai a 202,9 mil boe/d, a planta a 16.838 t e o casco da solução escolhida a 18.718 t (+24,8%)."),
]


def _mmss(s):
    return f"{s // 60}:{s % 60:02d}"


def _tempos():
    t, out = 0, []
    for item in ROTEIRO:
        out.append((t, t + item[2]))
        t += item[2]
    return out


def _texto_notas(i, item, ini, fim):
    titulo, quem, dur, fala, chaves, deixa, trans = item
    linhas = [f"ROTEIRO · slide {i + 1} de {len(ROTEIRO)} · {MEMBROS[quem]['nome'].upper()}",
              f"Tempo: {_mmss(ini)} a {_mmss(fim)} ({_mmss(dur)})" if dur else "Perguntas", "",
              "FALA", fala, ""]
    if chaves:
        linhas += ["NÚMEROS-CHAVE"] + [f"• {c}" for c in chaves] + [""]
    if deixa:
        linhas += ["DEIXA VISUAL", deixa, ""]
    if trans:
        linhas += ["TRANSIÇÃO", trans]
    if i == 0:
        linhas += ["", "DIVISÃO DA APRESENTAÇÃO"]
        for k, v in MEMBROS.items():
            sl = [j + 1 for j, it in enumerate(ROTEIRO) if it[1] == k and it[2]]
            dur_m = sum(it[2] for it in ROTEIRO if it[1] == k)
            linhas.append(f"• {v['nome']}: slides {sl[0]}–{sl[-1]} ({_mmss(dur_m)}) · {v['bloco']}")
    if i == len(ROTEIRO) - 1:
        linhas += ["", "PERGUNTAS PROVÁVEIS E QUEM RESPONDE"]
        for q, k, r in PERGUNTAS:
            linhas += [f"• [{k}] {q}", f"  {r}"]
    return "\n".join(linhas)


def _texto_comentario(i, item, ini, fim):
    titulo, quem, dur, fala, chaves, deixa, trans = item
    if not dur:
        return ("Perguntas: Felipe responde sobre modelo, estabilidade e validação; Gustavo sobre otimização, "
                "restrições e escolha; João sobre heave, air gap, plataformas reais e sensibilidade.")
    prox = ROTEIRO[i + 1][1] if i + 1 < len(ROTEIRO) else None
    txt = f"{quem} · {_mmss(ini)}–{_mmss(fim)} · " + "; ".join(chaves[:3]) + "."
    if prox and prox != quem and ROTEIRO[i + 1][2]:
        txt += f" No fim, passar a palavra para {prox}."
    return txt


def _titulo_slide(slide):
    return " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)


def aplicar(caminho=PPTX):
    prs = Presentation(caminho)
    slides = list(prs.slides)
    assert len(slides) == len(ROTEIRO), f"{len(slides)} slides, roteiro com {len(ROTEIRO)}"
    for s, item in zip(slides, ROTEIRO):
        assert item[0] in _titulo_slide(s), f"slide sem o título esperado: {item[0]}"
    tempos = _tempos()
    pkg = prs.part.package
    autores = list(MEMBROS)
    cont = {k: 0 for k in autores}
    agora = datetime(2026, 11, 24, 18, 0).strftime("%Y-%m-%dT%H:%M:%S.000")

    for i, (s, item) in enumerate(zip(slides, ROTEIRO)):
        ini, fim = tempos[i]
        s.notes_slide.notes_text_frame.text = _texto_notas(i, item, ini, fim)
        quem = item[1]
        cont[quem] += 1
        xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
               '<p:cmLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
               'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
               f'<p:cm authorId="{autores.index(quem)}" dt="{agora}" idx="{cont[quem]}">'
               '<p:pos x="10" y="10"/>'
               f'<p:text>{escape(_texto_comentario(i, item, ini, fim))}</p:text></p:cm></p:cmLst>')
        part = Part(PackURI(f"/ppt/comments/comment{i + 1}.xml"),
                    "application/vnd.openxmlformats-officedocument.presentationml.comments+xml",
                    pkg, xml.encode("utf-8"))
        s.part.relate_to(part, RT.COMMENTS)

    aut = "".join(f'<p:cmAuthor id="{j}" name="{escape(MEMBROS[k]["nome"])}" '
                  f'initials="{MEMBROS[k]["iniciais"]}" lastIdx="{cont[k]}" clrIdx="{j}"/>'
                  for j, k in enumerate(autores))
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<p:cmAuthorLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
           f'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">{aut}</p:cmAuthorLst>')
    part = Part(PackURI("/ppt/commentAuthors.xml"),
                "application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml",
                pkg, xml.encode("utf-8"))
    prs.part.relate_to(part, RT.COMMENT_AUTHORS)
    prs.save(caminho)
    print(f"Roteiro aplicado em {caminho}")


def exportar_md(caminho=MD):
    tempos = _tempos()
    L = ["# Roteiro da apresentação de 15 minutos · Grupo 02", "",
         "PNV3425 – Projeto de Sistemas Oceânicos · arquivo `PNV3425_G02_apresentacao_15min.pptx`. "
         "O mesmo texto está nas notas do apresentador de cada slide.", "",
         "## Divisão", "", "| Membro | Slides | Tempo | Bloco |", "|---|---|---|---|"]
    for k, v in MEMBROS.items():
        sl = [j + 1 for j, it in enumerate(ROTEIRO) if it[1] == k and it[2]]
        dur = sum(it[2] for it in ROTEIRO if it[1] == k)
        L.append(f"| {v['nome']} | {sl[0]}–{sl[-1]} | {_mmss(dur)} | {v['bloco']} |")
    L += ["", f"Tempo total de fala: {_mmss(tempos[-1][1])} (folga de {_mmss(900 - tempos[-1][1])} até 15:00).", ""]
    for i, item in enumerate(ROTEIRO):
        titulo, quem, dur, fala, chaves, deixa, trans = item
        ini, fim = tempos[i]
        cab = f"## {i + 1}. {titulo} · {quem}"
        cab += f" · {_mmss(ini)}–{_mmss(fim)}" if dur else " · perguntas"
        L += [cab, "", fala, ""]
        if chaves:
            L += ["**Números-chave:** " + " · ".join(chaves), ""]
        if deixa:
            L += [f"**Deixa visual:** {deixa}", ""]
        if trans:
            L += [f"**Transição:** {trans}", ""]
    L += ["## Perguntas prováveis", "", "| Pergunta | Quem responde | Resposta curta |", "|---|---|---|"]
    for q, k, r in PERGUNTAS:
        L.append(f"| {q} | {k} | {r} |")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Roteiro em Markdown: {caminho}")


def conferir_ritmo(palavras_por_min=140):
    """Compara o tamanho de cada fala com o tempo previsto."""
    for i, item in enumerate(ROTEIRO):
        if item[2]:
            n = len(item[3].split())
            print(f"slide {i + 1:2d} {item[1]:8s} {n:4d} palavras · previsto {_mmss(item[2])} · "
                  f"leitura a {palavras_por_min} ppm ≈ {_mmss(round(60 * n / palavras_por_min))}")


if __name__ == "__main__":
    conferir_ritmo()
    aplicar()
    exportar_md()
