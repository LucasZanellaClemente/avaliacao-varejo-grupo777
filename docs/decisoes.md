
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




# Decisões de modelagem — Questão 2

## D6. Incerteza com choques lognormais

Demanda, preço do concorrente e custo logístico recebem um fator aleatório lognormal
com média 1 e dispersão = sigma do config. Lognormal nunca é negativo.

## D7. DP por SKU

Estado (semana, estoque restante). O estado conjunto dos 24 SKUs seria inviável
(produto dos estoques). Os SKUs se ligam pelo caixa, medido na validação Monte Carlo.
gamma = 0,98 valoriza o caixa que entra antes (primeira dívida na semana 4).

## D8. Greedy usa o valor da DP

Benefício do destaque = valor com destaque − V(t, s). Sem isso, o Greedy contava como
ganho vendas que só eram antecipadas, e o caixa piorava (322 mil → 287 mil).
Também atualiza o estoque planejado semana a semana para não contar o mesmo ganho duas vezes.

## D9. Validação independente

5.000 cenários com seed diferente da estimativa (seed + 1000).
Teste de estresse: o plano só falha com demanda 65% abaixo do normal.
