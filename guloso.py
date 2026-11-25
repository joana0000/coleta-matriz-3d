"""Parte 1 - Coleta com algoritmo GULOSO.

A cada passo o algoritmo olha apenas para os vizinhos da posição atual e escolhe o
que parece melhor naquele momento (a escolha local ótima), sem nunca voltar atrás.

Regras de parada (verificadas após cada coleta, nesta ordem de prioridade):
  1. a coordenada final foi alcançada (independe da quantidade coletada);
  2. foram coletados 2000 itens;
  3. o valor acumulado chegou a -2000 (soma <= -2000);
  4. (extra) não há vizinho não visitado para onde ir - beco sem saída.
"""

from dataclasses import dataclass

from matriz import distancia_manhattan

LIMITE_ITENS = 2000
LIMITE_VALOR_NEGATIVO = -2000

MOTIVO_DESTINO = "coordenada final encontrada"
MOTIVO_LIMITE_ITENS = "limite de itens coletados atingido"
MOTIVO_LIMITE_NEGATIVO = "valor coletado chegou ao limite negativo"
MOTIVO_SEM_SAIDA = "beco sem saída (todos os vizinhos já foram coletados)"

ESTRATEGIAS = ("valor", "direcionado")


@dataclass
class ResultadoGuloso:
    caminho: list
    total: int
    motivo_parada: str
    estrategia: str

    @property
    def quantidade(self):
        return len(self.caminho)

    @property
    def chegou_ao_destino(self):
        return self.motivo_parada == MOTIVO_DESTINO


def coleta_gulosa(matriz, inicio, fim, estrategia="valor",
                  limite_itens=LIMITE_ITENS,
                  limite_negativo=LIMITE_VALOR_NEGATIVO):
    """Executa a coleta gulosa de `inicio` até `fim`.

    estrategia:
      "valor"       -> vai para o vizinho não visitado de MAIOR valor
                       (empate: o mais próximo do destino). É o guloso "puro".
      "direcionado" -> só considera vizinhos que diminuem a distância até o
                       destino e, entre eles, escolhe o de maior valor.
                       Sempre chega ao destino, com distância + 1 coletas.
    Em ambas, se o destino for vizinho da posição atual, o algoritmo vai até ele.
    """
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"Estratégia inválida: {estrategia!r}. Use {ESTRATEGIAS}.")
    inicio, fim = tuple(inicio), tuple(fim)
    matriz.validar_coordenada(inicio, "coordenada inicial")
    matriz.validar_coordenada(fim, "coordenada final")

    visitado = set()
    caminho = []
    total = 0
    atual = inicio

    while True:
        # --- coleta a posição atual (cada posição só é coletada uma vez)
        caminho.append(atual)
        visitado.add(atual)
        total += matriz.valor(*atual)

        # --- critérios de parada
        if atual == fim:
            motivo = MOTIVO_DESTINO
            break
        if len(caminho) >= limite_itens:
            motivo = MOTIVO_LIMITE_ITENS
            break
        if total <= limite_negativo:
            motivo = MOTIVO_LIMITE_NEGATIVO
            break

        # --- candidatos: vizinhos ainda não coletados
        candidatos = [v for v in matriz.vizinhos(*atual) if v not in visitado]
        if fim in candidatos:
            atual = fim                       # destino à vista: vai direto
            continue
        if estrategia == "direcionado":
            d = distancia_manhattan(atual, fim)
            candidatos = [v for v in candidatos if distancia_manhattan(v, fim) < d]
        if not candidatos:
            motivo = MOTIVO_SEM_SAIDA
            break

        # --- escolha gulosa: maior valor; empate -> mais perto do destino
        atual = max(candidatos,
                    key=lambda v: (matriz.valor(*v), -distancia_manhattan(v, fim)))

    return ResultadoGuloso(caminho, total, motivo, estrategia)
