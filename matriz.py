"""Matriz tridimensional usada pelos algoritmos guloso e backtracking.

Os valores ficam armazenados em uma lista "achatada" (1 dimensão) para economizar
memória: uma matriz 100x100x100 tem 1.000.000 de posições. A posição (x, y, z)
corresponde ao índice  (x * ny + y) * nz + z.

Coordenadas são baseadas em zero: em uma matriz 100x100x100 cada eixo vai de 0 a 99.
"""

import random

VALOR_MIN = -100
VALOR_MAX = 100

# Vizinhança de 6 direções: um passo em apenas um dos eixos por vez
# (não há movimento na diagonal).
DIRECOES = (
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
)


def distancia_manhattan(a, b):
    """Menor número de passos entre duas coordenadas (ignorando obstáculos)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


class Matriz3D:
    def __init__(self, nx, ny, nz, valores):
        if nx <= 0 or ny <= 0 or nz <= 0:
            raise ValueError("As dimensões da matriz devem ser positivas.")
        if len(valores) != nx * ny * nz:
            raise ValueError(
                f"Esperados {nx * ny * nz} valores, recebidos {len(valores)}."
            )
        for v in valores:
            if not isinstance(v, int) or v < VALOR_MIN or v > VALOR_MAX:
                raise ValueError(
                    f"Valor {v!r} fora do intervalo [{VALOR_MIN}, {VALOR_MAX}]."
                )
        self.nx, self.ny, self.nz = nx, ny, nz
        self.valores = list(valores)

    # ------------------------------------------------------------------ criação
    @classmethod
    def aleatoria(cls, n=100, semente=None):
        """Matriz n x n x n com inteiros aleatórios uniformes em [-100, 100].

        A mesma semente gera sempre a mesma matriz (reprodutibilidade dos testes).
        """
        rng = random.Random(semente)
        valores = [rng.randint(VALOR_MIN, VALOR_MAX) for _ in range(n * n * n)]
        return cls(n, n, n, valores)

    @classmethod
    def de_lista_3d(cls, dados):
        """Cria a matriz a partir de uma lista aninhada dados[x][y][z]."""
        nx, ny, nz = len(dados), len(dados[0]), len(dados[0][0])
        valores = []
        for x in range(nx):
            for y in range(ny):
                if len(dados[x][y]) != nz:
                    raise ValueError("Lista 3D irregular.")
                valores.extend(dados[x][y])
        return cls(nx, ny, nz, valores)

    # ------------------------------------------------------------------ acesso
    def dentro(self, x, y, z):
        return 0 <= x < self.nx and 0 <= y < self.ny and 0 <= z < self.nz

    def indice(self, x, y, z):
        return (x * self.ny + y) * self.nz + z

    def valor(self, x, y, z):
        return self.valores[(x * self.ny + y) * self.nz + z]

    def vizinhos(self, x, y, z):
        """Lista das coordenadas vizinhas (6 direções) que estão dentro da matriz."""
        resultado = []
        for dx, dy, dz in DIRECOES:
            a, b, c = x + dx, y + dy, z + dz
            if 0 <= a < self.nx and 0 <= b < self.ny and 0 <= c < self.nz:
                resultado.append((a, b, c))
        return resultado

    def validar_coordenada(self, coord, nome="coordenada"):
        if len(coord) != 3:
            raise ValueError(f"A {nome} deve ter 3 componentes (x, y, z).")
        if not self.dentro(*coord):
            raise ValueError(
                f"A {nome} {tuple(coord)} está fora da matriz "
                f"(x: 0..{self.nx - 1}, y: 0..{self.ny - 1}, z: 0..{self.nz - 1})."
            )

    def __repr__(self):
        return f"Matriz3D({self.nx}x{self.ny}x{self.nz})"


def validar_caminho(matriz, caminho, inicio, fim=None):
    """Confere se um caminho é válido. Devolve uma lista de problemas (vazia = OK).

    Regras: começa no início, cada passo é para um vizinho (6 direções),
    nenhuma posição se repete e (opcionalmente) termina no fim.
    """
    problemas = []
    if not caminho:
        return ["caminho vazio"]
    if tuple(caminho[0]) != tuple(inicio):
        problemas.append("o caminho não começa na coordenada inicial")
    if fim is not None and tuple(caminho[-1]) != tuple(fim):
        problemas.append("o caminho não termina na coordenada final")
    if len(set(caminho)) != len(caminho):
        problemas.append("há posições coletadas mais de uma vez")
    for i, pos in enumerate(caminho):
        if not matriz.dentro(*pos):
            problemas.append(f"posição {pos} fora da matriz")
        if i > 0 and distancia_manhattan(caminho[i - 1], pos) != 1:
            problemas.append(f"passo inválido de {caminho[i - 1]} para {pos}")
    return problemas
