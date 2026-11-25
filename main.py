"""Programa principal: coleta de valores em uma matriz 3D (guloso e backtracking).

Exemplos:
  py main.py guloso       --inicio 0 0 0 --fim 99 99 99 --semente 42
  py main.py guloso       --inicio 0 0 0 --fim 99 99 99 --semente 42 --estrategia direcionado
  py main.py backtracking --inicio 10 10 10 --fim 20 20 20 --semente 42 --tempo-limite 10
  py main.py ambos        --inicio 0 0 0 --fim 5 5 5 --semente 7
"""

import argparse
import csv
import sys
import time

from backtracking import LIMITE_COLETAS, coleta_backtracking
from guloso import ESTRATEGIAS, LIMITE_ITENS, LIMITE_VALOR_NEGATIVO, coleta_gulosa
from matriz import Matriz3D, distancia_manhattan, validar_caminho


def _resumo_caminho(matriz, caminho, mostrar):
    if not caminho:
        return "  (nenhum caminho)"
    def fmt(p):
        return f"{p}={matriz.valor(*p)}"
    if len(caminho) <= 2 * mostrar:
        return "  " + " -> ".join(fmt(p) for p in caminho)
    ini = " -> ".join(fmt(p) for p in caminho[:mostrar])
    fim = " -> ".join(fmt(p) for p in caminho[-mostrar:])
    return f"  {ini} -> ... ({len(caminho) - 2 * mostrar} posições) ... -> {fim}"


def _salvar_csv(arquivo, matriz, caminho):
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["passo", "x", "y", "z", "valor", "acumulado"])
        acumulado = 0
        for i, (x, y, z) in enumerate(caminho, start=1):
            acumulado += matriz.valor(x, y, z)
            w.writerow([i, x, y, z, matriz.valor(x, y, z), acumulado])
    print(f"  Caminho salvo em: {arquivo}")


def executar_guloso(matriz, args):
    print(f"\n=== ALGORITMO GULOSO (estratégia: {args.estrategia}) ===")
    t0 = time.perf_counter()
    r = coleta_gulosa(matriz, args.inicio, args.fim, estrategia=args.estrategia,
                      limite_itens=args.limite_itens,
                      limite_negativo=args.limite_negativo)
    dt = time.perf_counter() - t0
    print(f"  Itens coletados : {r.quantidade}")
    print(f"  Valor coletado  : {r.total}")
    print(f"  Motivo da parada: {r.motivo_parada}")
    print(f"  Chegou ao fim?  : {'sim' if r.chegou_ao_destino else 'não'}")
    print(f"  Posição final   : {r.caminho[-1]}")
    problemas = validar_caminho(matriz, r.caminho, args.inicio)
    print(f"  Caminho válido? : {'sim (sem repetições)' if not problemas else problemas}")
    print(f"  Tempo           : {dt:.3f} s")
    print("  Caminho:")
    print(_resumo_caminho(matriz, r.caminho, args.mostrar))
    if args.salvar:
        _salvar_csv(args.salvar.replace(".csv", "") + "_guloso.csv", matriz, r.caminho)
    return r


def executar_backtracking(matriz, args):
    lim = "sem limite" if args.tempo_limite is None else f"{args.tempo_limite} s"
    print(f"\n=== BACKTRACKING (máx. {args.limite_coletas} coletas, tempo limite: {lim}) ===")
    r = coleta_backtracking(matriz, args.inicio, args.fim,
                            limite_coletas=args.limite_coletas,
                            tempo_limite=args.tempo_limite)
    if not r.caminho:
        print("  Não existe caminho: a distância até o destino exige mais coletas "
              "do que o limite permite.")
        return r
    print(f"  Itens coletados : {r.quantidade}")
    print(f"  Maior valor     : {r.total}")
    print(f"  Ótimo garantido?: "
          f"{'sim (busca completa)' if r.otimo_garantido else 'NÃO (tempo limite esgotado - melhor encontrado)'}")
    print(f"  Nós explorados  : {r.nos_explorados}")
    print(f"  Podas viabilid. : {r.podas_viabilidade}")
    print(f"  Podas limitante : {r.podas_limitante}")
    print(f"  Melhorias       : {r.solucoes_melhoradas}")
    problemas = validar_caminho(matriz, r.caminho, args.inicio, args.fim)
    print(f"  Caminho válido? : {'sim (sem repetições, termina no fim)' if not problemas else problemas}")
    print(f"  Tempo           : {r.tempo_segundos:.3f} s")
    print("  Caminho:")
    print(_resumo_caminho(matriz, r.caminho, args.mostrar))
    if args.salvar:
        _salvar_csv(args.salvar.replace(".csv", "") + "_backtracking.csv", matriz, r.caminho)
    return r


def criar_parser():
    p = argparse.ArgumentParser(description="Coleta de valores em matriz 3D.")
    p.add_argument("algoritmo", choices=["guloso", "backtracking", "ambos"])
    p.add_argument("--inicio", nargs=3, type=int, required=True, metavar=("X", "Y", "Z"))
    p.add_argument("--fim", nargs=3, type=int, required=True, metavar=("X", "Y", "Z"))
    p.add_argument("--n", type=int, default=100, help="tamanho de cada eixo (padrão 100)")
    p.add_argument("--semente", type=int, default=None,
                   help="semente do gerador aleatório (mesma semente = mesma matriz)")
    p.add_argument("--estrategia", choices=ESTRATEGIAS, default="valor",
                   help="estratégia do guloso (padrão: valor)")
    p.add_argument("--limite-itens", type=int, default=LIMITE_ITENS)
    p.add_argument("--limite-negativo", type=int, default=LIMITE_VALOR_NEGATIVO)
    p.add_argument("--limite-coletas", type=int, default=LIMITE_COLETAS)
    p.add_argument("--tempo-limite", type=float, default=30.0,
                   help="segundos para o backtracking (padrão 30; 0 = sem limite)")
    p.add_argument("--mostrar", type=int, default=5,
                   help="quantas posições do início/fim do caminho exibir")
    p.add_argument("--salvar", metavar="ARQUIVO.csv",
                   help="salva o(s) caminho(s) completo(s) em CSV")
    return p


def main(argv=None):
    args = criar_parser().parse_args(argv)
    args.inicio, args.fim = tuple(args.inicio), tuple(args.fim)
    if args.tempo_limite is not None and args.tempo_limite <= 0:
        args.tempo_limite = None

    t0 = time.perf_counter()
    matriz = Matriz3D.aleatoria(args.n, args.semente)
    print(f"Matriz {args.n}x{args.n}x{args.n} gerada (semente={args.semente}) "
          f"em {time.perf_counter() - t0:.2f} s")
    try:
        matriz.validar_coordenada(args.inicio, "coordenada inicial")
        matriz.validar_coordenada(args.fim, "coordenada final")
    except ValueError as e:
        print(f"ERRO: {e}")
        return 2
    print(f"Início {args.inicio} (valor {matriz.valor(*args.inicio)}) | "
          f"Fim {args.fim} (valor {matriz.valor(*args.fim)}) | "
          f"distância mínima: {distancia_manhattan(args.inicio, args.fim)} passos")

    if args.algoritmo in ("guloso", "ambos"):
        executar_guloso(matriz, args)
    if args.algoritmo in ("backtracking", "ambos"):
        executar_backtracking(matriz, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
