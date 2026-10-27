"""
Greedy — Questão 1
Distribui o orçamento promocional (cupons) sobre a política de preços produzida pelo GA.

Modelo do cupom: o cliente paga (1 - c) do preço e o orçamento promocional cobre a diferença.
- A margem do varejista por unidade não muda (o cupom é pago pelo orçamento).
- A demanda reage ao preço que o cliente paga (mesma elasticidade do modelo).
- Benefício = unidades extras × margem por unidade.
- Custo     = c × preço × TODAS as unidades vendidas com cupom.
Regra gulosa: investir primeiro onde o benefício por real gasto é maior.
"""
from modelo import carregar_dados, avaliar_sku, PAUSA

CUPONS = [0.05, 0.10]  # degraus de cupom (5% e 10% do preço)


def efeito_cupom(sku, nivel, cupom, margem_min):
    """Unidades vendidas e custo do orçamento para um SKU com um certo cupom."""
    base = avaliar_sku(sku, nivel, margem_min)
    if cupom == 0:
        return base["unidades"], 0.0, base["margem_unit"]
    demanda = sku["demanda_base_90d"] * (nivel * (1 - cupom)) ** (-sku["elasticidade"])
    unidades = min(sku["estoque"], demanda)
    custo = cupom * base["preco"] * unidades
    return unidades, custo, base["margem_unit"]


def gerar_degraus(catalogo, politica, config):
    """
    Para cada SKU vendido, cria os degraus 0% -> 5% -> 10% com o benefício e o custo
    INCREMENTAIS de subir um degrau.
    """
    margem_min = config["margem_minima_percentual"]
    degraus = []
    for i, nivel in enumerate(politica):
        if nivel == PAUSA:
            continue
        sku = catalogo.iloc[i]
        anterior = 0.0
        u0, c0, m = efeito_cupom(sku, nivel, anterior, margem_min)
        for cupom in CUPONS:
            u1, c1, _ = efeito_cupom(sku, nivel, cupom, margem_min)
            beneficio = (u1 - u0) * m
            custo = c1 - c0
            if custo > 0:
                degraus.append({"i": i, "sku": sku["sku"], "de": anterior, "para": cupom,
                                "beneficio": beneficio, "custo": custo,
                                "razao": beneficio / custo})
            anterior, u0, c0 = cupom, u1, c1
    return degraus


def greedy_orcamento(catalogo, politica, config, razao_minima=0.0):
    """
    Ordena os degraus pelo benefício por real (razão) e compra os melhores enquanto
    houver orçamento. Um degrau de 10% só pode ser comprado depois do de 5% do mesmo SKU.

    razao_minima:
      0.0 -> orçamento já reservado para marketing (verba carimbada): vale gastar
             enquanto o cupom trouxer algum caixa extra
      1.0 -> orçamento sai do caixa da empresa: só compra se cada real voltar com lucro
    """
    orcamento = config["orcamento_promocional"]
    degraus = sorted(gerar_degraus(catalogo, politica, config),
                     key=lambda d: d["razao"], reverse=True)

    cupom_atual = {}          # SKU -> cupom já comprado
    gasto, ganho, escolhidos = 0.0, 0.0, []
    for d in degraus:
        if d["razao"] <= razao_minima:
            break                                   # daqui pra frente nenhum degrau compensa
        if cupom_atual.get(d["i"], 0.0) != d["de"]:
            continue                                # precisa ter comprado o degrau anterior
        if gasto + d["custo"] > orcamento:
            continue                                # não cabe no que sobrou do orçamento
        cupom_atual[d["i"]] = d["para"]
        gasto += d["custo"]
        ganho += d["beneficio"]
        escolhidos.append(d)

    return cupom_atual, gasto, ganho, escolhidos


if __name__ == "__main__":
    from genetic_algorithm import algoritmo_genetico
    from modelo import avaliar_politica

    catalogo, config = carregar_dados("data/G777", "G777")
    orcamento = config["orcamento_promocional"]

    # 1) Política de preços vinda do GA (integração GA -> Greedy)
    politica, _, _ = algoritmo_genetico(catalogo, config, tam_pop=30, taxa_mutacao=0.10)
    antes = avaliar_politica(catalogo, politica, config)
    print(f"Orçamento promocional: {orcamento:,.2f}")
    print(f"Caixa da política do GA (antes do Greedy): {antes['caixa']:,.2f}")

    # 2) Greedy nos dois cenários de origem do orçamento
    cenarios = [("Verba de marketing reservada (razão > 0)", 0.0),
                ("Verba sai do caixa (razão > 1)", 1.0)]
    for nome, razao_min in cenarios:
        cupons, gasto, ganho, escolhidos = greedy_orcamento(catalogo, politica, config, razao_min)
        print(f"\n== {nome} ==")
        print(f"Usado: {gasto:,.2f} ({gasto / orcamento * 100:.1f}% do orçamento) | "
              f"cupons em {len(cupons)} SKUs")
        print(f"Caixa extra dos cupons: {ganho:,.2f} | retorno médio: "
              f"{(ganho / gasto if gasto else 0):.2f} por real")
        for d in escolhidos[:5]:
            print(f"  {d['sku']}: {d['de']:.0%} -> {d['para']:.0%} | custo {d['custo']:9,.2f} | "
                  f"benefício {d['beneficio']:9,.2f} | {d['razao']:.2f} por real")
        if len(escolhidos) > 5:
            print(f"  ... e mais {len(escolhidos) - 5} degraus")
        print(f"Caixa (margem):  {antes['caixa']:12,.2f} -> {antes['caixa'] + ganho:12,.2f}")
        print(f"Unidades extras vendidas giram o estoque parado; "
              f"cobertura da dívida: {(antes['caixa'] + ganho) / config['divida_total_90d'] * 100:.1f}%")