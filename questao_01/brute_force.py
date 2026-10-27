"""
Brute Force — Questão 1
Testa TODAS as combinações de níveis válidos para um subconjunto pequeno de SKUs
e devolve a política ótima (benchmark exato para validar o Algoritmo Genético).
"""
import itertools
import time
import tracemalloc

from modelo import carregar_dados, niveis_validos, avaliar_sku, avaliar_politica, PAUSA


def escolher_subconjunto(catalogo, config, n=6):
    """
    Escolhe os n primeiros SKUs que têm pelo menos 2 níveis de preço válidos
    (SKUs que só podem pausar não têm decisão a tomar).
    """
    indices = []
    for i in range(len(catalogo)):
        precos = [x for x in niveis_validos(catalogo.iloc[i], config) if x != PAUSA]
        if len(precos) >= 2:
            indices.append(i)
        if len(indices) == n:
            break
    return catalogo.iloc[indices].reset_index(drop=True)


def brute_force_ingenuo(catalogo, config, max_frac_aumento=0.50):
    """
    Versão 1 (antes): avalia cada combinação chamando avaliar_politica,
    que recalcula todos os SKUs do zero a cada combinação.
    """
    opcoes = [niveis_validos(catalogo.iloc[i], config) for i in range(len(catalogo))]
    melhor_niveis, melhor_caixa, testadas = None, float("-inf"), 0

    for combinacao in itertools.product(*opcoes):
        testadas += 1
        r = avaliar_politica(catalogo, list(combinacao), config, max_frac_aumento)
        if r["valida"] and r["caixa"] > melhor_caixa:
            melhor_caixa, melhor_niveis = r["caixa"], list(combinacao)

    return melhor_niveis, melhor_caixa, testadas


def brute_force_otimizado(catalogo, config, max_frac_aumento=0.50):
    """
    Versão 2 (depois): pré-calcula o caixa de cada (SKU, nível) UMA vez.
    Cada combinação vira só uma soma de valores já calculados.
    """
    margem_min = config["margem_minima_percentual"]
    opcoes, caixas = [], []
    for i in range(len(catalogo)):
        sku = catalogo.iloc[i]
        niveis = niveis_validos(sku, config)
        opcoes.append(niveis)
        caixas.append({n: avaliar_sku(sku, n, margem_min)["caixa"] for n in niveis})

    limite_aumentos = max_frac_aumento * len(catalogo)
    melhor_niveis, melhor_caixa, testadas = None, float("-inf"), 0

    for combinacao in itertools.product(*opcoes):
        testadas += 1
        if sum(1 for n in combinacao if n > 1.0) > limite_aumentos:
            continue  # viola o limite de aumentos: descarta sem calcular o caixa
        caixa = sum(caixas[i][n] for i, n in enumerate(combinacao))
        if caixa > melhor_caixa:
            melhor_caixa, melhor_niveis = caixa, list(combinacao)

    return melhor_niveis, melhor_caixa, testadas


def medir(funcao, *args):
    """Executa a função medindo tempo (perf_counter) e pico de memória (tracemalloc)."""
    tracemalloc.start()
    inicio = time.perf_counter()
    resultado = funcao(*args)
    tempo = time.perf_counter() - inicio
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, tempo, pico / 1024  # KB


if __name__ == "__main__":
    catalogo, config = carregar_dados("data/G777", "G777")
    sub = escolher_subconjunto(catalogo, config, n=6)
    print("Subconjunto:", list(sub["sku"]))

    (niv1, cx1, t1), tempo1, mem1 = medir(brute_force_ingenuo, sub, config)
    (niv2, cx2, t2), tempo2, mem2 = medir(brute_force_otimizado, sub, config)

    print("\nCombinações testadas:", t1)
    print("Melhor política:", niv2)
    print("Caixa ótimo:", round(cx2, 2))
    print(f"\nIngênuo:    {tempo1:8.3f} s | pico {mem1:8.1f} KB")
    print(f"Otimizado:  {tempo2:8.3f} s | pico {mem2:8.1f} KB")
    print(f"Ganho de velocidade: {tempo1 / tempo2:.0f}x")
    print("Mesmo resultado nas duas versões:", niv1 == niv2 and abs(cx1 - cx2) < 1e-6)