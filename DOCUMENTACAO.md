# Coleta de Valores em Matriz 3D — Algoritmo Guloso e Backtracking

| Item | Informação |
|---|---|
| **Dupla** | `[NOME DO INTEGRANTE 1]` e `[NOME DO INTEGRANTE 2]` |
| **Linguagem** | Python 3 (testado no Python 3.14; requer 3.10 ou superior). Sem bibliotecas externas. |
| **Código-fonte** | https://github.com/joana0000/coleta-matriz-3d |

---

## 1. O problema

Uma matriz tridimensional de **100 × 100 × 100** (1.000.000 de posições) guarda em cada posição um inteiro entre **-100 e 100**. Partindo de uma coordenada inicial `(x1, y1, z1)`, é preciso coletar valores até uma coordenada final `(xf, yf, zf)`, sem coletar a mesma posição duas vezes.

- **Parte 1 — Guloso:** para a coleta quando (a) a coordenada final é encontrada, (b) 2000 itens foram coletados ou (c) o valor coletado chega a -2000.
- **Parte 2 — Backtracking:** no máximo 1000 coletas; determinar o **maior valor possível** do início até o fim.

### 1.1 Premissas adotadas

O enunciado não define alguns pontos. A dupla adotou estas premissas:

| # | Premissa | Justificativa |
|---|---|---|
| P1 | Movimento em **6 direções** (±x, ±y, ±z), um passo por vez, sem diagonais. | É a vizinhança usual em grade 3D: duas posições são vizinhas se diferem em 1 em um único eixo. |
| P2 | Coordenadas **começam em 0** (cada eixo vai de 0 a 99). | Padrão de índices em Python. |
| P3 | As posições **inicial e final também são coletadas** e contam como itens. | O caminho "coleta" tudo por onde passa. |
| P4 | "Chegar a -2000" significa **soma acumulada ≤ -2000**. | A soma pode pular de -1950 para -2049 sem passar por -2000 exatamente. |
| P5 | Ao alcançar a coordenada final, **a coleta termina** (o caminho não passa pelo fim para depois voltar). | Vale para as duas partes. |
| P6 | Se várias regras de parada valem ao mesmo tempo, a **coordenada final tem prioridade** ("independente de quantidade de itens coletados"). | Ex.: se o 2000º item é o destino, o motivo informado é "coordenada final encontrada". |
| P7 | A matriz é gerada aleatoriamente com distribuição uniforme; a opção `--semente` garante que a mesma matriz possa ser recriada. | Reprodutibilidade dos exemplos e testes. |

---

## 2. Estrutura do código

```
matriz.py         Classe Matriz3D: geração, acesso aos valores, vizinhos, validação
guloso.py         Parte 1 — algoritmo guloso
backtracking.py   Parte 2 — backtracking com podas (branch and bound)
main.py           Programa de linha de comando (CLI)
test_coleta.py    Testes automatizados (unittest) — 23 casos
```

### 2.1 Como executar

```powershell
# Parte 1 — guloso
py main.py guloso --inicio 0 0 0 --fim 99 99 99 --semente 42

# Parte 2 — backtracking (30 s de limite por padrão)
py main.py backtracking --inicio 0 0 0 --fim 99 99 99 --semente 42

# As duas, lado a lado, salvando os caminhos completos em CSV
py main.py ambos --inicio 10 10 10 --fim 20 20 20 --semente 42 --salvar exemplo.csv

# Testes
py -m unittest -v test_coleta
```

No Linux/macOS use `python3` no lugar de `py`.

| Opção | Padrão | Descrição |
|---|---|---|
| `--inicio X Y Z` / `--fim X Y Z` | obrigatório | coordenadas inicial e final |
| `--semente S` | aleatória | semente do gerador (mesma semente = mesma matriz) |
| `--n N` | 100 | tamanho de cada eixo (útil para testes com matrizes pequenas) |
| `--estrategia valor\|direcionado` | `valor` | estratégia do guloso (seção 3.2) |
| `--limite-itens` / `--limite-negativo` | 2000 / -2000 | regras de parada do guloso |
| `--limite-coletas` | 1000 | máximo de coletas do backtracking |
| `--tempo-limite SEG` | 30 | tempo máximo do backtracking; `0` = sem limite |
| `--mostrar K` | 5 | quantas posições do começo/fim do caminho exibir |
| `--salvar ARQ.csv` | — | grava o caminho completo (passo, x, y, z, valor, acumulado) |

---

## 3. Explicação detalhada do código

### 3.1 `matriz.py` — a matriz 3D

**Armazenamento.** Em vez de uma lista de listas de listas, os 1.000.000 de valores ficam em **uma única lista** ("achatada"). A posição `(x, y, z)` fica no índice:

```
indice = (x * ny + y) * nz + z
```

Isso usa menos memória e torna o acesso mais rápido, o que pesa no backtracking, que lê milhões de valores.

**Principais elementos:**

- `Matriz3D.aleatoria(n, semente)` — gera `n³` inteiros com `random.Random(semente).randint(-100, 100)`.
- `Matriz3D.de_lista_3d(dados)` — cria a matriz a partir de uma lista `dados[x][y][z]`. Os testes usam esta função para montar matrizes pequenas com valores escolhidos à mão.
- O construtor **valida** que todo valor é inteiro e está em [-100, 100] (senão lança `ValueError`).
- `vizinhos(x, y, z)` — devolve as até 6 posições vizinhas dentro dos limites. Um canto tem 3 vizinhos e uma posição interna tem 6.
- `validar_coordenada(...)` — rejeita coordenadas fora da matriz com mensagem clara.
- `distancia_manhattan(a, b)` = `|Δx| + |Δy| + |Δz|`: o menor número de passos entre duas posições com movimento em 6 direções.
- `validar_caminho(...)` — usada pelos testes e pela CLI. Confere se o caminho começa no início, (opcionalmente) termina no fim, não repete posições e só dá passos entre vizinhos.

### 3.2 `guloso.py` — Parte 1

**Ideia do algoritmo guloso:** em cada passo, faz a escolha que parece melhor **naquele momento** (ótimo local), olhando só para os vizinhos imediatos e **nunca desfazendo** uma escolha.

Pseudocódigo da função `coleta_gulosa`:

```
atual ← início
repita:
    coleta(atual)                 # adiciona ao caminho, marca como visitado, soma o valor
    se atual = fim                → para: "coordenada final encontrada"
    se itens coletados = 2000     → para: "limite de itens coletados atingido"
    se soma ≤ -2000               → para: "valor coletado chegou ao limite negativo"
    candidatos ← vizinhos de atual ainda não visitados
    se fim ∈ candidatos           → atual ← fim; continua
    (estratégia direcionado: mantém só candidatos que diminuem a distância ao fim)
    se candidatos vazio           → para: "beco sem saída"
    atual ← candidato de MAIOR valor (empate: o mais próximo do fim)
```

Pontos importantes:

1. **Nenhuma posição é coletada duas vezes.** O conjunto `visitado` (um `set` de tuplas, com consulta em O(1)) exclui posições já coletadas dos candidatos.
2. **Ordem das verificações.** As paradas são testadas logo depois de cada coleta, com o destino primeiro, o que implementa a prioridade da premissa P6.
3. **Destino à vista.** Se o fim é vizinho, o algoritmo vai até ele mesmo que valha menos que outro vizinho. Sem essa regra, o guloso poderia passar ao lado do destino e seguir em frente.
4. **Beco sem saída (parada extra).** Em 3D o guloso pode ficar cercado por posições que ele mesmo já coletou. O enunciado não prevê esse caso, então o programa para e informa o motivo, em vez de entrar em laço infinito.

**Duas estratégias de escolha:**

| Estratégia | Critério | Comportamento |
|---|---|---|
| `valor` (padrão) | maior valor entre os vizinhos não visitados | Guloso "puro". Coleta muito valor, mas **normalmente não chega ao destino**: vai atrás dos maiores valores e para em 2000 itens ou num beco sem saída. |
| `direcionado` | maior valor **entre os vizinhos que aproximam do destino** | Sempre chega ao destino, com exatamente `distância + 1` coletas. Coleta menos valor. |

**Complexidade:** cada passo examina no máximo 6 vizinhos, então são O(k) operações para k itens coletados (k ≤ 2000). A execução leva milissegundos; quase todo o tempo do programa é gasto gerando a matriz.

### 3.3 `backtracking.py` — Parte 2

**Objetivo:** entre todos os caminhos simples (sem repetição) do início até o fim com **no máximo 1000 posições**, achar o de **maior soma**.

**Ideia do backtracking** (função interna `explorar`):

```
explorar(atual, soma):
    se atual = fim:
        se soma > melhor: guarda este caminho como o melhor
        retorna                                  # a coleta termina no destino
    restantes ← 1000 − tamanho do caminho
    se restantes = 0: retorna
    PODA 2: se limitante(soma, restantes) ≤ melhor: retorna
    para cada vizinho v não visitado, do MAIOR para o menor valor:
        PODA 1: se distância(v, fim) > restantes − 1: pula v
        marca v; caminho.append(v)               # ESCOLHE
        explorar(v, soma + valor(v))             # EXPLORA
        caminho.pop(); desmarca v                # DESFAZ (backtrack)
```

O passo **escolhe → explora → desfaz** é o que caracteriza o backtracking: depois de testar um vizinho, a posição é desmarcada para poder fazer parte de outros caminhos.

O número de caminhos simples numa grade 3D cresce exponencialmente com o tamanho do caminho, então testar todos é inviável. Por isso o código usa três otimizações:

**Poda 1 — viabilidade.** Ao avançar para `v` sobram `restantes − 1` coletas. Se a distância de Manhattan de `v` até o fim é maior que isso, o destino não pode mais ser alcançado dentro do limite e o ramo é descartado.

**Poda 2 — limitante (*branch and bound*).** Calcula a maior soma que ainda seria possível no cenário mais otimista:

```
limitante = soma atual + (soma dos maiores valores positivos da matriz,
                          na quantidade de coletas restantes)
```

Se nem esse valor supera a melhor solução já conhecida, o ramo é descartado. Os maiores valores positivos são ordenados **uma única vez**, e a soma acumulada (`prefixo`) faz cada consulta custar O(1). Se o valor do destino é negativo, ele entra obrigatoriamente na conta, o que deixa o limitante mais justo. A estimativa nunca subestima o ganho possível, por isso a poda **não descarta a solução ótima**.

**Solução inicial.** Antes da busca, o guloso `direcionado` gera um caminho válido que serve como primeira "melhor solução". Assim a Poda 2 já funciona desde o começo e o programa **sempre** devolve uma resposta válida.

**Ordenação dos vizinhos.** Os vizinhos são testados do maior para o menor valor. Com isso, as primeiras soluções completas já são boas, o que fortalece a Poda 2.

**Tempo limite.** O problema é **NP-difícil** (é uma variante do "caminho simples mais longo"). Por isso há `--tempo-limite` (padrão 30 s). A cada 1024 nós o código consulta o relógio e, se o tempo acabou, lança uma exceção interna (`_TempoEsgotado`) que encerra a recursão. O resultado informa:

- `otimo_garantido = True` → a busca terminou: o valor **é comprovadamente o máximo possível**;
- `otimo_garantido = False` → o tempo acabou: o valor é **o melhor encontrado**, não necessariamente o máximo.

**Detalhes de implementação:**

- `visitado` é um `bytearray` de 1.000.000 de bytes (1 MB), indexado pela posição achatada. É mais rápido e econômico que um `set`.
- A profundidade de recursão chega a 1000 níveis, acima do limite padrão do Python. O código aumenta o limite (`sys.setrecursionlimit`) durante a busca e o restaura depois.
- Se `distância(início, fim) + 1 > limite de coletas`, não existe caminho e a função retorna na hora com caminho vazio.
- A busca guarda estatísticas: nós explorados, podas de cada tipo e quantas vezes a melhor solução foi melhorada.

### 3.4 `main.py` — linha de comando

Lê os argumentos com `argparse`, gera a matriz, valida as coordenadas (com mensagem de erro amigável), roda o(s) algoritmo(s) e mostra: itens coletados, valor, motivo da parada, se o caminho é válido, tempo e um resumo do caminho (`posição=valor`). Com `--salvar`, grava o caminho completo em CSV (separador `;`, abre direto no Excel).

---

## 4. Exemplos de execução e resultados

Todos os exemplos usam `--semente 42`. Com a mesma semente, a matriz e os resultados são os mesmos em qualquer computador. Os tempos dependem da máquina.

### Exemplo 1 — Guloso (valor) de um canto ao outro

```text
> py main.py guloso --inicio 0 0 0 --fim 99 99 99 --semente 42
Matriz 100x100x100 gerada (semente=42) em 0.40 s
Início (0, 0, 0) (valor 63) | Fim (99, 99, 99) (valor -56) | distância mínima: 297 passos

=== ALGORITMO GULOSO (estratégia: valor) ===
  Itens coletados : 2000
  Valor coletado  : 113946
  Motivo da parada: limite de itens coletados atingido
  Chegou ao fim?  : não
  Posição final   : (48, 17, 32)
  Caminho válido? : sim (sem repetições)
  Tempo           : 0.017 s
  Caminho:
  (0, 0, 0)=63 -> (1, 0, 0)=38 -> (2, 0, 0)=72 -> (2, 0, 1)=-31 -> (2, 0, 2)=78 -> ... (1990 posições) ... -> (49, 20, 32)=91 -> (49, 19, 32)=97 -> (48, 19, 32)=64 -> (48, 18, 32)=100 -> (48, 17, 32)=72
```

**Análise:** o guloso puro coleta muito valor, mas fica dando voltas atrás dos maiores valores e para no limite de 2000 itens sem chegar ao destino. É o comportamento típico de um algoritmo guloso: ótimo localmente, sem visão do objetivo global.

### Exemplo 2 — Guloso (direcionado), mesmo trajeto

```text
> py main.py guloso --inicio 0 0 0 --fim 99 99 99 --semente 42 --estrategia direcionado
=== ALGORITMO GULOSO (estratégia: direcionado) ===
  Itens coletados : 298
  Valor coletado  : 13881
  Motivo da parada: coordenada final encontrada
  Chegou ao fim?  : sim
  Posição final   : (99, 99, 99)
  Caminho válido? : sim (sem repetições)
  ...
  (0, 0, 0)=63 -> ... (288 posições) ... -> (99, 99, 98)=-58 -> (99, 99, 99)=-56
```

**Análise:** chega ao destino com o mínimo de passos (297 + 1 = 298 itens) e escolhe sempre o melhor vizinho entre os que aproximam do fim.

### Exemplo 3 — Guloso preso em beco sem saída

```text
> py main.py ambos --inicio 10 10 10 --fim 20 20 20 --semente 42 --tempo-limite 10 --salvar exemplo.csv
Início (10, 10, 10) (valor -57) | Fim (20, 20, 20) (valor 83) | distância mínima: 30 passos

=== ALGORITMO GULOSO (estratégia: valor) ===
  Itens coletados : 698
  Valor coletado  : 38522
  Motivo da parada: beco sem saída (todos os vizinhos já foram coletados)
  Chegou ao fim?  : não
  Posição final   : (10, 0, 11)
  ...
  Caminho salvo em: exemplo_guloso.csv

=== BACKTRACKING (máx. 1000 coletas, tempo limite: 10.0 s) ===
  Itens coletados : 999
  Maior valor     : 56305
  Ótimo garantido?: NÃO (tempo limite esgotado - melhor encontrado)
  Nós explorados  : 3250176
  Podas viabilid. : 8450616
  Podas limitante : 905276
  Melhorias       : 13
  Caminho válido? : sim (sem repetições, termina no fim)
  Tempo           : 10.001 s
  ...
  Caminho salvo em: exemplo_backtracking.csv
```

Trecho do CSV gerado (`exemplo_backtracking.csv`):

```text
passo;x;y;z;valor;acumulado
1;10;10;10;-57;-57
2;10;11;10;27;-30
3;10;11;11;29;-1
4;10;11;12;92;91
```

**Análise:** o guloso encostou na face y = 0 da matriz e ficou cercado pelas posições que já tinha coletado. O backtracking coletou 999 itens e não 1000 por causa da **paridade**: a grade 3D é bipartida e a distância até o destino é 30 (par), então qualquer caminho até lá tem número par de passos, ou seja, número ímpar de posições. 1000 posições é impossível nesse caso.

### Exemplo 4 — Backtracking na matriz 100³ com 1000 coletas

```text
> py main.py backtracking --inicio 0 0 0 --fim 99 99 99 --semente 42 --tempo-limite 30
=== BACKTRACKING (máx. 1000 coletas, tempo limite: 30.0 s) ===
  Itens coletados : 1000
  Maior valor     : 54845
  Ótimo garantido?: NÃO (tempo limite esgotado - melhor encontrado)
  Nós explorados  : 14555136
  Podas viabilid. : 9932437
  Podas limitante : 9588148
  Melhorias       : 15
  Caminho válido? : sim (sem repetições, termina no fim)
  Tempo           : 30.004 s
```

**Análise:** comparação com o guloso direcionado (13.881 no mesmo trajeto): o backtracking encontrou um caminho de **54.845**, cerca de 4 vezes mais, usando todas as 1000 coletas permitidas. Na matriz completa não é possível **provar** que esse é o máximo (ver seção 6).

### Exemplo 5 — Backtracking com ótimo comprovado

```text
> py main.py backtracking --inicio 50 50 50 --fim 52 51 50 --semente 42 --limite-coletas 12 --tempo-limite 0
=== BACKTRACKING (máx. 12 coletas, tempo limite: sem limite) ===
  Itens coletados : 12
  Maior valor     : 562
  Ótimo garantido?: sim (busca completa)
  Nós explorados  : 5550
  Podas viabilid. : 2948
  Podas limitante : 3714
  Melhorias       : 4
  Tempo           : 0.131 s
```

### Exemplo 6 — Guloso × Backtracking numa matriz 4×4×4

```text
> py main.py ambos --inicio 0 0 0 --fim 3 3 3 --n 4 --semente 7 --limite-coletas 20 --tempo-limite 0
=== ALGORITMO GULOSO (estratégia: valor) ===
  Itens coletados : 44
  Valor coletado  : 456
  Motivo da parada: coordenada final encontrada

=== BACKTRACKING (máx. 20 coletas, tempo limite: sem limite) ===
  Itens coletados : 20
  Maior valor     : 636
  Ótimo garantido?: sim (busca completa)
  Nós explorados  : 155650
```

**Análise:** com menos da metade das coletas (20 contra 44), o backtracking obteve um valor 39% maior que o guloso, e esse valor é comprovadamente o máximo.

### Exemplo 7 — Tratamento de erros

```text
> py main.py guloso --inicio 0 0 0 --fim 100 0 0 --semente 42
ERRO: A coordenada final (100, 0, 0) está fora da matriz (x: 0..99, y: 0..99, z: 0..99).

> py main.py backtracking --inicio 0 0 0 --fim 99 99 99 --semente 42 --limite-coletas 200
=== BACKTRACKING (máx. 200 coletas, tempo limite: 30.0 s) ===
  Não existe caminho: a distância até o destino exige mais coletas do que o limite permite.
```

---

## 5. Plano de testes

Testes automatizados em `test_coleta.py` (biblioteca padrão `unittest`). Comando: `py -m unittest -v test_coleta`.
**Resultado obtido: 23 testes executados, 23 aprovados (≈ 7 s).**

Para forçar situações exatas, alguns testes usam matrizes "linha" (N × 1 × 1) ou matrizes pequenas montadas à mão. Assim cada regra de parada pode ser provocada de forma controlada.

### 5.1 Matriz

| ID | Objetivo | Entrada | Resultado esperado | Status |
|---|---|---|---|---|
| M01 | Dimensão e intervalo | matriz 100³, semente 42 | 1.000.000 valores, todos em [-100, 100] | ✅ |
| M02 | Reprodutibilidade | duas matrizes com semente 1 | valores idênticos | ✅ |
| M03 | Valor inválido | valor 101 | `ValueError` | ✅ |
| M04 | Coordenada inválida | fim (100,0,0); início (-1,0,0) | `ValueError` no guloso e no backtracking | ✅ |
| M05 | Vizinhança | canto (0,0,0) e centro (50,50,50) | 3 e 6 vizinhos | ✅ |

### 5.2 Guloso

| ID | Objetivo | Entrada | Resultado esperado | Status |
|---|---|---|---|---|
| G01 | Início = fim | (5,5,5) → (5,5,5) | 1 item, motivo "coordenada final encontrada" | ✅ |
| G02 | Escolha gulosa | 3×3×1, vizinhos 10, 20, 30, 90 | segundo passo vai para o 90 | ✅ |
| G03 | Sem repetição | 100³, (0,0,0)→(99,99,99), as duas estratégias | caminho válido, ≤ 2000 itens, soma confere | ✅ |
| G04 | Parada em 2000 itens | linha de 3000 posições valendo 1 | 2000 itens, total 2000, motivo "limite de itens" | ✅ |
| G05 | Parada em -2000 (exato) | linha de 3000 posições valendo -100 | 20 itens, total -2000, motivo "limite negativo" | ✅ |
| G06 | Parada ao ultrapassar -2000 | linha de 3000 posições valendo -99 | 21 itens (-2079), motivo "limite negativo" | ✅ |
| G07 | Prioridade do destino (2000) | linha de 2000; o destino é o 2000º item | motivo "coordenada final encontrada" | ✅ |
| G08 | Prioridade do destino (-2000) | linha de 20 × (-100); destino no fim | total -2000, motivo "coordenada final encontrada" | ✅ |
| G09 | Beco sem saída | linha [0, 50, 0, 0, -100], início índice 2 | caminho 2→1→0, motivo "beco sem saída" | ✅ |
| G10 | Direcionado sempre chega | 100³, 3 destinos diferentes | chega com `distância + 1` itens | ✅ |
| G11 | Vai ao destino vizinho | destino vale -100, outro vizinho vale 100 | vai direto ao destino | ✅ |

### 5.3 Backtracking

| ID | Objetivo | Entrada | Resultado esperado | Status |
|---|---|---|---|---|
| B01 | **Correção do ótimo** | 10 matrizes aleatórias (3×3×2 e 2×2×3) × limites 4, 7, 1000 = 30 casos | mesmo valor de uma **força bruta sem podas** que enumera todos os caminhos | ✅ |
| B02 | Desvio compensa | 3×3×1 com "muro" de -100 no meio | soma 252 (contorna o muro) | ✅ |
| B03 | Início = fim | (3,3,3) → (3,3,3) | caminho de 1 posição | ✅ |
| B04 | Destino inalcançável | (0,0,0)→(99,99,99) com limite 100 | caminho vazio, total `None` | ✅ |
| B05 | Regras na matriz 100³ | (0,0,0)→(99,99,99), 3 s | válido, termina no fim, ≤ 1000 itens, soma confere | ✅ |
| B06 | Nunca pior que o guloso | (10,10,10)→(20,20,20), 2 s | total ≥ guloso direcionado | ✅ |
| B07 | Limite exato | (0,0,0)→(2,2,2), limite 7 | 7 itens, ótimo comprovado | ✅ |

O teste **B01** é o mais importante: compara o backtracking (com todas as podas) com uma implementação independente de força bruta. Se alguma poda descartasse a solução ótima, os valores seriam diferentes.

### 5.4 Testes manuais (via CLI)

| Caso | Comando | Verificado |
|---|---|---|
| Coordenada fora da matriz | `--fim 100 0 0` | mensagem de erro, código de saída 2 |
| Limite de coletas insuficiente | `--limite-coletas 200` em (0,0,0)→(99,99,99) | "Não existe caminho" |
| Exportação CSV | `--salvar exemplo.csv` | CSV com passo, x, y, z, valor, acumulado |
| Reprodutibilidade | mesmo comando duas vezes com `--semente 42` | saídas idênticas (exceto tempos) |

---

## 6. Limitações e erros conhecidos (situações que não funcionam)

1. **O backtracking não garante o ótimo na matriz 100×100×100 com 1000 coletas.** O problema é NP-difícil e o número de caminhos possíveis é astronômico. Com o tempo limite, o programa devolve a **melhor solução encontrada** e avisa `Ótimo garantido?: NÃO`. Mesmo sem tempo limite (`--tempo-limite 0`), a busca não terminaria em tempo viável (anos). O ótimo só é comprovado em matrizes pequenas ou com limites de coletas pequenos (Exemplos 5 e 6, teste B01).

2. **O limitante (Poda 2) é fraco em matrizes grandes.** Ele usa os maiores valores da matriz **inteira**. Numa matriz 100³ existem milhares de posições valendo 100, então a estimativa é quase sempre `soma + 100 × restantes`, e a poda só atua perto do fim da busca. Um limitante que considerasse só a região alcançável seria mais justo, porém mais caro de calcular.

3. **A busca explora sobretudo o final do caminho.** Por ser em profundidade, o backtracking passa a maior parte do tempo alterando as últimas posições do caminho. O começo do caminho quase não é revisto dentro do tempo limite, então melhorias que dependem de mudar o início raramente são encontradas.

4. **O guloso (estratégia `valor`) normalmente não chega ao destino** numa matriz aleatória: para em 2000 itens ou em beco sem saída (Exemplos 1 e 3). É uma limitação da própria abordagem gulosa, que não planeja. A estratégia `direcionado` resolve isso, mas coleta menos valor.

5. **Beco sem saída no guloso.** O enunciado não prevê esse caso. O programa para e informa "beco sem saída", sem atingir nenhuma das três condições do enunciado.

6. **A parada em -2000 é rara na prática.** Com valores uniformes em [-100, 100] e a escolha sempre pelo maior vizinho, a soma do guloso quase sempre cresce. Essa condição só foi provocada com matrizes construídas para isso (testes G05, G06, G08).

7. **Desempenho do Python.** A geração da matriz leva cerca de 0,4 a 0,7 s, e o backtracking explora em torno de 300 a 500 mil nós por segundo. Uma implementação em C/C++/Java exploraria mais nós no mesmo tempo, mas continuaria sem garantir o ótimo na matriz completa.

8. **Recursão profunda.** O backtracking chega a 1000 níveis de recursão. O limite do Python é aumentado automaticamente, mas com `--limite-coletas` muito alto (dezenas de milhares) pode haver estouro da pilha do sistema operacional e o programa pode fechar.

9. **Limite de coletas e paridade.** Quando a distância até o destino é par, o caminho sempre tem número ímpar de posições, e vice-versa. Por isso, às vezes o melhor caminho tem 999 coletas e não 1000 (Exemplo 3). Não é um erro, mas pode parecer que o limite não foi aproveitado.

10. **Matriz apenas aleatória pela CLI.** A linha de comando não carrega uma matriz de arquivo. Matrizes específicas só podem ser criadas pela API (`Matriz3D.de_lista_3d`), como nos testes.

11. **Memória.** A matriz 100³ guardada como lista de inteiros Python ocupa cerca de 8 MB de ponteiros (os inteiros pequenos são compartilhados). Matrizes com `--n` muito maior (por exemplo, 500, que daria 125 milhões de posições) podem esgotar a memória.

---

## 7. Conclusão

- O **guloso** é extremamente rápido (milissegundos) e fácil de implementar, mas toma decisões só com informação local. Na versão pura ele raramente chega ao destino; na versão direcionada chega, mas coleta pouco.
- O **backtracking** explora sistematicamente as alternativas (escolhe → explora → desfaz) e, com as podas de viabilidade e de limitante, encontra soluções muito melhores: cerca de 4 vezes o valor do guloso direcionado no mesmo trajeto. Em instâncias pequenas comprova o ótimo (validado contra força bruta). Na matriz completa o custo exponencial obriga a usar tempo limite.
