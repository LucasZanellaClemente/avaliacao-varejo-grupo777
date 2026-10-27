
# Desempenho — Questão 1

Medição com `time.perf_counter()` (tempo) e `tracemalloc` (pico de memória).
Script: `python questao_01/desempenho.py` → `questao_01/resultados/desempenho.csv`.

| Algoritmo   | SKUs         | Tempo (s)             | Observação          |
| ----------- | ------------ | --------------------- | --------------------- |
| Brute Force | 4            | 0,012                 | 1.536 combinações   |
| Brute Force | 5            | 0,055                 | 7.680 combinações   |
| Brute Force | 6            | 0,448                 | 53.760 combinações  |
| Brute Force | 7            | 3,191                 | 376.320 combinações |
| GA          | 10 / 20 / 30 | 0,12 / 0,18 / 0,56    | —                    |
| Greedy      | 10 / 20 / 30 | 0,002 / 0,003 / 0,004 | —                    |

Leitura: o Brute Force multiplica o tempo por ~7x a cada SKU adicional (crescimento
exponencial), enquanto GA e Greedy crescem de forma aproximadamente linear.

## Otimização antes/depois (Brute Force, 6 SKUs)

| Versão                                                                                            | Tempo  | Pico de memória |
| -------------------------------------------------------------------------------------------------- | ------ | ---------------- |
| Ingênua (recalcula tudo)                                                                          | 71,2 s | 56 KB            |
| Otimizada (pré-cálculo)                                                                          | 1,3 s  | 6 KB             |
| Ganho: ~55x, com resultado idêntico (verificado no teste `test_bf_otimizado_igual_ao_ingenuo`). |        |                  |

## Configurações do GA (catálogo completo)

| Configuração           | Caixa      | Gerações | Observação                              |
| ------------------------ | ---------- | ---------- | ----------------------------------------- |
| A: pop 30, mutação 10% | 433.958,55 | 348        | mais exploração, atingiu o ótimo       |
| B: pop 80, mutação 3%  | 432.911,29 | 128        | converge mais rápido, parou 0,24% abaixo |
