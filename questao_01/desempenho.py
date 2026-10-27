"""
Medição de desempenho da Questão 1 em entradas pequena, média e grande.
Usa time.perf_counter() (tempo) e tracemalloc (pico de memória).
Rodar a partir da raiz:  python questao_01/desempenho.py
"""
from pathlib import Path

import pandas as pd

from modelo import carregar_dados
from brute_force import escolher_subconjunto, brute_force_otimizado
from genetic_algorithm import algoritmo_genetico, medir
from greedy import greedy_orcamento

if __name__ == "__main__":
    catalogo, config = carregar_dados("data/G777", "G777")
    linhas = []

    # Brute Force: o tempo explode com o número de SKUs (exponencial)
    for n in [4, 5, 6, 7]:
        sub = escolher_subconjunto(catalogo, config, n=n)
        (_, _, combos), t, m = medir(brute_force_otimizado, sub, config)
        linhas.append({"algoritmo": "Brute Force", "n_skus": n, "tempo_s": round(t, 4),
                       "memoria_kb": round(m, 1), "observacao": f"{combos} combinações"})

    # GA e Greedy: pequeno (10), médio (20) e grande (30 SKUs)
    for n in [10, 20, 30]:
        cat = catalogo.iloc[:n].reset_index(drop=True)
        (pol, _, hist), t, m = medir(algoritmo_genetico, cat, config, tam_pop=30, taxa_mutacao=0.10)
        linhas.append({"algoritmo": "Algoritmo Genético", "n_skus": n, "tempo_s": round(t, 4),
                       "memoria_kb": round(m, 1), "observacao": f"{len(hist)} gerações"})
        (_, _, _, esc), t, m = medir(greedy_orcamento, cat, pol, config)
        linhas.append({"algoritmo": "Greedy", "n_skus": n, "tempo_s": round(t, 4),
                       "memoria_kb": round(m, 1), "observacao": f"{len(esc)} degraus comprados"})

    tabela = pd.DataFrame(linhas)
    Path("questao_01/resultados").mkdir(parents=True, exist_ok=True)
    tabela.to_csv("questao_01/resultados/desempenho.csv", index=False)
    print(tabela.to_string(index=False))