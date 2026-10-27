
# Decisões de modelagem — Questão 1

## D1. Demanda por elasticidade constante

demanda = demanda_base_90d × nível^(−elasticidade); unidades = min(estoque, demanda).

## D2. Opção "pausar SKU"

5 SKUs (Q1-005, 015, 020, 021, 025) não atingem a margem mínima em nenhum nível.
Em vez de vender abaixo do piso, o SKU é pausado (caixa 0, estoque preservado).
Base: o enunciado proíbe liquidar estoque abaixo do custo.

## D3. Limite de aumentos de preço (50% dos SKUs)

Na instância, 24 de 30 SKUs prefeririam +10% (a demanda supera o estoque, então
desconto não aumenta vendas). Sem limite, a solução seria trivial e arriscada
comercialmente. O limite cria dependência entre SKUs e justifica BF e GA.
Parâmetro ajustável: max_frac_aumento.

## D4. Papel do Greedy

O giro de estoque é tratado no Greedy: o orçamento promocional vai para os SKUs
com estoque sobrando, onde cada real investido gera mais caixa adicional.
