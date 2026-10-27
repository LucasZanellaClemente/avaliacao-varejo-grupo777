from pathlib import Path
import json
import pandas as pd


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
    nivel: multiplicador do preço (ex.: 0.90 = 10% de desconto)
    margem_minima: ex.: 0.0592 = 5,92%
    """
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


def avaliar_politica(catalogo, niveis, config, max_frac_desconto=0.40):
    """
    Avalia uma política completa: um nível de preço para cada SKU.

    niveis: lista com um nível por SKU, na mesma ordem do catálogo
    max_frac_desconto: fração máxima de SKUs com desconto (nível < 1.00)
    """
    caixa_total = 0.0
    receita_total = 0.0
    estoque_restante = 0
    n_descontos = 0
    todos_validos = True

    for i, nivel in enumerate(niveis):
        sku = catalogo.iloc[i]
        r = avaliar_sku(sku, nivel, config["margem_minima_percentual"])

        if not r["valido"]:
            todos_validos = False

        caixa_total += r["caixa"]
        receita_total += r["preco"] * r["unidades"]
        estoque_restante += sku["estoque"] - r["unidades"]
        if nivel < 1.0:
            n_descontos += 1

    respeita_carteira = n_descontos <= max_frac_desconto * len(niveis)

    return {
        "caixa": caixa_total,
        "receita": receita_total,
        "margem_pct": caixa_total / receita_total if receita_total else 0,
        "estoque_restante": estoque_restante,
        "n_descontos": n_descontos,
        "valida": todos_validos and respeita_carteira,
        "folga_meta": caixa_total - config["meta_caixa_90d"],
        "cobertura_divida": caixa_total / config["divida_total_90d"],
    }


if __name__ == "__main__":
    catalogo, config = carregar_dados("data/G777", "G777")
    print(catalogo.head())
    print("SKUs:", len(catalogo))
    print("Níveis de preço:", config["niveis_preco_relativos"])
    print("Meta de caixa:", config["meta_caixa_90d"])

    # Teste 1: um SKU em todos os níveis
    print("\nQ1-001 por nível (nível, preço, unidades, margem/un, margem %, válido)")
    primeiro = catalogo.iloc[0]
    for nivel in config["niveis_preco_relativos"]:
        r = avaliar_sku(primeiro, nivel, config["margem_minima_percentual"])
        print(nivel, round(r["preco"], 2), round(r["unidades"], 1),
              round(r["margem_unit"], 2), round(r["margem_pct"] * 100, 1), r["valido"])

    # Teste 2: política atual (todos os SKUs no nível 1,00)
    atual = [1.0] * len(catalogo)
    r = avaliar_politica(catalogo, atual, config)
    print("\nCaixa com preços atuais:", round(r["caixa"], 2))
    print("Meta:", config["meta_caixa_90d"], "| Folga:", round(r["folga_meta"], 2))
    print("Cobertura da dívida:", round(r["cobertura_divida"] * 100, 1), "%")
    print("Válida:", r["valida"])