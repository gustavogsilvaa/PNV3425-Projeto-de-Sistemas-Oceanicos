# -*- coding: utf-8 -*-
"""
Extrai do código real os trechos citados no Apêndice A do relatório.

Os trechos são copiados sem nenhuma alteração para relatorio/trechos/*.py, e
o arquivo trechos/trechos.tex guarda, para cada um, o arquivo de origem e as
linhas inicial e final. Assim as listagens do relatório têm a mesma numeração
de linhas dos arquivos do repositório. Gera também o diff entre o código do
caso-base e o da condição de 10% de lastro (trechos/diff_lastro10.txt).

Uso (na pasta relatorio/):
    python gerar_trechos.py
"""
import ast
import difflib
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SAIDA = os.path.join(AQUI, "trechos")
BASE = "caso_base/codigo/pnv3425_grupo02.py"
L10 = "condicao_10pct_lastro/codigo/pnv3425_grupo02_condicao_10pct_lastro.py"

# (rótulo, arquivo, início, fim). Início e fim são nomes de objetos do nível
# superior do módulo (função, classe ou variável) ou "re:<regex>" para uma linha.
TRECHOS = [
    ("dados", BASE, "RHO", "INCLUIR_GAS"),
    ("cenario", BASE, "Cenario", "coef_altura"),
    ("hidrostatica", BASE, "hidrostatica", "hidrostatica"),
    ("pesos", BASE, "pesos", "pesos"),
    ("caixas", BASE, "caixas_2d", "_integrais_submersas"),
    ("equilibrio", BASE, "_volume_e_derivada", "curva_gz"),
    ("alagamento", BASE, "angulo_alagamento", "angulo_alagamento"),
    ("vento", BASE, "z_clr", "tabela_vento"),
    ("criterio", BASE, "criterio_areas", "estabilidade"),
    ("heave", BASE, "OMEGAS", "heave"),
    ("avaliar", BASE, "avaliar", "viavel"),
    ("lhs", BASE, "nao_dominados", "variacao_sistematica"),
    ("problema", BASE, "Problema", "_tarefa_slsqp"),
    ("somapond", BASE, "soma_ponderada", "soma_ponderada"),
    ("epsilon", BASE, "epsilon_restrito", "ponto_joelho"),
    ("fronteira", BASE, r"re:# Fronteira de Pareto = não dominados",
     r're:front\.to_csv\(os\.path\.join\(OUT_DIR, "fronteira_pareto\.csv"\)'),
]


def intervalos(arvore):
    """Linhas (início, fim) de cada nome definido no nível superior."""
    mapa = {}
    for no in arvore.body:
        ini = min([no.lineno] + [d.lineno for d in getattr(no, "decorator_list", [])])
        nomes = []
        if isinstance(no, (ast.FunctionDef, ast.ClassDef)):
            nomes = [no.name]
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                elems = alvo.elts if isinstance(alvo, ast.Tuple) else [alvo]
                nomes += [e.id for e in elems if isinstance(e, ast.Name)]
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            nomes = [no.target.id]
        for n in nomes:
            mapa[n] = (ini, no.end_lineno)
    return mapa


def linha(chave, linhas, mapa, lado):
    if chave.startswith("re:"):
        padrao = re.compile(chave[3:])
        achadas = [i + 1 for i, s in enumerate(linhas) if padrao.search(s)]
        if len(achadas) != 1:
            raise ValueError(f"padrão {chave!r} encontrado {len(achadas)} vezes")
        return achadas[0]
    return mapa[chave][0 if lado == "ini" else 1]


def tex_escape(s):
    return s.replace("_", r"\_").replace("%", r"\%")


def main():
    os.makedirs(SAIDA, exist_ok=True)
    cache = {}
    defs = ["% Gerado por gerar_trechos.py. Não editar à mão."]
    for rotulo, arq, k_ini, k_fim in TRECHOS:
        if arq not in cache:
            with open(os.path.join(RAIZ, arq), encoding="utf-8") as f:
                txt = f.read()
            cache[arq] = (txt.splitlines(), intervalos(ast.parse(txt)))
        linhas, mapa = cache[arq]
        ini, fim = linha(k_ini, linhas, mapa, "ini"), linha(k_fim, linhas, mapa, "fim")
        with open(os.path.join(SAIDA, rotulo + ".py"), "w", encoding="utf-8") as f:
            f.write("\n".join(linhas[ini - 1:fim]) + "\n")
        defs.append(f"\\trechodef{{{rotulo}}}{{{tex_escape(arq)}}}{{{ini}}}{{{fim}}}")
        print(f"{rotulo:13s} {arq}: linhas {ini}-{fim}")

    with open(os.path.join(RAIZ, BASE), encoding="utf-8") as f:
        a = f.read().splitlines()
    with open(os.path.join(RAIZ, L10), encoding="utf-8") as f:
        b = f.read().splitlines()
    diff = list(difflib.unified_diff(a, b, fromfile=BASE, tofile=L10, n=1, lineterm=""))
    with open(os.path.join(SAIDA, "diff_lastro10.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(diff) + "\n")
    print(f"diff caso-base x 10% de lastro: {len(diff)} linhas")

    with open(os.path.join(SAIDA, "trechos.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(defs) + "\n")


if __name__ == "__main__":
    main()
