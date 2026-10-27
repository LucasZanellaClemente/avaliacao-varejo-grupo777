from pathlib import Path
import json
import pandas as pd

PAUSA = 0.0  # nível especial: o SKU não é vendido no período (caixa 0, estoque parado)


def carregar_dados(pasta, grupo):
    """
    Lê o catálogo (CSV) e a configuração (JSON) da Questão 1.
    Retorna: (catalogo: DataFrame, config: dict)
    """
    pasta = Path(pasta)
    arquivo_csv = pasta / f"q1_catalogo_{grupo}.csv"
    arquivo_json = pasta / f"q1_config_{grupo}.json"

    catalogo = pd.read_csv(arquivo_csv, encoding="utf-8-sig")
    with open(arquivo_json, encoding="utf-8") as f:
        config = json.load(f)
    return catalogo, config


def avaliar_sku(sku, nivel, margem_minima):
    """
    Calcula o resultado de UM SKU em UM nível de preço.

    sku: uma linha do catálogo (pandas Series)
    nivel: multiplicador do preço (ex.: 0.90 = 10% de desconto); PAUSA = não vender
    margem_minima: ex.: 0.0538 = 5,38%
    """
    if nivel == PAUSA:
        return {"preco": 0.0, "unidades": 0.0, "margem_unit": 0.0,
                "margem_pct": 0.0, "caixa": 0.0, "valido": True}

    preco = sku["preco_atual"] * nivel

    # demanda reage ao preço pela elasticidade (modelo de elasticidade constante)
    demanda = sku["demanda_base_90d"] * nivel ** (-sku["elasticidade"])
    unidades = min(sku["estoque"], demanda)

    margem_unit = (preco * (1 - sku["taxa_marketplace"])
                   - sku["custo_unitario"] - sku["custo_logistico"])
    margem_pct = margem_unit / preco
    valido = margem_pct >= margem_minima

    caixa = unidades * margem_unit

    return {
        "preco": preco,
        "unidades": unidades,
        "margem_unit": margem_unit,
        "margem_pct": margem_pct,
        "caixa": caixa,
        "valido": valido,
    }


def niveis_validos(sku, config):
    """
    Níveis permitidos para um SKU: os que respeitam a margem mínima, mais a PAUSA.
    Reduz o espaço de busca do Brute Force e do GA.
    """
    validos = [n for n in config["niveis_preco_relativos"]
               if avaliar_sku(sku, n, config["margem_minima_percentual"])["valido"]]
    return validos + [PAUSA]


def avaliar_politica(catalogo, niveis, config, max_frac_aumento=0.50):
    """
    Avalia uma política completa: um nível de preço para cada SKU.

    niveis: lista com um nível por SKU, na mesma ordem do catálogo
    max_frac_aumento: fração máxima de SKUs com aumento de preço (nível > 1.00)
    """
    caixa_total = 0.0
    receita_total = 0.0
    estoque_restante = 0.0
    n_aumentos = 0
    n_pausados = 0
    todos_validos = True

    for i, nivel in enumerate(niveis):
        sku = catalogo.iloc[i]
        r = avaliar_sku(sku, nivel, config["margem_minima_percentual"])

        if not r["valido"]:
            todos_validos = False

        caixa_total += r["caixa"]
        receita_total += r["preco"] * r["unidades"]
        estoque_restante += sku["estoque"] - r["unidades"]
        if nivel > 1.0:
            n_aumentos += 1
        if nivel == PAUSA:
            n_pausados += 1

    respeita_carteira = n_aumentos <= max_frac_aumento * len(niveis)

    return {
        "caixa": caixa_total,
        "receita": receita_total,
        "margem_pct": caixa_total / receita_total if receita_total else 0,
        "estoque_restante": estoque_restante,
        "n_aumentos": n_aumentos,
        "n_pausados": n_pausados,
        "valida": todos_validos and respeita_carteira,
        "folga_meta": caixa_total - config["meta_caixa_90d"],
        "cobertura_divida": caixa_total / config["divida_total_90d"],
    }


if __name__ == "__main__":
    catalogo, config = carregar_dados("data/G777", "G777")
    print("SKUs:", len(catalogo), "| Meta de caixa:", config["meta_caixa_90d"])

    # Quantos níveis cada SKU pode usar (inclui a pausa)
    opcoes = [niveis_validos(catalogo.iloc[i], config) for i in range(len(catalogo))]
    sem_margem = [catalogo.iloc[i]["sku"] for i, o in enumerate(opcoes) if o == [PAUSA]]
    print("SKUs sem nenhum nível com margem mínima (só podem pausar):", sem_margem)

    # Política de referência: preço atual quando possível, senão o menor nível válido, senão pausa
    referencia = []
    for o in opcoes:
        precos = [n for n in o if n != PAUSA]
        referencia.append(1.0 if 1.0 in precos else (min(precos) if precos else PAUSA))

    r = avaliar_politica(catalogo, referencia, config)
    print("\nPolítica de referência (sem otimização)")
    print("Caixa:", round(r["caixa"], 2), "| Folga da meta:", round(r["folga_meta"], 2))
    print("Cobertura da dívida:", round(r["cobertura_divida"] * 100, 1), "%")
    print("Aumentos:", r["n_aumentos"], "| Pausados:", r["n_pausados"], "| Válida:", r["valida"])