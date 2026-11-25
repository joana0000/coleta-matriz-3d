"""Parte 2 - Coleta com BACKTRACKING (maior valor possível).

Procura o caminho de `inicio` até `fim` que maximiza a soma dos valores coletados,
com no máximo 1000 coletas e sem repetir posições (caminho simples).

O backtracking explora os caminhos em profundidade: avança para um vizinho, continua
a busca a partir dele e, ao terminar, DESFAZ o passo (desmarca a posição) e tenta o
próximo vizinho. Para não explorar todos os caminhos possíveis (o que é inviável),
usa três técnicas de poda:

  1. Poda de viabilidade: se a distância até o destino é maior do que o número de
     coletas que ainda restam, o destino não pode mais ser alcançado -> volta.
  2. Poda por limitante (branch and bound): soma atual + o máximo que ainda daria
     para ganhar (soma dos maiores valores positivos da matriz, na quantidade de
     coletas restantes) <= melhor solução já encontrada -> volta.
  3. Solução inicial: o caminho do guloso "direcionado" é usado como primeira
     melhor solução, para que a poda 2 funcione desde o início.

Os vizinhos são testados do maior para o menor valor, para achar boas soluções cedo.
Como o problema é NP-difícil (variação do "caminho mais longo"), há um tempo limite
opcional: ao esgotá-lo, devolve a melhor solução encontrada até ali e informa que a
otimalidade NÃO foi comprovada.
"""

import sys
import time
from dataclasses import dataclass

from guloso import coleta_gulosa
from matriz import distancia_manhattan

LIMITE_COLETAS = 1000


class _TempoEsgotado(Exception):
    pass


@dataclass
class ResultadoBacktracking:
    caminho: list            # vazio se não existe caminho viável
    total: int | None
    otimo_garantido: bool    # True = a busca terminou, o valor é o máximo possível
    nos_explorados: int
    podas_viabilidade: int
    podas_limitante: int
    solucoes_melhoradas: int
    tempo_segundos: float

    @property
    def quantidade(self):
        return len(self.caminho)


def _prefixo_maiores_positivos(matriz, k):
    """prefixo[i] = soma dos i maiores valores positivos da matriz (i = 0..k)."""
    positivos = sorted((v for v in matriz.valores if v > 0), reverse=True)[:k]
    prefixo = [0] * (k + 1)
    for i in range(1, k + 1):
        prefixo[i] = prefixo[i - 1] + (positivos[i - 1] if i <= len(positivos) else 0)
    return prefixo


def coleta_backtracking(matriz, inicio, fim, limite_coletas=LIMITE_COLETAS,
                        tempo_limite=None, usar_solucao_inicial=True):
    inicio, fim = tuple(inicio), tuple(fim)
    matriz.validar_coordenada(inicio, "coordenada inicial")
    matriz.validar_coordenada(fim, "coordenada final")
    if limite_coletas < 1:
        raise ValueError("O limite de coletas deve ser pelo menos 1.")

    t0 = time.perf_counter()
    stats = {"nos": 0, "viab": 0, "lim": 0, "melhorias": 0}

    # Sem caminho possível: mesmo em linha reta são necessárias distância + 1 coletas.
    if distancia_manhattan(inicio, fim) + 1 > limite_coletas:
        return ResultadoBacktracking([], None, True, 0, 0, 0, 0,
                                     time.perf_counter() - t0)

    valor_fim = matriz.valor(*fim)
    prefixo = _prefixo_maiores_positivos(matriz, limite_coletas)
    nx, ny, nz = matriz.nx, matriz.ny, matriz.nz
    valores = matriz.valores
    fx, fy, fz = fim

    melhor = {"total": None, "caminho": []}
    if usar_solucao_inicial:
        g = coleta_gulosa(matriz, inicio, fim, estrategia="direcionado",
                          limite_itens=limite_coletas, limite_negativo=-10**9)
        melhor["total"], melhor["caminho"] = g.total, list(g.caminho)

    visitado = bytearray(nx * ny * nz)
    caminho = [inicio]
    visitado[matriz.indice(*inicio)] = 1
    prazo = None if tempo_limite is None else t0 + tempo_limite

    def limitante(soma, restantes):
        """Maior soma final que ainda seria possível (estimativa otimista)."""
        if valor_fim > 0:
            return soma + prefixo[restantes]
        return soma + valor_fim + prefixo[restantes - 1]

    def explorar(atual, soma):
        stats["nos"] += 1
        if prazo is not None and (stats["nos"] & 1023) == 0 \
                and time.perf_counter() > prazo:
            raise _TempoEsgotado

        # Caso base: chegou ao destino -> a coleta termina aqui.
        if atual == fim:
            if melhor["total"] is None or soma > melhor["total"]:
                melhor["total"], melhor["caminho"] = soma, list(caminho)
                stats["melhorias"] += 1
            return

        restantes = limite_coletas - len(caminho)   # coletas que ainda podem ser feitas
        if restantes <= 0:
            return
        # Poda 2 (limitante): nem no melhor cenário supera a melhor solução.
        if melhor["total"] is not None and limitante(soma, restantes) <= melhor["total"]:
            stats["lim"] += 1
            return

        x, y, z = atual
        candidatos = []
        for a, b, c in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z),
                        (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)):
            if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz:
                idx = (a * ny + b) * nz + c
                if visitado[idx]:
                    continue
                # Poda 1 (viabilidade): depois deste passo restam (restantes - 1)
                # coletas, que precisam cobrir a distância até o destino.
                if abs(a - fx) + abs(b - fy) + abs(c - fz) > restantes - 1:
                    stats["viab"] += 1
                    continue
                candidatos.append((valores[idx], idx, (a, b, c)))
        candidatos.sort(reverse=True)   # maior valor primeiro

        for v, idx, viz in candidatos:
            visitado[idx] = 1            # escolhe
            caminho.append(viz)
            explorar(viz, soma + v)      # explora
            caminho.pop()                # desfaz (backtrack)
            visitado[idx] = 0

    limite_antigo = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limite_antigo, limite_coletas + 1000))
    otimo = True
    try:
        explorar(inicio, matriz.valor(*inicio))
    except _TempoEsgotado:
        otimo = False
    finally:
        sys.setrecursionlimit(limite_antigo)

    return ResultadoBacktracking(
        caminho=melhor["caminho"],
        total=melhor["total"],
        otimo_garantido=otimo,
        nos_explorados=stats["nos"],
        podas_viabilidade=stats["viab"],
        podas_limitante=stats["lim"],
        solucoes_melhoradas=stats["melhorias"],
        tempo_segundos=time.perf_counter() - t0,
    )
