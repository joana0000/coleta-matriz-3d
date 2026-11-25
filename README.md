# Coleta de valores em matriz 3D — Guloso × Backtracking

Trabalho prático em Python 3 (sem bibliotecas externas): coleta de valores em uma matriz 100 × 100 × 100 com valores entre −100 e 100.

- **Parte 1 — Guloso** ([guloso.py](guloso.py)): para ao chegar à coordenada final, ao coletar 2000 itens ou quando a soma chega a −2000.
- **Parte 2 — Backtracking** ([backtracking.py](backtracking.py)): maior valor possível com no máximo 1000 coletas.

A documentação completa (explicação do código, exemplos de execução, plano de testes e limitações) está em [DOCUMENTACAO.md](DOCUMENTACAO.md).

## Como executar

```bash
py main.py guloso --inicio 0 0 0 --fim 99 99 99 --semente 42
py main.py backtracking --inicio 0 0 0 --fim 99 99 99 --semente 42
py -m unittest -v test_coleta
```

No Linux/macOS use `python3` no lugar de `py`.
