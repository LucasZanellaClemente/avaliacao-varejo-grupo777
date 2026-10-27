"""
Testes automatizados da Questão 1.
Rodar a partir da raiz do projeto:  pytest -q
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "questao_01"))

from modelo import avaliar_sku, avaliar_politica, niveis_validos, PAUSA  # noqa: E402
from brute_force import brute_force_otimizado, brute_force_ingenuo      # noqa: E402
from genetic_algorithm import algoritmo_genetico                         # noqa: E402
from greedy import greedy_orcamento                                      # noqa: E402

CONFIG = {
    "margem_minima_percentual": 0.05,
    "niveis_preco_relativos": [0.9, 1.0, 1.1],
    "meta_caixa_90d": 1000.0,
    "divida_total_90d": 800.0,
    "orcamento_promocional": 500.0,
}


def sku(preco=100.0, custo=50.0, estoque=10, demanda=10, elasticidade=1.5,
        taxa=0.10, logistica=5.0, nome="T-001"):
    return pd.Series({"sku": nome, "preco_atual": preco, "custo_unitario": custo,
                      "estoque": estoque, "demanda_base_90d": demanda,
                      "elasticidade": elasticidade, "taxa_marketplace": taxa,
                      "custo_logistico": logistica})


def catalogo(n=4):
    linhas = [sku(preco=100 + 10 * i, demanda=8 + i, estoque=12, nome=f"T-{i:03d}") for i in range(n)]
    return pd.DataFrame(linhas).reset_index(drop=True)


# ---------- modelo ----------
def test_margem_no_preco_atual():
    r = avaliar_sku(sku(), 1.0, 0.05)
    # 100 * (1 - 0.10) - 50 - 5 = 35
    assert r["margem_unit"] == pytest.approx(35.0)
    assert r["valido"]


def test_unidades_limitadas_pelo_estoque():
    r = avaliar_sku(sku(estoque=5, demanda=50), 1.0, 0.05)
    assert r["unidades"] == 5


def test_desconto_aumenta_demanda():
    caro = avaliar_sku(sku(estoque=1000), 1.0, 0.05)
    barato = avaliar_sku(sku(estoque=1000), 0.9, 0.05)
    assert barato["unidades"] > caro["unidades"]


def test_margem_negativa_e_invalida():
    r = avaliar_sku(sku(custo=95.0), 1.0, 0.05)
    assert not r["valido"]


def test_pausa_nao_gera_caixa_e_e_valida():
    r = avaliar_sku(sku(), PAUSA, 0.05)
    assert r["caixa"] == 0 and r["valido"]


def test_sku_sem_margem_so_pode_pausar():
    assert niveis_validos(sku(custo=200.0), CONFIG) == [PAUSA]


def test_limite_de_aumentos_invalida_politica():
    cat = catalogo(4)
    r = avaliar_politica(cat, [1.1, 1.1, 1.1, 1.0], CONFIG, max_frac_aumento=0.5)
    assert not r["valida"]


# ---------- brute force ----------
def test_bf_otimizado_igual_ao_ingenuo():
    cat = catalogo(4)
    n1, c1, _ = brute_force_ingenuo(cat, CONFIG)
    n2, c2, _ = brute_force_otimizado(cat, CONFIG)
    assert n1 == n2 and c1 == pytest.approx(c2)


def test_bf_respeita_limite_de_aumentos():
    cat = catalogo(4)
    niveis, _, _ = brute_force_otimizado(cat, CONFIG, max_frac_aumento=0.5)
    assert sum(1 for n in niveis if n > 1.0) <= 2


# ---------- algoritmo genético ----------
def test_ga_reprodutivel_com_mesma_seed():
    cat = catalogo(5)
    a = algoritmo_genetico(cat, CONFIG, seed=7, geracoes=50)
    b = algoritmo_genetico(cat, CONFIG, seed=7, geracoes=50)
    assert a[0] == b[0] and a[1] == b[1]


def test_ga_alcanca_otimo_em_instancia_pequena():
    cat = catalogo(4)
    _, otimo, _ = brute_force_otimizado(cat, CONFIG)
    _, caixa_ga, _ = algoritmo_genetico(cat, CONFIG, seed=1, geracoes=200)
    assert caixa_ga == pytest.approx(otimo)


# ---------- greedy ----------
def test_greedy_nao_estoura_orcamento():
    cat = catalogo(4)
    _, gasto, _, _ = greedy_orcamento(cat, [1.0] * 4, CONFIG, razao_minima=0.0)
    assert gasto <= CONFIG["orcamento_promocional"] + 1e-9


def test_greedy_orcamento_zero_nao_gasta():
    cat = catalogo(4)
    cfg = dict(CONFIG, orcamento_promocional=0.0)
    cupons, gasto, _, _ = greedy_orcamento(cat, [1.0] * 4, cfg)
    assert gasto == 0 and cupons == {}


def test_greedy_ignora_sku_pausado():
    cat = catalogo(3)
    cupons, _, _, _ = greedy_orcamento(cat, [PAUSA, 1.0, 1.0], CONFIG)
    assert 0 not in cupons