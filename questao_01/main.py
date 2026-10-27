"""
Questão 1 — Operação Caixa 90
Executa a cadeia completa: Brute Force (benchmark) -> Algoritmo Genético -> Greedy.

Exemplos:
  python questao_01/main.py --seed 42
  python questao_01/main.py --meta 1.10                 # cenário-surpresa: meta de caixa +10%
  python questao_01/main.py --logistica 1.15            # custo logístico +15%
  python questao_01/main.py --orcamento 0.75            # orçamento promocional -25%
  python questao_01/main.py --remover Q1-007            # SKU indisponível
  python questao_01/main.py --pop 100 --mutacao 0.02    # parâmetros do GA
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from modelo import carregar_dados, avaliar_politica
from brute_force import escolher_subconjunto, brute_force_otimizado
from genetic_algorithm import algoritmo_genetico, medir
from greedy import greedy_orcamento


def ler_argumentos():
    p = argparse.ArgumentParser(description="Questão 1 — Operação Caixa 90")
    p.add_argument("--grupo", default="G777")
    p.add_argument("--pasta", default="data/G777")
    p.add_argument("--seed", type=int, default=42, help="seed do Algoritmo Genético")
    p.add_argument("--modo", choices=["completo", "rapido"], default="completo",
                   help="rapido = pula o Brute Force")
    # parâmetros do modelo
    p.add_argument("--max-aumento", type=float, default=0.50, help="fração máx. de SKUs com aumento")
    p.add_argument("--razao-minima", type=float, default=0.0,
                   help="0 = verba de marketing reservada; 1 = verba sai do caixa")
    p.add_argument("--n-bf", type=int, default=6, help="tamanho do subconjunto do Brute Force")
    # parâmetros do GA
    p.add_argument("--pop", type=int, default=30)
    p.add_argument("--mutacao", type=float, default=0.10)
    p.add_argument("--geracoes", type=int, default=500)
    # cenário-surpresa (multiplicadores)
    p.add_argument("--meta", type=float, default=1.0, help="multiplica a meta de caixa")
    p.add_argument("--logistica", type=float, default=1.0, help="multiplica o custo logístico")
    p.add_argument("--orcamento", type=float, default=1.0, help="multiplica o orçamento promocional")
    p.add_argument("--remover", nargs="*", default=[], help="SKUs indisponíveis")
    return p.parse_args()


def aplicar_cenario(catalogo, config, args):
    """Aplica as alterações de cenário nos dados, sem tocar nos arquivos oficiais."""
    catalogo = catalogo.copy()
    config = dict(config)
    catalogo["custo_logistico"] = catalogo["custo_logistico"] * args.logistica
    config["meta_caixa_90d"] = config["meta_caixa_90d"] * args.meta
    config["orcamento_promocional"] = config["orcamento_promocional"] * args.orcamento
    if args.remover:
        catalogo = catalogo[~catalogo["sku"].isin(args.remover)].reset_index(drop=True)
    return catalogo, config


def main():
    args = ler_argumentos()
    saida = Path("questao_01/resultados")
    saida.mkdir(parents=True, exist_ok=True)

    catalogo, config = carregar_dados(args.pasta, args.grupo)
    catalogo, config = aplicar_cenario(catalogo, config, args)
    print(f"SKUs: {len(catalogo)} | Meta: {config['meta_caixa_90d']:,.2f} | "
          f"Dívida: {config['divida_total_90d']:,.2f} | "
          f"Orçamento promocional: {config['orcamento_promocional']:,.2f}")

    # Etapa A — Brute Force valida o GA num subconjunto pequeno
    if args.modo == "completo":
        sub = escolher_subconjunto(catalogo, config, n=args.n_bf)
        (_, otimo, combos), t_bf, m_bf = medir(brute_force_otimizado, sub, config, args.max_aumento)
        (_, cx_sub, _), t_ga_sub, m_ga_sub = medir(
            algoritmo_genetico, sub, config, max_frac_aumento=args.max_aumento,
            tam_pop=args.pop, taxa_mutacao=args.mutacao, geracoes=args.geracoes, seed=args.seed)
        gap = (otimo - cx_sub) / otimo * 100
        tabela_bf = pd.DataFrame([
            {"metodo": "Brute Force", "caixa": round(otimo, 2), "tempo_s": round(t_bf, 4),
             "memoria_kb": round(m_bf, 1), "combinacoes": combos, "gap_pct": 0.0},
            {"metodo": "Algoritmo Genético", "caixa": round(cx_sub, 2), "tempo_s": round(t_ga_sub, 4),
             "memoria_kb": round(m_ga_sub, 1), "combinacoes": None, "gap_pct": round(gap, 2)},
        ])
        tabela_bf.to_csv(saida / "bf_vs_ga.csv", index=False)
        print(f"\n[A] Brute Force x GA em {len(sub)} SKUs")
        print(tabela_bf.to_string(index=False))

    # Etapa B — GA no catálogo completo
    (politica, cx_ga, hist), t_ga, m_ga = medir(
        algoritmo_genetico, catalogo, config, max_frac_aumento=args.max_aumento,
        tam_pop=args.pop, taxa_mutacao=args.mutacao, geracoes=args.geracoes, seed=args.seed)
    r_ga = avaliar_politica(catalogo, politica, config, args.max_aumento)
    print(f"\n[B] GA no catálogo completo: caixa {cx_ga:,.2f} | {len(hist)} gerações | "
          f"{t_ga:.2f} s | {r_ga['n_aumentos']} aumentos | {r_ga['n_pausados']} pausados")

    # Etapa C — Greedy distribui o orçamento sobre a política do GA
    (cupons, gasto, ganho, _), t_gr, m_gr = medir(
        greedy_orcamento, catalogo, politica, config, args.razao_minima)
    caixa_final = r_ga["caixa"] + ganho
    print(f"\n[C] Greedy: usou {gasto:,.2f} do orçamento em {len(cupons)} SKUs | "
          f"caixa extra {ganho:,.2f}")

    # Resultado final
    folga = caixa_final - config["meta_caixa_90d"]
    resumo = {
        "caixa_final": round(caixa_final, 2),
        "meta_caixa": round(config["meta_caixa_90d"], 2),
        "meta_atingida": bool(folga >= 0),
        "folga_ou_insuficiencia": round(folga, 2),
        "cobertura_divida_pct": round(caixa_final / config["divida_total_90d"] * 100, 1),
        "margem_pct": round(r_ga["margem_pct"] * 100, 2),
        "estoque_restante_un": round(r_ga["estoque_restante"], 1),
        "orcamento_usado": round(gasto, 2),
        "orcamento_usado_pct": round(gasto / config["orcamento_promocional"] * 100, 1)
        if config["orcamento_promocional"] else 0,
        "skus_com_aumento": r_ga["n_aumentos"],
        "skus_pausados": r_ga["n_pausados"],
        "parametros": vars(args),
    }
    pd.DataFrame({"sku": catalogo["sku"], "nivel_preco": politica,
                  "cupom": [cupons.get(i, 0.0) for i in range(len(catalogo))]}
                 ).to_csv(saida / "politica_final.csv", index=False)
    with open(saida / "resumo.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2, default=float)

    print("\n== RESULTADO FINAL ==")
    print(f"Caixa gerado:          {caixa_final:,.2f}")
    print(f"Meta de caixa:         {config['meta_caixa_90d']:,.2f} -> "
          f"{'ATINGIDA' if folga >= 0 else 'NÃO ATINGIDA'} "
          f"({'folga' if folga >= 0 else 'insuficiência'} de {abs(folga):,.2f})")
    print(f"Cobertura da dívida:   {resumo['cobertura_divida_pct']}%")
    print(f"Margem (preços do GA): {resumo['margem_pct']}%")
    print(f"Estoque remanescente:  {resumo['estoque_restante_un']:,.0f} unidades (antes dos cupons)")
    print(f"Orçamento promocional: {gasto:,.2f} usados ({resumo['orcamento_usado_pct']}%)")
    print(f"\nArquivos salvos em {saida}/ (bf_vs_ga.csv, politica_final.csv, resumo.json)")


if __name__ == "__main__":
    main()