"""
Algoritmo Genético — Questão 1
Busca uma política de preços (um nível por SKU) que maximize o caixa,
respeitando a margem mínima (níveis válidos) e o limite de aumentos de preço.

Representação: cromossomo = lista com o nível escolhido para cada SKU.
"""
import random
import time
import tracemalloc

from modelo import carregar_dados, niveis_validos, avaliar_sku


def preparar(catalogo, config):
    """Pré-calcula opções válidas e o caixa de cada (SKU, nível) — mesma ideia do BF otimizado."""
    margem_min = config["margem_minima_percentual"]
    opcoes, caixas = [], []
    for i in range(len(catalogo)):
        sku = catalogo.iloc[i]
        niveis = niveis_validos(sku, config)
        opcoes.append(niveis)
        caixas.append({n: avaliar_sku(sku, n, margem_min)["caixa"] for n in niveis})
    return opcoes, caixas


def fitness(cromossomo, caixas, limite_aumentos):
    """Caixa total; políticas com aumentos acima do limite são penalizadas."""
    caixa = sum(caixas[i][n] for i, n in enumerate(cromossomo))
    excesso = sum(1 for n in cromossomo if n > 1.0) - limite_aumentos
    if excesso > 0:
        caixa -= excesso * 1_000_000  # penalidade grande: a política nunca vence uma válida
    return caixa


def selecao_torneio(populacao, notas, k, rng):
    """Sorteia k indivíduos e devolve o melhor deles."""
    competidores = rng.sample(range(len(populacao)), k)
    vencedor = max(competidores, key=lambda i: notas[i])
    return populacao[vencedor]


def crossover_uniforme(pai, mae, rng):
    """Cada gene (SKU) vem do pai ou da mãe com 50% de chance."""
    return [p if rng.random() < 0.5 else m for p, m in zip(pai, mae)]


def mutacao(cromossomo, opcoes, taxa, rng):
    """Com probabilidade 'taxa', troca o nível de um SKU por outro nível válido."""
    return [rng.choice(opcoes[i]) if rng.random() < taxa else n
            for i, n in enumerate(cromossomo)]


def algoritmo_genetico(catalogo, config, max_frac_aumento=0.50, tam_pop=60,
                       geracoes=500, taxa_mutacao=0.05, elitismo=2, torneio=3,
                       paciencia=100, seed=42):
    """
    Retorna: (melhor_cromossomo, melhor_caixa, historico_do_melhor_por_geracao)
    Critério de parada: 'geracoes' no máximo, ou 'paciencia' gerações sem melhora.
    """
    rng = random.Random(seed)
    opcoes, caixas = preparar(catalogo, config)
    limite = max_frac_aumento * len(catalogo)

    populacao = [[rng.choice(o) for o in opcoes] for _ in range(tam_pop)]
    historico, melhor, melhor_nota, sem_melhora = [], None, float("-inf"), 0

    for _ in range(geracoes):
        notas = [fitness(c, caixas, limite) for c in populacao]

        # guarda o melhor da geração
        idx = max(range(tam_pop), key=lambda i: notas[i])
        if notas[idx] > melhor_nota + 1e-9:
            melhor, melhor_nota, sem_melhora = list(populacao[idx]), notas[idx], 0
        else:
            sem_melhora += 1
        historico.append(melhor_nota)
        if sem_melhora >= paciencia:
            break

        # elitismo: os melhores passam direto para a próxima geração
        ordem = sorted(range(tam_pop), key=lambda i: notas[i], reverse=True)
        nova = [list(populacao[i]) for i in ordem[:elitismo]]

        while len(nova) < tam_pop:
            pai = selecao_torneio(populacao, notas, torneio, rng)
            mae = selecao_torneio(populacao, notas, torneio, rng)
            filho = mutacao(crossover_uniforme(pai, mae, rng), opcoes, taxa_mutacao, rng)
            nova.append(filho)
        populacao = nova

    return melhor, melhor_nota, historico


def medir(funcao, *args, **kwargs):
    tracemalloc.start()
    inicio = time.perf_counter()
    resultado = funcao(*args, **kwargs)
    tempo = time.perf_counter() - inicio
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, tempo, pico / 1024


if __name__ == "__main__":
    from brute_force import escolher_subconjunto, brute_force_otimizado

    catalogo, config = carregar_dados("data/G777", "G777")

    # 1) Validação: GA x Brute Force no mesmo subconjunto de 6 SKUs
    sub = escolher_subconjunto(catalogo, config, n=6)
    _, otimo, _ = brute_force_otimizado(sub, config)
    (_, cx_ga, hist), tempo, mem = medir(algoritmo_genetico, sub, config, tam_pop=30, geracoes=100)
    gap = (otimo - cx_ga) / otimo * 100
    print("== Subconjunto de 6 SKUs ==")
    print(f"Brute Force (ótimo): {otimo:,.2f}")
    print(f"GA:                  {cx_ga:,.2f} | gap {gap:.2f}% | {len(hist)} gerações | {tempo:.3f} s")

    # 2) Catálogo completo com duas configurações do GA (comparação de convergência)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("\n== Catálogo completo (30 SKUs) ==")
    plt.figure(figsize=(8, 4.5))
    configuracoes = [("A: pop 30, mutação 10%", dict(tam_pop=30, taxa_mutacao=0.10)),
                     ("B: pop 80, mutação 3%",  dict(tam_pop=80, taxa_mutacao=0.03))]
    for nome, params in configuracoes:
        (pol, cx, hist), tempo, mem = medir(algoritmo_genetico, catalogo, config, **params)
        aumentos = sum(1 for n in pol if n > 1.0)
        pausados = sum(1 for n in pol if n == 0.0)
        print(f"{nome}: caixa {cx:,.2f} | {len(hist)} gerações | {tempo:.2f} s | "
              f"pico {mem:.0f} KB | {aumentos} aumentos | {pausados} pausados")
        plt.plot(hist, label=nome)

    plt.axhline(config["meta_caixa_90d"], color="gray", linestyle="--", label="Meta de caixa")
    plt.title("GA — melhor caixa por geração")
    plt.xlabel("Geração")
    plt.ylabel("Caixa (R$)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("questao_01/resultados/ga_fitness.png", dpi=120)
    print("\nGráfico salvo em questao_01/resultados/ga_fitness.png")