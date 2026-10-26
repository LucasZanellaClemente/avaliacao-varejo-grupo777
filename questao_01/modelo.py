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


if __name__ == "__main__":
    catalogo, config = carregar_dados("data/G777", "G777")
    print(catalogo.head())
    print("SKUs:", len(catalogo))
    print("Níveis de preço:", config["niveis_preco_relativos"])
    print("Meta de caixa:", config["meta_caixa_90d"])