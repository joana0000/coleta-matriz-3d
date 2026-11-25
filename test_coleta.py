"""Plano de testes automatizado.  Executar com:  py -m unittest -v test_coleta"""

import random
import unittest

from backtracking import coleta_backtracking
from guloso import (MOTIVO_DESTINO, MOTIVO_LIMITE_ITENS, MOTIVO_LIMITE_NEGATIVO,
                    MOTIVO_SEM_SAIDA, coleta_gulosa)
from matriz import Matriz3D, distancia_manhattan, validar_caminho


def linha(valores):
    """Matriz 'linha' N x 1 x 1 - útil para forçar situações exatas."""
    return Matriz3D(len(valores), 1, 1, list(valores))


def forca_bruta(matriz, inicio, fim, limite):
    """Enumera TODOS os caminhos simples sem nenhuma poda (referência de correção)."""
    melhor = [None]
    caminho = [inicio]
    vis = {inicio}

    def dfs(atual, soma):
        if atual == fim:
            if melhor[0] is None or soma > melhor[0]:
                melhor[0] = soma
            return
        if len(caminho) == limite:
            return
        for v in matriz.vizinhos(*atual):
            if v not in vis:
                vis.add(v); caminho.append(v)
                dfs(v, soma + matriz.valor(*v))
                caminho.pop(); vis.remove(v)

    dfs(inicio, matriz.valor(*inicio))
    return melhor[0]


class TestMatriz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grande = Matriz3D.aleatoria(100, semente=42)

    def test_M01_dimensao_e_intervalo(self):
        self.assertEqual(len(self.grande.valores), 1_000_000)
        self.assertGreaterEqual(min(self.grande.valores), -100)
        self.assertLessEqual(max(self.grande.valores), 100)

    def test_M02_semente_reproduzivel(self):
        a = Matriz3D.aleatoria(10, semente=1)
        b = Matriz3D.aleatoria(10, semente=1)
        self.assertEqual(a.valores, b.valores)

    def test_M03_valor_fora_do_intervalo(self):
        with self.assertRaises(ValueError):
            Matriz3D(1, 1, 2, [0, 101])

    def test_M04_coordenada_invalida(self):
        with self.assertRaises(ValueError):
            coleta_gulosa(self.grande, (0, 0, 0), (100, 0, 0))
        with self.assertRaises(ValueError):
            coleta_backtracking(self.grande, (-1, 0, 0), (5, 5, 5))

    def test_M05_vizinhos_canto_e_centro(self):
        self.assertEqual(len(self.grande.vizinhos(0, 0, 0)), 3)
        self.assertEqual(len(self.grande.vizinhos(50, 50, 50)), 6)


class TestGuloso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grande = Matriz3D.aleatoria(100, semente=42)

    def test_G01_inicio_igual_ao_fim(self):
        r = coleta_gulosa(self.grande, (5, 5, 5), (5, 5, 5))
        self.assertEqual(r.quantidade, 1)
        self.assertEqual(r.motivo_parada, MOTIVO_DESTINO)
        self.assertEqual(r.total, self.grande.valor(5, 5, 5))

    def test_G02_escolhe_vizinho_de_maior_valor(self):
        # 3x3x1: a partir do centro (1,1,0) o maior vizinho é (2,1,0)=90
        m = Matriz3D.de_lista_3d([
            [[0], [10], [0]],
            [[20], [0], [30]],
            [[0], [90], [0]],
        ])
        r = coleta_gulosa(m, (1, 1, 0), (0, 0, 0))
        self.assertEqual(r.caminho[1], (2, 1, 0))

    def test_G03_sem_repeticao_matriz_100(self):
        for estrategia in ("valor", "direcionado"):
            r = coleta_gulosa(self.grande, (0, 0, 0), (99, 99, 99), estrategia)
            self.assertEqual(validar_caminho(self.grande, r.caminho, (0, 0, 0)), [])
            self.assertLessEqual(r.quantidade, 2000)
            self.assertEqual(r.total, sum(self.grande.valor(*p) for p in r.caminho))

    def test_G04_para_em_2000_itens(self):
        m = linha([1] * 3000)                       # destino no índice 2999
        r = coleta_gulosa(m, (0, 0, 0), (2999, 0, 0))
        self.assertEqual(r.quantidade, 2000)
        self.assertEqual(r.total, 2000)
        self.assertEqual(r.motivo_parada, MOTIVO_LIMITE_ITENS)

    def test_G05_para_em_menos_2000(self):
        m = linha([-100] * 3000)
        r = coleta_gulosa(m, (0, 0, 0), (2999, 0, 0))
        self.assertEqual(r.quantidade, 20)          # 20 x (-100) = -2000
        self.assertEqual(r.total, -2000)
        self.assertEqual(r.motivo_parada, MOTIVO_LIMITE_NEGATIVO)

    def test_G06_ultrapassa_menos_2000(self):
        m = linha([-99] * 3000)                     # nunca dá exatamente -2000
        r = coleta_gulosa(m, (0, 0, 0), (2999, 0, 0))
        self.assertEqual(r.quantidade, 21)          # -2079 <= -2000
        self.assertEqual(r.motivo_parada, MOTIVO_LIMITE_NEGATIVO)

    def test_G07_destino_tem_prioridade_no_item_2000(self):
        m = linha([1] * 2000)                       # o 2000º item é o destino
        r = coleta_gulosa(m, (0, 0, 0), (1999, 0, 0))
        self.assertEqual(r.quantidade, 2000)
        self.assertEqual(r.motivo_parada, MOTIVO_DESTINO)

    def test_G08_destino_tem_prioridade_no_menos_2000(self):
        m = linha([-100] * 20)                      # destino coincide com -2000
        r = coleta_gulosa(m, (0, 0, 0), (19, 0, 0))
        self.assertEqual(r.total, -2000)
        self.assertEqual(r.motivo_parada, MOTIVO_DESTINO)

    def test_G09_beco_sem_saida(self):
        # início no índice 2: vai para 1 (50), depois 0, e fica preso
        m = linha([0, 50, 0, 0, -100])
        r = coleta_gulosa(m, (2, 0, 0), (4, 0, 0))
        self.assertEqual(r.caminho, [(2, 0, 0), (1, 0, 0), (0, 0, 0)])
        self.assertEqual(r.motivo_parada, MOTIVO_SEM_SAIDA)

    def test_G10_direcionado_sempre_chega(self):
        for fim in [(99, 99, 99), (50, 0, 73), (0, 99, 0)]:
            r = coleta_gulosa(self.grande, (0, 0, 0), fim, "direcionado")
            self.assertEqual(r.motivo_parada, MOTIVO_DESTINO)
            self.assertEqual(r.quantidade, distancia_manhattan((0, 0, 0), fim) + 1)

    def test_G11_vai_ao_destino_quando_vizinho(self):
        m = Matriz3D.de_lista_3d([[[0], [-100]], [[100], [0]]])
        r = coleta_gulosa(m, (0, 0, 0), (0, 1, 0))  # destino vale -100, vizinho vale 100
        self.assertEqual(r.caminho, [(0, 0, 0), (0, 1, 0)])


class TestBacktracking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grande = Matriz3D.aleatoria(100, semente=42)

    def test_B01_igual_a_forca_bruta(self):
        # matrizes pequenas: o backtracking deve achar exatamente o ótimo
        casos = [(3, 3, 2, s) for s in range(5)] + [(2, 2, 3, s) for s in range(5)]
        for nx, ny, nz, s in casos:
            rng = random.Random(s)
            m = Matriz3D(nx, ny, nz, [rng.randint(-100, 100) for _ in range(nx * ny * nz)])
            fim = (nx - 1, ny - 1, nz - 1)
            for limite in (4, 7, 1000):
                esperado = forca_bruta(m, (0, 0, 0), fim, limite)
                r = coleta_backtracking(m, (0, 0, 0), fim, limite_coletas=limite)
                with self.subTest(dims=(nx, ny, nz), semente=s, limite=limite):
                    self.assertTrue(r.otimo_garantido)
                    self.assertEqual(r.total, esperado)
                    if r.caminho:
                        self.assertEqual(validar_caminho(m, r.caminho, (0, 0, 0), fim), [])
                        self.assertLessEqual(r.quantidade, limite)

    def test_B02_desvio_compensa(self):
        # 3x3x1: o caminho direto (0,0)->(0,1)->(0,2) vale -2; o desvio vale bem mais
        m = Matriz3D.de_lista_3d([
            [[1], [-100], [1]],
            [[50], [-100], [50]],
            [[50], [50], [50]],
        ])
        r = coleta_backtracking(m, (0, 0, 0), (0, 2, 0))
        self.assertEqual(r.total, 1 + 50 + 50 + 50 + 50 + 50 + 1)
        self.assertTrue(r.otimo_garantido)

    def test_B03_inicio_igual_ao_fim(self):
        r = coleta_backtracking(self.grande, (3, 3, 3), (3, 3, 3))
        self.assertEqual(r.caminho, [(3, 3, 3)])
        self.assertEqual(r.total, self.grande.valor(3, 3, 3))

    def test_B04_destino_inalcancavel_com_o_limite(self):
        r = coleta_backtracking(self.grande, (0, 0, 0), (99, 99, 99), limite_coletas=100)
        self.assertEqual(r.caminho, [])
        self.assertIsNone(r.total)

    def test_B05_matriz_100_respeita_regras(self):
        r = coleta_backtracking(self.grande, (0, 0, 0), (99, 99, 99), tempo_limite=3)
        self.assertEqual(validar_caminho(self.grande, r.caminho, (0, 0, 0), (99, 99, 99)), [])
        self.assertLessEqual(r.quantidade, 1000)
        self.assertEqual(r.total, sum(self.grande.valor(*p) for p in r.caminho))

    def test_B06_nunca_pior_que_guloso_direcionado(self):
        g = coleta_gulosa(self.grande, (10, 10, 10), (20, 20, 20), "direcionado")
        r = coleta_backtracking(self.grande, (10, 10, 10), (20, 20, 20), tempo_limite=2)
        self.assertGreaterEqual(r.total, g.total)

    def test_B07_limite_exato_de_coletas(self):
        # com limite = distância + 1 só existem caminhos "em linha reta"
        r = coleta_backtracking(self.grande, (0, 0, 0), (2, 2, 2), limite_coletas=7)
        self.assertEqual(r.quantidade, 7)
        self.assertTrue(r.otimo_garantido)


if __name__ == "__main__":
    unittest.main(verbosity=2)
