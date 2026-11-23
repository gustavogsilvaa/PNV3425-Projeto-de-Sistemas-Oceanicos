# -*- coding: utf-8 -*-
"""
Gera as apresentações do Trabalho Final em PPTX, no layout do grupo:
  apresentacao/PNV3425_G02_apresentacao_completa.pptx  (~35 slides)
  apresentacao/PNV3425_G02_apresentacao_15min.pptx     (14 slides, com notas e tempos)

Uso (na raiz do repositório):
    python apresentacao/figuras_apresentacao.py
    python apresentacao/gerar_apresentacoes.py
Para os PDFs, converta os PPTX no PowerPoint ou com
    soffice --headless --convert-to pdf apresentacao/*.pptx
"""
import os
import re

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, "figuras")

NAVY, ORANGE, BLUE, TEAL = "0B2E40", "E36C1E", "2E75B6", "1A9E8A"
RED, GREEN = "C0392B", "1E8449"
TXT, SUB, FOOT = "1F2D3A", "5B6B78", "7A8A96"
CARD, ROW_A, ROW_B = "F0F3F6", "F2F5F8", "FFFFFF"
FONT = "Calibri"
SW, SH = 13.333, 7.5

MEMBROS = ["Felipe Perpétuo Simões – 11263255",
           "Gustavo Guilherme Silva – 11820555",
           "João Marcos Magalhães Moura – 12554693"]


def rgb(h):
    return RGBColor.from_string(h)


# ---------------------------------------------------------------------------
# Texto com marcação simples: **negrito**, _{subscrito}, ^{sobrescrito}
# ---------------------------------------------------------------------------
TOK = re.compile(r"(\*\*.+?\*\*|_\{[^}]*\}|\^\{[^}]*\})")


def add_runs(p, texto, size, color=TXT, bold=False, italic=False):
    for parte in TOK.split(texto):
        if not parte:
            continue
        b, base, t = bold, None, parte
        if parte.startswith("**"):
            add_runs(p, parte[2:-2], size, color, True, italic)
            continue
        if parte.startswith("_{"):
            base, t = "-25000", parte[2:-1]
        elif parte.startswith("^{"):
            base, t = "30000", parte[2:-1]
        r = p.add_run()
        r.text = t
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(size), b, italic, FONT
        f.color.rgb = rgb(color)
        if base:
            r.font._element.set("baseline", base)


def _bullet(p, level, color):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(0.28 + 0.34 * level))))
    pPr.set("indent", str(int(-Inches(0.22))))
    c = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(c, qn("a:srgbClr")).set("val", color)
    etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
    etree.SubElement(pPr, qn("a:buChar")).set("char", "•" if level == 0 else "–")


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for a in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, a, Inches(0.04))
    return tf


def texto(slide, l, t, w, h, linhas, size=16, color=TXT, bold=False, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, espaco=4):
    tf = textbox(slide, l, t, w, h, anchor)
    linhas = [linhas] if isinstance(linhas, str) else linhas
    for i, ln in enumerate(linhas):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(espaco)
        add_runs(p, ln, size, color, bold)
    return tf


def bullets(slide, l, t, w, h, itens, size=16, espaco=7):
    """itens: str (nível 0) ou (nível, str)."""
    tf = textbox(slide, l, t, w, h)
    for i, it in enumerate(itens):
        nivel, txt = (0, it) if isinstance(it, str) else it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(espaco if nivel == 0 else espaco - 2)
        _bullet(p, nivel, NAVY)
        add_runs(p, txt, size - 2 * nivel, TXT)
    return tf


def retangulo(slide, l, t, w, h, cor, forma=MSO_SHAPE.RECTANGLE, linha=None):
    s = slide.shapes.add_shape(forma, Inches(l), Inches(t), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(cor)
    if linha:
        s.line.color.rgb = rgb(linha)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    st = s._element.find(qn("p:style"))
    if st is not None:
        s._element.remove(st)
    return s


def kpi(slide, l, t, w, h, rotulo, valor, cor=NAVY, vsize=28):
    retangulo(slide, l, t, w, h, CARD)
    retangulo(slide, l, t, 0.07, h, cor)
    texto(slide, l + 0.22, t + 0.12, w - 0.3, 0.35, rotulo, size=12, color=SUB)
    texto(slide, l + 0.22, t + 0.42, w - 0.3, h - 0.45, valor, size=vsize, color=NAVY, bold=True)


def imagem(slide, nome, l, t, w, h, align="c"):
    """Insere a figura inteira dentro da caixa (l, t, w, h), mantendo a proporção."""
    caminho = os.path.join(FIG, nome)
    iw, ih = Image.open(caminho).size
    esc = min(w / iw, h / ih)
    pw, ph = iw * esc, ih * esc
    x = l + (w - pw) / 2 if align == "c" else l
    y = t + (h - ph) / 2
    return slide.shapes.add_picture(caminho, Inches(x), Inches(y), Inches(pw), Inches(ph))


def equacao(slide, nome, l, t, w, h, align="c"):
    return imagem(slide, nome, l, t, w, h, align)


def tabela(slide, linhas, l, t, w, larg, rh=0.36, size=12, alinh=None, negrito_col0=True,
           destaque=(), cores=None, hsize=None):
    """linhas[0] é o cabeçalho. larg: frações da largura. cores: {(i, j): hex}."""
    n, m = len(linhas), len(linhas[0])
    alinh = alinh or (["l"] + ["c"] * (m - 1))
    gf = slide.shapes.add_table(n, m, Inches(l), Inches(t), Inches(w), Inches(rh * n))
    tb = gf.table
    tb.first_row = True
    tb.horz_banding = False
    for j, f in enumerate(larg):
        tb.columns[j].width = Inches(w * f)
    for i in range(n):
        tb.rows[i].height = Inches(rh)
        for j in range(m):
            c = tb.cell(i, j)
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = rgb(NAVY)
            elif i in destaque:
                c.fill.fore_color.rgb = rgb("FCE9DC")
            else:
                c.fill.fore_color.rgb = rgb(ROW_A if i % 2 == 1 else ROW_B)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.02)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[alinh[j]]
            cor = "FFFFFF" if i == 0 else (cores or {}).get((i, j), TXT)
            neg = i == 0 or (negrito_col0 and j == 0) or i in destaque
            add_runs(p, str(linhas[i][j]), (hsize or size) if i == 0 else size, cor, neg)
    return gf


def seta(slide, x1, y1, x2, y2, cor=NAVY):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(cor)
    c.line.width = Pt(1.75)
    ln = c.line._get_or_add_ln()
    te = etree.SubElement(ln, qn("a:tailEnd"))
    te.set("type", "triangle"); te.set("w", "med"); te.set("len", "med")
    return c


def caixa(slide, l, t, w, h, txt, cor=CARD, borda=NAVY, size=13, bold=False, tcor=TXT):
    s = retangulo(slide, l, t, w, h, cor, MSO_SHAPE.ROUNDED_RECTANGLE, borda)
    s.adjustments[0] = 0.15
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for a in ("margin_left", "margin_right"):
        setattr(tf, a, Inches(0.08))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    add_runs(p, txt, size, tcor, bold)
    return s


# ---------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------
class Deck:
    def __init__(self, rodape):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(SW), Inches(SH)
        self.rodape = rodape
        self.n = 0

    def _novo(self):
        self.n += 1
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    @staticmethod
    def notas(s, txt):
        if txt:
            s.notes_slide.notes_text_frame.text = txt

    def capa(self, kicker, titulo, linhas, notas=None):
        s = self._novo()
        retangulo(s, 0, 0, SW, SH, NAVY)
        texto(s, 1.0, 2.2, 11.5, 0.5, kicker, size=22, color="F4B183", bold=True)
        texto(s, 1.0, 2.72, 11.8, 1.2, titulo, size=42, color="FFFFFF", bold=True)
        retangulo(s, 1.03, 3.92, 1.9, 0.08, ORANGE)
        cores = [("D6E1EA", 19), ("C9D6E0", 16), ("8FA5B5", 14)]
        for i, ln in enumerate(linhas):
            c, sz = cores[min(i, 2)]
            texto(s, 1.0, 4.15 + 0.46 * i, 11.8, 0.45, ln, size=sz, color=c)
        for i, nome in enumerate(MEMBROS):
            texto(s, 1.0, 5.75 + 0.36 * i, 8, 0.35, nome, size=15, color="FFFFFF")
        self.notas(s, notas)
        return s

    def fecho(self, titulo, linhas):
        s = self._novo()
        retangulo(s, 0, 0, SW, SH, NAVY)
        texto(s, 1.0, 2.6, 11.5, 1.1, titulo, size=44, color="FFFFFF", bold=True)
        retangulo(s, 1.03, 3.7, 1.9, 0.08, ORANGE)
        for i, ln in enumerate(linhas):
            texto(s, 1.0, 3.95 + 0.45 * i, 11.5, 0.45, ln, size=17, color="C9D6E0")
        for i, nome in enumerate(MEMBROS):
            texto(s, 1.0, 5.75 + 0.36 * i, 8, 0.35, nome, size=15, color="FFFFFF")
        return s

    def slide(self, titulo, subtitulo, secao, notas=None):
        s = self._novo()
        retangulo(s, 0, 0, 0.2, SH, NAVY)
        texto(s, 0.6, 0.28, 12.3, 0.7, titulo, size=30, color=NAVY, bold=True)
        texto(s, 0.6, 0.94, 12.3, 0.45, subtitulo, size=15, color=SUB)
        retangulo(s, 0.62, 1.42, 1.6, 0.07, ORANGE)
        texto(s, 0.55, 7.0, 10, 0.3, f"{self.rodape} · {secao}", size=10, color=FOOT)
        texto(s, 12.0, 7.0, 0.9, 0.3, str(self.n), size=11, color=FOOT, bold=True, align=PP_ALIGN.RIGHT)
        self.notas(s, notas)
        return s

    def salvar(self, caminho):
        self.prs.save(caminho)
        print(f"{caminho}: {self.n} slides")


# ---------------------------------------------------------------------------
# Conteúdo compartilhado
# ---------------------------------------------------------------------------
TAB_CAMPO = [["Grandeza", "Valor"],
             ["Lâmina d'água · distância à costa", "1.450 m · 190 km"],
             ["Solo marinho", "argiloso"],
             ["Óleo original · grau API", "2,2 bilhões de bbl · 31"],
             ["Fator de recuperação", "30% → 660 milhões de bbl"],
             ["Gás recuperável", "30 bilhões de m³"],
             ["Reservatório", "2.700 m abaixo do leito · coluna de 120 m"],
             ["Mar de 100 anos", "H_{s} = 5,6 m · T_{p} = 15,2 s"]]

TAB_FICHA = [["", "1 · Mín. peso", "2 · Mín. heave", "3 · Escolhida"],
             ["L_{p} · b_{p} · h_{p} [m]", "137,5 · 16,4 · 7,4", "110,1 · 14,2 · 15,0", "111,8 · 13,4 · 10,2"],
             ["b_{c} · h_{c} · T [m]", "8,0 · 20,0 · 12,0", "14,2 · 50,0 · 40,0", "12,6 · 39,6 · 24,0"],
             ["Área de convés [m²]", "18.905", "12.125", "12.499"],
             ["Δ [t] · lastro [t]", "35.244 · 11", "68.962 · 18.081", "40.247 · 11"],
             ["**Peso do casco [t]**", "**10.346**", "**23.634**", "**14.998**"],
             ["KG · GM_{T} · GM_{L} [m]", "27,2 · 4,00 · 7,91", "37,4 · 4,00 · 4,00", "42,8 · 4,00 · 4,67"],
             ["φ_{al} transv. · long. [°]", "9,0 · 9,8", "24,4 · 24,4", "21,6 · 23,9"],
             ["min A/B (transv. · long.)", "1,302 · 1,601", "1,304 · 1,486", "1,303 · 1,304"],
             ["T_{n} [s]", "40,3", "23,1", "21,8"],
             ["**H_{1/3,z} [m]**", "**2,366**", "**1,043**", "**1,552**"],
             ["a_{mín} · a [m]", "7,41 · 15,37", "6,18 · 25,03", "6,65 · 25,84"],
             ["Restrições ativas", "GM_{T}, lastro, A/B", "GM_{T}, b_{c} = b_{p}, A/B", "GM_{T}, lastro, A/B"],
             ["Variáveis no limite", "b_{c}, h_{c}, T mínimos", "h_{c}, T máximos", "nenhuma"]]

TAB_VALID = [["Grandeza", "Modelo", "Aula", "Erro"],
             ["KG [m]", "33,21", "33,00", "+0,6%"],
             ["A/B mínimo transversal", "2,310", "2,33", "−0,9%"],
             ["A/B mínimo longitudinal", "2,273", "2,36", "−3,7%"],
             ["T_{n} [s]", "20,703", "20,70", "0,0%"],
             ["H_{1/3,z} [m]", "2,984", "2,98", "+0,1%"],
             ["η_{max} [m]", "11,35", "11,35", "0,0%"]]

TAB_SENS = [["Hipótese", "Peso do casco", "Variação", "H_{1/3,z}", "Lastro"],
            ["Caso-base (só óleo, h_{m} = 12 m)", "14.998 t", "–", "1,552 m", "11 t"],
            ["h_{m} = 15 m (valor do Ex. 9)", "15.792 t", "+5,3%", "1,560 m", "11 t"],
            ["Gás no BOE (202,9 mil boe/d)", "18.718 t", "+24,8%", "1,373 m", "11 t"],
            ["Lastro mínimo de 10%", "16.026 t", "+6,9%", "1,549 m", "3.611 t"]]

TAB_CRIT = [["Plano", "Vento", "φ_{1}", "φ_{2}", "φ_{al}", "A [m·rad]", "B [m·rad]", "A/B"],
            ["Transversal", "51,5 m/s", "14,1°", "31,6°", "21,6°", "0,574", "0,440", "**1,303**"],
            ["Transversal", "36 m/s", "6,7°", "33,1°", "21,6°", "0,574", "0,215", "2,667"],
            ["Longitudinal", "51,5 m/s", "11,5°", "31,7°", "23,9°", "0,598", "0,459", "1,304"],
            ["Longitudinal", "36 m/s", "5,0°", "33,0°", "23,9°", "0,598", "0,224", "2,669"]]


def s_campo_resumo(d, secao, notas=None, completo=True):
    s = d.slide("O campo KZ-2026-B", "Kwanza Offshore Energy · concessão de 22 anos · bacia do Baixo Congo, Angola",
                secao, notas)
    tabela(s, TAB_CAMPO, 0.6, 1.75, 7.4, [0.45, 0.55], rh=0.5, size=14)
    kpi(s, 8.5, 1.75, 4.3, 1.15, "Pico de produção de óleo (anos 5 a 7)", "158.894 bpd", ORANGE)
    kpi(s, 8.5, 3.05, 4.3, 1.15, "Área mínima de convés  (L_{p} ≥ 107,5 m)", "11.563 m²", NAVY)
    kpi(s, 8.5, 4.35, 4.3, 1.15, "Planta de produção (83 kg/boe)", "13.188 t", BLUE)
    texto(s, 8.5, 5.7, 4.3, 0.9, "A planta é dimensionada pelo pico de óleo. O caso com gás "
          "processado a bordo entra na análise de sensibilidade.", size=13, color=SUB)
    return s


def s_geometria(d, secao, notas=None, compacto=False):
    s = d.slide("Modelo paramétrico: geometria e variáveis",
                "2 pontoons retangulares + 4 colunas quadradas em planta quadrada de lado L_{p}", secao, notas)
    imagem(s, "f_geometria_param.png", 0.5, 1.7, 7.6, 3.5)
    tab = [["Variável", "Mínimo", "Máximo"],
           ["L_{p} [m]", "107,5", "150"], ["b_{p} [m]", "8", "25"], ["h_{p} [m]", "6", "20"],
           ["b_{c} [m]", "8", "25"], ["h_{c} [m]", "20", "50"], ["T [m]", "12", "40"]]
    tabela(s, tab, 8.6, 1.75, 4.2, [0.44, 0.28, 0.28], rh=0.4, size=13)
    if compacto:
        bullets(s, 0.7, 5.35, 12.2, 1.5, [
            "Para cada x = (L_{p}, b_{p}, h_{p}, b_{c}, h_{c}, T): hidrostática → pesos e GM → GZ 2D e vento "
            "→ heave, RAO e espectro → air gap mínimo → restrições e objetivos",
            "Objetivos: **mínimo peso estrutural do casco** e **mínimo H_{1/3,z} de heave**; uma avaliação leva ≈ 6 ms"],
            size=16)
    else:
        bullets(s, 0.7, 5.35, 7.5, 1.5, [
            "Entre pontoons: d_{p} = L_{p} − b_{p}; trecho livre: l_{d} = L_{p} − 2b_{c}",
            "Air gap a = h_{p} + h_{c} − T; restrição geométrica extra T − h_{p} ≥ 1 m",
            "Objetivos: mínimo W_{casco} e mínimo H_{1/3,z}"], size=16)
        texto(s, 8.6, 4.75, 4.2, 1.6, "L_{p} mínimo vem da área de convés. Os demais limites são escolhas "
              "práticas do grupo; os extremos da fronteira encostam neles.", size=13, color=SUB)
    return s


def s_validacao(d, secao, notas=None):
    s = d.slide("Validação: plataforma dos Exercícios 7 a 10",
                "L_{p} = 100 m · b_{p} = h_{p} = b_{c} = 15 m · h_{c} = 45 m · T = 30 m · H_{s} = 12,2 m · h_{m} = 15 m",
                secao, notas)
    tabela(s, TAB_VALID, 0.6, 1.75, 7.6, [0.46, 0.18, 0.18, 0.18], rh=0.62, size=15)
    kpi(s, 8.7, 1.75, 2.0, 1.15, "T_{n}", "20,70 s", NAVY, 26)
    kpi(s, 10.85, 1.75, 2.0, 1.15, "H_{1/3,z}", "2,98 m", ORANGE, 26)
    bullets(s, 8.7, 3.1, 4.2, 3.6, [
        "Erros de 0,0% a 3,7% contra os resultados das aulas",
        "dGZ/dφ em 0° = GM nos dois planos (erro nulo)",
        "RAO(ω → 0) = 1 e Σ pesos = Δ",
        "Linha d'água por Newton = bissecção em 2.030 geometrias (|ΔGZ| ≤ 1,2·10^{−8} m)",
        "Com h_{d} = 7 m o KG daria 33,00 m, mas o A/B subiria para 2,42"], size=15)
    return s


def s_otimizacao(d, secao, notas=None):
    s = d.slide("Procedimento de variação sistemática",
                "Amostragem do domínio + dois métodos de otimização + filtro de não dominância", secao, notas)
    passos = [("1", "Hipercubo latino", "20.000 combinações no domínio; só 547 passam sem vento e 227 com vento", BLUE),
              ("2", "Soma ponderada", "SLSQP para w_{1} = 0; 0,05; …; 1, partindo das 5 melhores amostras e do w_{1} anterior", NAVY),
              ("3", "ε-restrito", "min W_{casco} com H_{1/3,z} ≤ ε em 12 níveis: preenche os trechos não convexos", TEAL),
              ("4", "Não dominância", "Filtro sobre as 260 soluções viáveis; cada ótimo é reconfirmado com GZ a cada 0,25°", ORANGE)]
    for i, (n, tit, desc, cor) in enumerate(passos):
        x = 0.6 + i * 3.1
        retangulo(s, x, 1.75, 2.95, 2.35, CARD)
        retangulo(s, x, 1.75, 2.95, 0.07, cor)
        texto(s, x + 0.18, 1.9, 0.6, 0.6, n, size=30, color=cor, bold=True)
        texto(s, x + 0.7, 2.02, 2.2, 0.5, tit, size=17, color=NAVY, bold=True)
        texto(s, x + 0.18, 2.6, 2.65, 1.45, desc, size=14, color=TXT)
    equacao(s, "eq_obj.png", 0.6, 4.3, 6.3, 0.75)
    equacao(s, "eq_eps.png", 7.0, 4.35, 5.8, 0.6)
    vals = [("Amostras avaliadas", "20.000", BLUE), ("Viáveis no LHS", "227 (1,1%)", NAVY),
            ("Pontos na fronteira", "25", ORANGE), ("Tempo da rodada (8 núcleos)", "≈ 4 min", TEAL)]
    for i, (r, v, c) in enumerate(vals):
        kpi(s, 0.6 + i * 3.1, 5.3, 2.95, 1.25, r, v, c, 26)
    return s


def s_pareto(d, secao, notas=None, extra=False):
    s = d.slide("Conjunto viável e fronteira de Pareto", "Peso estrutural do casco × altura significativa de heave",
                secao, notas)
    imagem(s, "f_pareto.png", 0.45, 1.65, 8.3, 5.25)
    itens = ["O critério de vento é a restrição mais seletiva: 547 → 227 amostras",
             "A fronteira vai de **10.346 t** (H_{1/3,z} = 2,37 m) a **23.634 t** (1,04 m)",
             "Fronteira não convexa: 7 dos 21 ótimos da soma ponderada ficam dominados; o ε-restrito preenche os vazios",
             "Nenhuma amostra do LHS sobrevive ao filtro: o SLSQP acha um casco 14,9% mais leve"]
    if extra:
        itens.append("GM_{T} = 4 m e A/B = 1,30 estão ativos nos 25 pontos: o projeto é governado pela estabilidade")
    bullets(s, 8.95, 1.8, 4.0, 5.0, itens, size=15)
    return s


def s_ficha(d, secao, notas=None):
    s = d.slide("Ficha técnica comparativa dos três cenários",
                "Extremos da fronteira (w_{1} = 0 e w_{1} = 1) e solução escolhida no joelho", secao, notas)
    tabela(s, TAB_FICHA, 0.6, 1.7, 12.2, [0.28, 0.24, 0.24, 0.24], rh=0.355, size=13, destaque=(5, 10),
           cores={(13, 3): GREEN, (13, 1): RED, (13, 2): RED})
    return s


def s_final_dim(d, secao, notas=None):
    s = d.slide("Solução final: dimensões, pesos e centros",
                "Cenário 3 · ε-restrito com H_{1/3,z} ≤ 1,552 m · todas as variáveis no interior do domínio",
                secao, notas)
    dim = [["Dimensão", "Valor"], ["L_{p}", "111,80 m"], ["b_{p} · h_{p}", "13,40 · 10,21 m"],
           ["b_{c} · h_{c}", "12,55 · 39,61 m"], ["T · air gap a", "23,98 · 25,84 m"],
           ["Área de convés", "12.499 m² (+8,1%)"], ["Δ", "40.247 t"], ["KB · KG", "7,75 · 42,82 m"],
           ["GM_{T} · GM_{L}", "4,00 · 4,67 m"]]
    tabela(s, dim, 0.6, 1.75, 4.6, [0.48, 0.52], rh=0.45, size=15)
    pes = [["Item", "Peso [t]", "VCG [m]"], ["Planta de produção", "13.188", "63,82"],
           ["Estrutura do convés", "4.616", "53,82"], ["Carga operacional", "4.616", "53,82"],
           ["Pontoons", "8.257", "5,10"], ["Colunas", "6.741", "30,01"],
           ["Risers + amarração", "2.817", "49,82"], ["Lastro", "11", "0,00"], ["**Total = Δ**", "**40.247**", "**42,82**"]]
    tabela(s, pes, 5.5, 1.75, 4.6, [0.5, 0.25, 0.25], rh=0.45, size=14)
    kpi(s, 10.4, 1.75, 2.45, 1.2, "Peso do casco", "14.998 t", ORANGE, 26)
    kpi(s, 10.4, 3.1, 2.45, 1.2, "Topside", "22.420 t", NAVY, 26)
    texto(s, 10.4, 4.45, 2.45, 1.9, "O KG alto vem das 22.420 t de topside; o GM de 4 m sai do BM de 39 m.",
          size=13, color=SUB)
    return s


def s_final_gz(d, secao, notas=None, com_tabela=False):
    s = d.slide("Solução final: estabilidade intacta",
                "Curvas GZ e HA nos dois planos · critério DNV-OS-C301 / MODU 2009", secao, notas)
    if com_tabela:
        imagem(s, "f_gz_final.png", 0.5, 1.6, 12.4, 3.55)
        tabela(s, TAB_CRIT, 0.6, 5.2, 12.2, [0.15, 0.12, 0.1, 0.1, 0.1, 0.15, 0.15, 0.13], rh=0.33, size=12)
    else:
        imagem(s, "f_gz_final.png", 0.5, 1.6, 12.4, 3.9)
        bullets(s, 0.7, 5.6, 12.2, 1.3, [
            "A/B = 1,303 no plano transversal (caso crítico) e 1,304 no longitudinal; φ_{2} > φ_{al} nos quatro casos",
            "O ganho de GZ depois de ≈ 15° vem do pontoon de barlavento saindo da água; após φ_{al} a curva não tem significado físico"],
            size=15)
    return s


def s_final_heave(d, secao, notas=None, compacto=False):
    s = d.slide("Solução final: heave e air gap" if compacto else "Solução final: forças de excitação e RAO",
                "Mar de 100 anos JONSWAP γ = 3,3 · H_{s} = 5,6 m · T_{p} = 15,2 s · ξ = 0,05", secao, notas)
    if compacto:
        imagem(s, "f_rao.png", 0.45, 1.65, 6.1, 3.6)
        imagem(s, "f_espectros.png", 6.7, 1.65, 6.1, 3.6)
        vals = [("T_{n}", "21,85 s", NAVY), ("RAO máximo", "1,47 m/m", BLUE), ("H_{1/3,z}", "1,552 m", ORANGE),
                ("Folga de air gap", "19,2 m", TEAL)]
        for i, (r, v, c) in enumerate(vals):
            kpi(s, 0.6 + i * 3.1, 5.45, 2.95, 1.2, r, v, c, 26)
    else:
        imagem(s, "f_forcas_heave.png", 0.45, 1.65, 6.1, 3.6)
        imagem(s, "f_rao.png", 6.7, 1.65, 6.1, 3.6)
        bullets(s, 0.7, 5.4, 12.2, 1.5, [
            "A força se anula em ω = 0,314 rad/s, logo acima de ω_{n} = 0,288 rad/s: o cancelamento limita o pico do RAO a 1,47",
            "No pico do mar (ω_{p} = 0,413 rad/s): F_{col} = 3.257, F_{pont} = −2.526, F_{MA} = −2.928 kN/m; cos(ω²d_{p}/2g) = 0,654; RAO = 0,32"],
            size=15)
    return s


def s_justificativa(d, secao, notas=None):
    s = d.slide("Por que a solução intermediária", "Custo marginal de reduzir o heave ao longo da fronteira",
                secao, notas)
    imagem(s, "f_custo_marginal.png", 0.45, 1.65, 6.9, 5.1)
    tab = [["Trecho", "Peso adicional", "Redução de H_{1/3,z}", "t por mm"],
           ["Cenário 1 → 3", "4.652 t", "0,81 m", "5,7"], ["Cenário 3 → 2", "8.635 t", "0,51 m", "**17,0**"]]
    tabela(s, tab, 7.6, 1.8, 5.25, [0.3, 0.25, 0.27, 0.18], rh=0.45, size=13)
    bullets(s, 7.6, 3.4, 5.25, 3.4, [
        "Depois do joelho, cada milímetro de heave custa **3×** mais peso",
        "Contra o cenário 1: +45% de peso e −34% de H_{1/3,z}; contra o 2: −37% de peso",
        "Única solução com todas as variáveis no interior do domínio",
        "φ_{al} = 21,6°, contra 9,0° do cenário de mínimo peso"], size=15)
    return s


def s_sensibilidade(d, secao, notas=None):
    s = d.slide("Sensibilidade às hipóteses", "Otimização completa repetida para as hipóteses mais incertas",
                secao, notas)
    tabela(s, TAB_SENS, 0.6, 1.75, 7.3, [0.4, 0.16, 0.13, 0.16, 0.15], rh=0.5, size=13)
    imagem(s, "f_sens_hdhm.png", 8.1, 1.65, 4.9, 2.6)
    texto(s, 8.15, 4.25, 4.8, 0.4, "Geometria fixa da solução final, variando h_{d} e h_{m}", size=11, color=SUB)
    bullets(s, 0.7, 4.45, 12.2, 2.4, [
        "Com a geometria fixa, só h_{d} = 8 m e h_{m} = 12 m são viáveis: a solução está no limite de GM_{T} e A/B",
        "Reotimizando, h_{m} = 15 m custa +5,3% e o lastro mínimo de 10% custa +6,9%, com o mesmo H_{1/3,z}",
        "**Gás no BOE é a hipótese de maior impacto (+24,8%)** e deve ser confirmada com o professor",
        "H_{1/3,z} varia 7% entre γ = 1 e 3,3 e 12% entre ξ = 0,03 e 0,08; o a_{mín} muda menos de 0,2 m"],
        size=15)
    return s


# ---------------------------------------------------------------------------
# Versão completa
# ---------------------------------------------------------------------------
def completa():
    d = Deck("PNV3425 – Projeto de Sistemas Oceânicos · Trabalho Final")
    d.capa("Trabalho Final", "Projeto paramétrico de uma semissubmersível",
           ["Bloco KZ-2026-B · bacia do Baixo Congo (Angola) · lâmina d'água de 1.450 m",
            "Otimização multiobjetivo: peso estrutural do casco × altura significativa de heave",
            "PNV3425 – Projeto de Sistemas Oceânicos · Escola Politécnica da USP · 2º semestre de 2026"])

    # Roteiro
    s = d.slide("Roteiro", "Do campo à solução final", "Roteiro")
    itens = [("Campo e dados de projeto", "reservatório, curva de produção, mar de 100 anos e hipóteses"),
             ("Modelo paramétrico", "geometria, fluxo de cálculo e equações dos Exercícios 7 a 10"),
             ("Validação", "comparação com os resultados das aulas"),
             ("Otimização e fronteira de Pareto", "LHS, soma ponderada, ε-restrito e restrições ativas"),
             ("Os três cenários", "mínimo peso, mínimo heave e solução escolhida"),
             ("Solução final", "pesos, estabilidade, vento, heave, air gap e restrições"),
             ("Sensibilidade e conclusões", "hipóteses incertas, recomendações e próximos passos")]
    for i, (t, dsc) in enumerate(itens):
        y = 1.75 + i * 0.72
        caixa(s, 0.8, y, 0.55, 0.55, str(i + 1), ORANGE, ORANGE, 18, True, "FFFFFF")
        texto(s, 1.6, y - 0.02, 5.5, 0.4, t, size=19, color=NAVY, bold=True)
        texto(s, 1.6, y + 0.32, 10.5, 0.35, dsc, size=13, color=SUB)

    sec = "Campo e dados"
    s_campo_resumo(d, sec)

    s = d.slide("Curva de produção e demanda de topside",
                "A planta é dimensionada pelo pico de óleo; o gás entra na sensibilidade", sec)
    imagem(s, "f_producao.png", 0.45, 1.65, 7.2, 4.4)
    bullets(s, 7.9, 1.8, 5.0, 5.0, [
        "A integral da curva dá 659 milhões de bbl, coerente com os 660 recuperáveis",
        "Q = 158,9 mil boe/d → L_{p}^{2} ≥ 42,246Q + 4850,1 = 11.563 m² → **L_{p} ≥ 107,5 m**",
        "Planta: 0,083 t/boe → **13.188 t**; estrutura do convés e carga operacional: 35% cada",
        "Topside total: **22.420 t**, centro a h_{p} + h_{c} + h_{d} + h_{m}/2",
        "Com o gás (30 bi m³ ≈ 183 mi boe, +27,7%) o pico iria a 202,9 mil boe/d"], size=16)

    s = d.slide("Condições ambientais e dados fixos",
                "Mar de 100 anos do campo; vento do critério de estabilidade do enunciado", sec)
    amb = [["Retorno", "H_{s} [m]", "T_{p} [s]", "Vento [m/s]"], ["1 ano", "3,4", "11,5", "12,0"],
           ["10 anos", "4,5", "13,4", "18,0"], ["**100 anos**", "**5,6**", "**15,2**", "24,0"]]
    tabela(s, amb, 0.6, 1.75, 5.6, [0.3, 0.23, 0.23, 0.24], rh=0.46, size=14, destaque=(3,))
    fix = [["Dado", "Valor"], ["γ_{e} (aço)", "0,270 t/m³"], ["h_{d} · h_{m} (estimados)", "8 · 12 m"],
           ["Vento: tempestade · operação", "51,5 · 36 m/s"], ["ξ heave", "0,05"],
           ["JONSWAP γ", "3,3 (T_{p}/√H_{s} = 6,42)"], ["ρ · ρ_{ar}", "1,025 t/m³ · 1,222 kg/m³"]]
    tabela(s, fix, 6.6, 1.75, 6.2, [0.5, 0.5], rh=0.46, size=14)
    bullets(s, 0.7, 4.0, 5.6, 2.8, [
        "O vento de 100 anos do local (24 m/s) dá só 22% do momento do vento de 51,5 m/s: o critério é conservador",
        "A corrente (0,95 m/s na superfície) fica fora do escopo: não há análise de ancoragem"], size=15)
    texto(s, 6.6, 5.15, 6.2, 1.4, "h_{d} e h_{m} devem ser estimados por semelhantes. Os módulos respondem "
          "por 54% do HM_{0} da solução final, por isso o efeito deles é testado na sensibilidade.",
          size=13, color=SUB)

    sec = "Modelo"
    s_geometria(d, sec)

    s = d.slide("Fluxo de cálculo", "Cada etapa usa as saídas da anterior · uma avaliação completa ≈ 6 ms", sec)
    caixa(s, 4.2, 1.7, 4.9, 0.5, "Variáveis x = (L_{p}, b_{p}, h_{p}, b_{c}, h_{c}, T)", "FCE9DC", ORANGE, 14, True)
    esq = ["1 · Hidrostática (Ex. 7): ∇, Δ, KB, BM, KM", "2 · Pesos e centros (Ex. 8): W_{casco}, lastro, KG, GM",
           "3 · Convés e air gap (Ex. 8): L_{p}^{2}, a", "4 · Curva GZ por projeções 2D (Ex. 9), φ_{al}",
           "5 · Vento (Ex. 9): HM_{0}, HM_{ud}, HA, A/B"]
    dir_ = ["6 · Heave (Ex. 10): F_{3}, A_{33}, C_{33}, T_{n}, RAO", "7 · Espectro (Ex. 10): S_{z}, m_{0z}, H_{1/3,z}",
            "8 · Air gap mínimo: η_{max}, z_{min}, a_{mín}"]
    ys = [2.55 + 0.78 * i for i in range(5)]
    for y, t in zip(ys, esq):
        caixa(s, 1.0, y, 5.2, 0.55, t, size=14)
    for y, t in zip(ys[:3], dir_):
        caixa(s, 7.1, y, 5.2, 0.55, t, size=14)
    caixa(s, 7.1, ys[3], 5.2, 0.55, "Restrições e objetivos: W_{casco}, H_{1/3,z}", "FBE3E1", RED, 14, True)
    caixa(s, 7.1, ys[4], 5.2, 0.55, "LHS + soma ponderada + ε-restrito → Pareto", "DFF1EC", TEAL, 14, True)
    seta(s, 5.4, 2.2, 3.6, 2.55)
    for y in ys[:-1]:
        seta(s, 3.6, y + 0.55, 3.6, y + 0.78)
        seta(s, 9.7, y + 0.55, 9.7, y + 0.78)
    seta(s, 6.2, ys[0] + 0.27, 7.1, ys[0] + 0.27)
    seta(s, 6.2, ys[4] + 0.27, 7.1, ys[3] + 0.4)

    s = d.slide("1–3) Hidrostática, pesos e air gap", "Exercícios 7 e 8 · KG do modelo de pesos, sem superfície livre", sec)
    equacao(s, "eq_hidro.png", 0.6, 1.7, 12.2, 0.75)
    pes = [["Item", "Peso", "VCG (da quilha)"], ["Planta de produção", "0,083 t/boe × BOE", "h_{p} + h_{c} + h_{d} + h_{m}/2"],
           ["Estrutura do convés · carga operacional", "0,35 W_{planta} cada", "h_{p} + h_{c} + h_{d}/2"],
           ["Pontoons · colunas", "γ_{e}·2L_{p}b_{p}h_{p} · γ_{e}·4b_{c}^{2}h_{c}", "h_{p}/2 · h_{p} + h_{c}/2"],
           ["Risers · amarração", "4% Δ · 3% Δ", "h_{p} + h_{c}"], ["Lastro", "Δ − ΣW", "n/2 (nível real)"]]
    tabela(s, pes, 0.6, 2.65, 8.1, [0.36, 0.34, 0.30], rh=0.62, size=14)
    bullets(s, 9.0, 2.7, 3.9, 4.0, [
        "O lastro fecha ΣW = Δ e fica nos pontoons com nível n = V_{lastro}/(2L_{p}b_{p})",
        "W_{casco} = pontoons + colunas é o 1º objetivo",
        "A_{wp} = 4b_{c}^{2}; I_{T} e I_{L} pelos centros das colunas",
        "Air gap: a = h_{p} + h_{c} − T"], size=15)

    s = d.slide("4) Curva GZ pelo método de projeções 2D", "Volume constante a cada ângulo, nos planos transversal e longitudinal", sec)
    equacao(s, "eq_gz.png", 0.6, 1.7, 12.2, 0.7)
    bullets(s, 0.7, 2.65, 7.8, 4.2, [
        "Cada plano é um conjunto de retângulos com espessura fora do plano:",
        (1, "transversal: 2 pontoons (largura b_{p}, espessura L_{p}) + 2 colunas (b_{c}, espessura 2b_{c})"),
        (1, "longitudinal: retângulo L_{p} × h_{p} (espessura 2b_{p}) + 2 colunas nas extremidades"),
        "Linha d'água inclinada z = α + u·tan φ; α por Newton com derivada exata ∂V/∂α = Σ t_{i}ℓ_{i} e salvaguarda de bissecção",
        "φ_{al}: o fundo do convés na borda (u = L_{p}/2, z = h_{p} + h_{c}) toca a água (Brent)",
        "Passo de 1° na otimização e de 0,25° nos resultados finais"], size=16)
    kpi(s, 8.9, 2.7, 3.9, 1.2, "dGZ/dφ em 0° contra GM", "erro 0,0%", NAVY, 24)
    kpi(s, 8.9, 4.05, 3.9, 1.2, "Newton × bissecção (2.030 cascos)", "|ΔGZ| ≤ 1,2·10^{−8} m", ORANGE, 22)

    s = d.slide("5) Momento de vento e critério de áreas",
                "DNV-OS-C301 / MODU 2009 · 2 planos × 2 velocidades (51,5 e 36 m/s)", sec)
    equacao(s, "eq_ha.png", 0.6, 1.7, 12.2, 0.8)
    par = [["Parcela", "Área exposta", "Altura z sobre a LA", "C_{s}", "Momento"],
           ["Colunas (4, sem sombra)", "4 b_{c} a", "a/2", "1,0", "HM_{0}"],
           ["Deck box", "L_{p} h_{d}", "a + h_{d}/2", "1,0", "HM_{0}"],
           ["Módulos de topside", "L_{p} h_{m}", "a + h_{d} + h_{m}/2", "1,1", "HM_{0}"],
           ["Face inferior do convés", "L_{p}^{2}", "a", "1,0", "HM_{ud}"]]
    tabela(s, par, 0.6, 2.75, 7.9, [0.32, 0.18, 0.24, 0.1, 0.16], rh=0.6, size=14)
    bullets(s, 8.8, 2.75, 4.1, 4.1, [
        "F = ½ρ_{ar}V^{2} C_{s} C_{h} A, com C_{h} da tabela do MODU",
        "Braço até o z_{CLR}, centroide da silhueta submersa de cada plano",
        "Atende se A ≥ 1,3B e GZ > 0 até φ_{2} (ou φ_{al}) nos 4 casos",
        "Na otimização: min A/B ≥ 1,3 no caso mais desfavorável"], size=15)

    s = d.slide("6) Forças de heave e massa adicional", "Froude-Krylov nas colunas e nos pontoons + difração pela massa adicional", sec)
    equacao(s, "eq_f3.png", 0.6, 1.7, 12.2, 0.85)
    equacao(s, "eq_a33.png", 0.6, 2.75, 12.2, 0.85)
    bullets(s, 0.7, 3.9, 12.2, 2.9, [
        "cos(ω²d_{p}/2g): defasagem da onda de través entre os dois pontoons (d_{p} = L_{p} − b_{p})",
        "C_{A} de retângulo da DNV-RP-C205 em função de b_{p}/h_{p}; massa adicional só no trecho livre l_{d} = L_{p} − 2b_{c}",
        "B_{33} = 2ξ√(C_{33}(Δ + A_{33})) com ξ = 0,05; forças por metro de amplitude de onda",
        "As três parcelas têm sinais opostos: o zero de F_{3} logo acima de ω_{n} corta a ressonância"], size=16)

    s = d.slide("7–8) RAO, espectro de resposta e air gap mínimo",
                "Resposta linear no mar de 100 anos e estatística de Rayleigh para 3 horas", sec)
    equacao(s, "eq_rao.png", 0.6, 1.7, 12.2, 0.85)
    equacao(s, "eq_airgap.png", 0.6, 2.75, 8.0, 0.85)
    bullets(s, 0.7, 3.9, 7.9, 2.9, [
        "JONSWAP da DNV-RP-C205 com γ = 3,3 e σ = 0,07/0,09; H_{1/3,z} também com γ = 1",
        "1.500 frequências entre 0,02 e 2,5 rad/s",
        "Hipótese conservadora do enunciado: crista máxima com a plataforma na posição mais baixa",
        "Sem roll, pitch e efeitos não lineares da crista (DNVGL-OTG-13)"], size=16)
    kpi(s, 9.0, 3.9, 3.85, 1.2, "Crista máxima η_{max} = 1,86 H_{s}/2", "5,21 m", BLUE, 26)

    s = d.slide("Restrições do problema", "Seção 2 do enunciado, mais uma restrição geométrica de consistência", sec)
    rst = [["Restrição", "Expressão", "Origem"],
           ["Área mínima de convés", "L_{p}^{2} ≥ 42,246Q + 4850,1 = 11.563 m²", "Aula de pesos e centros"],
           ["Estabilidade inicial", "1 m ≤ GM_{T} ≤ 4 m", "Enunciado"],
           ["Período natural de heave", "T_{n} > 20 s", "Enunciado"],
           ["Lastro", "W_{lastro} > 0 e V_{lastro} ≤ 0,9 V_{pontoons}", "Enunciado"],
           ["Colunas e pontoons", "b_{c} ≤ b_{p}", "Enunciado"],
           ["Critério de áreas", "min A/B ≥ 1,3 e GZ > 0, nos 4 casos", "DNV-OS-C301 / MODU"],
           ["Air gap", "a ≥ a_{mín} = η_{max} − z_{min}", "Enunciado (item 4)"],
           ["Consistência geométrica", "T − h_{p} ≥ 1 m (nunca ativa)", "Adicional do grupo"]]
    tabela(s, rst, 0.6, 1.75, 12.2, [0.27, 0.48, 0.25], rh=0.5, size=14, destaque=(8,))

    sec = "Validação"
    s_validacao(d, sec)
    s = d.slide("Validação: curvas GZ e braço de vento", "Plataforma dos Exercícios 7 a 10 · BOE = 120.000 · h_{d} = 8 m · h_{m} = 15 m", sec)
    imagem(s, "f_gz_validacao.png", 0.5, 1.65, 12.4, 4.2)
    bullets(s, 0.7, 5.95, 12.2, 1.0, [
        "φ_{al} = 27,6° (transversal) e 30,4° (longitudinal); z_{CLR} = 10,96 m e 15,00 m; o plano longitudinal fica 3,7% abaixo da aula"],
        size=15)

    sec = "Otimização"
    s_otimizacao(d, sec)
    s_pareto(d, sec)
    s = d.slide("Restrições ativas e famílias de projeto", "Variáveis normalizadas pelos limites ao longo dos 25 pontos da fronteira", sec)
    imagem(s, "f_variaveis_fronteira.png", 0.45, 1.65, 7.9, 4.5)
    tab = [["Restrição ativa", "Pontos"], ["GM_{T} = 4 m", "25 / 25"], ["A/B = 1,30", "25 / 25"],
           ["Lastro ≈ 0", "17 / 25"], ["b_{c} = b_{p}", "9 / 25"], ["Área de convés", "4 / 25"],
           ["Air gap · T_{n}", "0 / 25"]]
    tabela(s, tab, 8.7, 1.75, 4.15, [0.62, 0.38], rh=0.42, size=14, destaque=(1, 2))
    bullets(s, 8.7, 4.85, 4.2, 2.0, [
        "**Rasa e larga** (até 13.700 t): L_{p} → 150 m, T_{n} de 29 a 40 s",
        "**Compacta e profunda** (acima de 14.200 t): L_{p} ≈ 108–118 m, T_{n} ≈ 22 s"], size=13)

    sec = "Cenários"
    s_ficha(d, sec)
    s = d.slide("Geometria dos três cenários", "Vista lateral com linha d'água de projeto e crista máxima η_{max} = 5,21 m", sec)
    imagem(s, "f_geometria_3.png", 0.4, 1.6, 12.5, 4.1)
    bullets(s, 0.7, 5.75, 12.2, 1.2, [
        "Folga de air gap de 8 a 19 m: com H_{s} = 5,6 m, h_{c} é definido pelo φ_{al} do critério de vento, e não pela onda",
        "Só o cenário 2 tem lastro real (18.081 t); nos cenários 1 e 3 o deslocamento é todo consumido por casco e topside"], size=15)

    s = d.slide("Cenário 1 · mínimo peso estrutural", "w_{1} = 0 · semissubmersível rasa: T, h_{c} e b_{c} no limite mínimo", sec)
    imagem(s, "f_gz_cen1.png", 0.45, 1.65, 8.4, 3.4)
    for i, (r, v, c) in enumerate([("Peso do casco", "10.346 t", RED), ("H_{1/3,z}", "2,37 m", NAVY), ("φ_{al} transversal", "9,0°", ORANGE)]):
        kpi(s, 9.1, 1.75 + i * 1.3, 3.75, 1.15, r, v, c, 26)
    bullets(s, 0.7, 5.2, 12.2, 1.7, [
        "Pontoons levam 87% do casco; com colunas de 8 m o GM só sai do afastamento, por isso L_{p} = 137,5 m",
        "Topo dos pontoons a só 4,6 m de profundidade: H_{1/3,z}/H_{s} = 42%, apesar de T_{n} = 40 s",
        "Sob tempestade a plataforma inclina 4,9°, mais da metade do caminho até o alagamento: reserva pequena demais"], size=15)

    s = d.slide("Cenário 2 · mínimo heave", "w_{1} = 1 · calado profundo: T = 40 m e h_{c} = 50 m no limite máximo", sec)
    imagem(s, "f_gz_cen2.png", 0.45, 1.65, 8.4, 3.4)
    for i, (r, v, c) in enumerate([("Peso do casco", "23.634 t", GREEN), ("H_{1/3,z}", "1,04 m", NAVY), ("Lastro", "18.081 t", BLUE)]):
        kpi(s, 9.1, 1.75 + i * 1.3, 3.75, 1.15, r, v, c, 26)
    bullets(s, 0.7, 5.2, 12.2, 1.7, [
        "Topo dos pontoons a 25 m: o fator e^{−k(T−h_{p})} vale 0,65 no pico do mar (0,92 no cenário 1); H_{1/3,z}/H_{s} = 19%",
        "Único cenário com lastro real (37,5% dos pontoons); b_{c} = b_{p} = 14,2 m e φ_{al} = 24,4° nos dois planos",
        "Casco 2,3× mais pesado, 46% nas colunas; o fim da fronteira é plano (23.306 → 23.634 t para −0,003 m)"], size=15)

    s = d.slide("Heave dos três cenários", "RAO e espectro de resposta no mesmo mar de 100 anos", sec)
    imagem(s, "f_heave_3cenarios.png", 0.45, 1.6, 7.0, 5.2)
    bullets(s, 7.7, 1.8, 5.2, 5.0, [
        "Cenário 1: T_{n} = 40,3 s, longe da ressonância, mas a excitação quase não se atenua com pontoons rasos",
        "Cenários 2 e 3: T_{n} de 22 a 23 s; o zero da força logo acima de ω_{n} corta o pico",
        "Nos três, a maior parte da resposta fica no pico do mar (0,41 rad/s), e não em ω_{n}",
        "H_{1/3,z}: 2,37 → 1,55 → 1,04 m; H_{1/3,z}/H_{s}: 42% → 28% → 19%"], size=16)

    sec = "Solução final"
    s_final_dim(d, sec)
    s_final_gz(d, sec)
    s = d.slide("Solução final: forças e momentos de vento",
                "Forças iguais nos dois planos (planta quadrada); braços até o z_{CLR} de cada plano", sec)
    tv = [["Parcela", "Área [m²]", "z [m]", "C_{s}", "C_{h}", "F 51,5 [kN]", "F 36 [kN]", "Braço T [m]", "Braço L [m]"],
          ["Colunas (4)", "1.297", "12,9", "1,0", "1,00", "2.102", "1.027", "29,0", "25,1"],
          ["Deck box", "894", "29,8", "1,0", "1,10", "1.594", "779", "45,9", "42,0"],
          ["Módulos", "1.342", "39,8", "1,1", "1,20", "2.870", "1.402", "55,9", "52,0"],
          ["Face inferior", "12.499", "25,8", "1,0", "1,10", "22.281", "10.887", "41,9", "38,0"]]
    tabela(s, tv, 0.6, 1.75, 12.2, [0.16, 0.1, 0.08, 0.07, 0.07, 0.13, 0.13, 0.13, 0.13], rh=0.45, size=13)
    mv = [["Momento [kN·m]", "Transv. 51,5", "Transv. 36", "Long. 51,5", "Long. 36"],
          ["HM_{0} (colunas + deck + módulos)", "294.706", "144.005", "269.057", "131.473"],
          ["HM_{ud} (face inferior)", "934.163", "456.471", "847.134", "413.945"],
          ["HA(0) = HM_{0}/Δg [m]", "0,746", "0,365", "0,682", "0,333"],
          ["z_{CLR} [m]", "7,89", "7,89", "11,80", "11,80"]]
    tabela(s, mv, 0.6, 4.25, 8.2, [0.36, 0.16, 0.16, 0.16, 0.16], rh=0.44, size=13)
    bullets(s, 9.1, 4.3, 3.8, 2.5, [
        "A face inferior gera 3,2× o HM_{0}: aumentar L_{p} aumenta o momento",
        "Os módulos são 54% do HM_{0}",
        "Transversal é crítico: z_{CLR} mais baixo"], size=15)

    s = d.slide("Solução final: critério de áreas", "Áreas de 0 a φ_{al} com φ em radianos · quatro casos", sec)
    tabela(s, TAB_CRIT, 0.6, 1.75, 12.2, [0.15, 0.12, 0.1, 0.1, 0.1, 0.15, 0.15, 0.13], rh=0.5, size=14, destaque=(1,))
    for i, (r, v, c) in enumerate([("A/B mínimo (≥ 1,3)", "1,303", ORANGE), ("GZ > 0 até φ_{al}", "atende", GREEN),
                                   ("Inclinação sob tempestade", "14,1°", NAVY)]):
        kpi(s, 0.6 + i * 4.15, 4.6, 3.95, 1.2, r, v, c, 26)
    texto(s, 0.6, 6.0, 12.2, 0.8, "φ_{2} > φ_{al} nos quatro casos, então a verificação de GZ > 0 vai até φ_{al}. "
          "A inclinação de 14° sob vento de tempestade merece atenção nas fases seguintes.", size=14, color=SUB)

    s_final_heave(d, sec)
    s = d.slide("Solução final: espectros e altura significativa", "S_{z} = RAO² S_{ζ} · H_{1/3,z} = 4√m_{0z}", sec)
    imagem(s, "f_espectros.png", 0.45, 1.65, 7.3, 4.3)
    hv = [["Grandeza", "Valor"], ["C_{A} · l_{d}", "1,451 · 86,7 m"], ["A_{33}", "36.378 t"],
          ["C_{33} · B_{33}", "6.337 kN/m · 2.204 kN·s/m"], ["ω_{n} · T_{n}", "0,288 rad/s · 21,85 s"],
          ["m_{0z}", "0,1506 m²"], ["H_{1/3,z} (γ = 3,3 · γ = 1)", "1,552 · 1,454 m"]]
    tabela(s, hv, 8.0, 1.75, 4.85, [0.5, 0.5], rh=0.45, size=13)
    bullets(s, 8.0, 5.0, 4.9, 1.9, [
        "Pico pequeno em ω_{n} e pico principal em ω_{p}",
        "H_{1/3,z}/H_{s} = 28%; T_{n} 9% acima do limite"], size=15)

    s = d.slide("Solução final: air gap e resumo das restrições", "Valor de cada restrição e folga em relação ao limite", sec)
    ag = [["Air gap", "Valor"], ["η_{max} = 1,86·5,6/2", "5,21 m"], ["z_{min} = −1,86·1,552/2", "−1,44 m"],
          ["a_{mín} = η_{max} − z_{min}", "6,65 m"], ["a = h_{p} + h_{c} − T", "25,84 m"], ["**Folga**", "**19,19 m**"]]
    tabela(s, ag, 0.6, 1.75, 4.3, [0.6, 0.4], rh=0.48, size=13)
    rs = [["Restrição", "Valor", "Limite", "Folga", "Estado"],
          ["Área de convés [m²]", "12.499", "≥ 11.563", "8,1%", ""], ["GM_{T} [m]", "4,000", "1 a 4", "0,0%", "ativa"],
          ["T_{n} [s]", "21,85", "> 20", "9,2%", ""], ["Lastro [t]", "11", "> 0", "≈ 0", "ativa"],
          ["V_{lastro}/V_{pontoons}", "0,000", "≤ 0,9", "100%", ""], ["b_{c} [m]", "12,55", "≤ 13,40", "6,3%", ""],
          ["Air gap [m]", "25,84", "≥ 6,65", "288%", ""], ["min A/B", "1,303", "≥ 1,3", "0,2%", "ativa"],
          ["GZ > 0 até φ_{al}", "sim", "–", "–", ""]]
    cores = {(i, 4): ORANGE for i in (2, 4, 8)}
    tabela(s, rs, 5.2, 1.75, 7.65, [0.34, 0.15, 0.17, 0.16, 0.18], rh=0.45, size=13, cores=cores)
    texto(s, 0.6, 4.85, 4.3, 1.9, "As tabelas completas dos três cenários estão em resultados/restricoes_*.csv.",
          size=13, color=SUB)

    sec = "Sensibilidade"
    s_justificativa(d, "Solução final")
    s_sensibilidade(d, sec)

    sec = "Conclusões"
    s = d.slide("Conclusões", "O que o modelo mostra sobre o projeto da semissubmersível do KZ-2026-B", sec)
    bullets(s, 0.7, 1.75, 7.6, 5.0, [
        "O modelo cobre os 8 itens do enunciado e reproduz as aulas com erro de até 3,7%",
        "Só 1,1% do domínio é viável; o critério de áreas é a restrição mais seletiva",
        "O projeto é governado pela estabilidade: GM_{T} = 4 m e A/B = 1,30 ativos em todos os ótimos; air gap e T_{n} têm folga",
        "A fronteira tem duas famílias, rasa e larga e compacta e profunda, separadas perto de 14.000 t",
        "A solução escolhida fica no ponto a partir do qual reduzir o heave custa 3× mais peso"], size=19, espaco=14)
    for i, (r, v, c) in enumerate([("Peso do casco", "14.998 t", ORANGE), ("H_{1/3,z} · T_{n}", "1,55 m · 21,8 s", NAVY),
                                   ("L_{p} · T", "111,8 · 24,0 m", BLUE), ("A/B · GM_{T}", "1,303 · 4,00 m", TEAL)]):
        kpi(s, 8.7, 1.75 + i * 1.25, 4.15, 1.12, r, v, c, 24)

    s = d.slide("Limitações e próximos passos", "Pontos a confirmar antes de uma fase seguinte do projeto", sec)
    bullets(s, 0.7, 1.75, 6.0, 5.0, [
        "**Limitações do modelo**",
        (1, "GZ 2D sem o volume do deck box; curva sem significado após φ_{al}"),
        (1, "Air gap sem roll, pitch, fase onda × heave e efeitos não lineares"),
        (1, "Heave linear desacoplado, sem amarração; C_{A} 2D de retângulo"),
        (1, "Pesos por correlações (planta, convés, risers, amarração)")], size=17)
    bullets(s, 6.9, 1.75, 6.0, 5.0, [
        "**Próximos passos**",
        (1, "Confirmar se o gás entra no BOE (+25% no casco)"),
        (1, "Fundamentar h_{d} e h_{m} com o pôster de semissubmersíveis"),
        (1, "Adotar lastro mínimo para ajuste de calado e trim (+7%)"),
        (1, "Validar com uma plataforma real e verificar a inclinação de 14° sob tempestade"),
        (1, "Air gap pela DNVGL-OTG-13")], size=17)

    d.fecho("Obrigado", ["Perguntas?", "Código, resultados e relatório: github.com/gustavogsilvaa/PNV3425-Projeto-de-Sistemas-Oceanicos"])
    return d


# ---------------------------------------------------------------------------
# Versão de 15 minutos
# ---------------------------------------------------------------------------
def focada():
    d = Deck("PNV3425 – Projeto de Sistemas Oceânicos · Trabalho Final")
    d.capa("Trabalho Final", "Projeto paramétrico de uma semissubmersível",
           ["Bloco KZ-2026-B · bacia do Baixo Congo (Angola) · lâmina d'água de 1.450 m",
            "Otimização multiobjetivo: peso estrutural do casco × altura significativa de heave",
            "PNV3425 – Projeto de Sistemas Oceânicos · Escola Politécnica da USP · 2º semestre de 2026"],
           notas="[0:30] Apresentar o grupo e o objetivo: dimensionar a semissubmersível do bloco KZ-2026-B "
                 "minimizando ao mesmo tempo o peso do casco e o heave, com todas as restrições do enunciado.")

    s_campo_resumo(d, "Problema", notas=(
        "[1:00] Campo em 1.450 m de lâmina d'água. A planta é dimensionada pelo pico de óleo, 158.894 bpd entre "
        "os anos 5 e 7. Isso fixa a área mínima de convés (Lp de pelo menos 107,5 m) e um topside de 22.420 t. "
        "Mar de 100 anos brando: Hs = 5,6 m e Tp = 15,2 s."))

    s_geometria(d, "Modelo", compacto=True, notas=(
        "[1:15] Seis variáveis. Para cada combinação o modelo encadeia os Exercícios 7 a 10: hidrostática, "
        "pesos e GM, curva GZ 2D e critério de vento, heave com RAO e espectro, e o air gap mínimo. "
        "Uma avaliação leva cerca de 6 ms, o que permite avaliar dezenas de milhares de cascos."))

    s_validacao(d, "Validação", notas=(
        "[1:00] Antes de otimizar, aplicamos o modelo à plataforma dos exercícios. Tn e Hs de heave batem "
        "exatamente; o A/B fica até 3,7% abaixo da aula, ou seja, do lado conservador. "
        "As verificações internas confirmam a coerência entre GZ e GM e o limite RAO = 1."))

    s_otimizacao(d, "Otimização", notas=(
        "[1:15] 20.000 amostras de hipercubo latino; só 227 são viáveis, e o critério de vento é o que mais "
        "reprova. A partir delas, soma ponderada com SLSQP e, como a fronteira é não convexa, o método "
        "ε-restrito para preencher os vazios. O filtro de não dominância deixa 25 pontos."))

    s_pareto(d, "Otimização", extra=True, notas=(
        "[1:30] A fronteira vai de 10.346 t a 23.634 t. Ponto principal: em todos os 25 ótimos o GM está no "
        "máximo de 4 m e o A/B no mínimo de 1,30. O projeto é governado pela estabilidade; air gap e Tn têm folga."))

    s_ficha(d, "Cenários", notas=(
        "[1:30] Cenário 1: semi rasa, mais leve, mas com heave de 42% do Hs e ângulo de alagamento de só 9°. "
        "Cenário 2: calado de 40 m, heave de 19% do Hs, porém 2,3 vezes mais pesado. "
        "Os dois extremos encostam nos limites do domínio; a solução 3 é a única no interior."))

    s_final_dim(d, "Solução final", notas=(
        "[1:00] Solução escolhida: Lp = 111,8 m, T = 24 m, casco de 14.998 t. O KG alto vem do topside, "
        "e o GM de 4 m é obtido pelo BM de 39 m. Ponto fraco: lastro praticamente nulo."))

    s_final_gz(d, "Solução final", com_tabela=True, notas=(
        "[1:30] Critério atendido nos quatro casos; o crítico é a tempestade no plano transversal, A/B = 1,303. "
        "A face inferior do convés gera 3,2 vezes o momento das outras parcelas, o que segura o Lp perto do mínimo. "
        "Sob tempestade a plataforma inclina 14°, valor a verificar em fases seguintes."))

    s_final_heave(d, "Solução final", compacto=True, notas=(
        "[1:15] Tn = 21,85 s. A força de excitação se anula logo acima de ωn, o que corta a ressonância: "
        "o RAO máximo é 1,47 e, no pico do mar, 0,32. Hs de heave de 1,55 m. "
        "O air gap tem 19 m de folga: a altura das colunas vem do critério de vento, não da onda."))

    s_justificativa(d, "Escolha", notas=(
        "[1:00] Por que este ponto: até ele, cada milímetro de heave custa 5,7 t; depois, 17 t. "
        "Além disso é a única solução no interior do domínio e tem φal de 21,6°."))

    s_sensibilidade(d, "Sensibilidade", notas=(
        "[1:00] A solução está ajustada às restrições ativas: com geometria fixa, mudar hd ou hm a torna inviável. "
        "Reotimizando, hm = 15 m custa 5% e lastro mínimo de 10% custa 7%. "
        "A hipótese de maior impacto é incluir o gás: +25% no casco."))

    s = d.slide("Conclusões e próximos passos", "Síntese do projeto do KZ-2026-B", "Conclusões", notas=(
        "[0:45] Fechar com a solução escolhida e os próximos passos: confirmar o gás, fundamentar hd e hm, "
        "adotar lastro mínimo e validar com uma plataforma real."))
    bullets(s, 0.7, 1.75, 7.6, 5.0, [
        "Modelo validado contra as aulas (erro ≤ 3,7%) cobrindo os 8 itens do enunciado",
        "Projeto governado pela estabilidade: GM_{T} = 4 m e A/B = 1,30 ativos em todos os ótimos",
        "Solução escolhida no joelho: depois dela, reduzir heave custa 3× mais peso",
        "**Próximos passos:** confirmar o gás no BOE, fundamentar h_{d}/h_{m}, adotar lastro mínimo, "
        "validar com plataforma real"], size=20, espaco=16)
    for i, (r, v, c) in enumerate([("Peso do casco", "14.998 t", ORANGE), ("H_{1/3,z} · T_{n}", "1,55 m · 21,8 s", NAVY),
                                   ("L_{p} · T", "111,8 · 24,0 m", BLUE), ("A/B · GM_{T}", "1,303 · 4,00 m", TEAL)]):
        kpi(s, 8.7, 1.75 + i * 1.25, 4.15, 1.12, r, v, c, 24)

    d.fecho("Obrigado", ["Perguntas?", "Código, resultados e relatório: github.com/gustavogsilvaa/PNV3425-Projeto-de-Sistemas-Oceanicos"])
    return d


if __name__ == "__main__":
    completa().salvar(os.path.join(AQUI, "PNV3425_G02_apresentacao_completa.pptx"))
    focada().salvar(os.path.join(AQUI, "PNV3425_G02_apresentacao_15min.pptx"))
