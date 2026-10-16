from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from motor_reembolso import cambio

RAIZ = Path(__file__).resolve().parents[1]
CAMBIO_V4 = RAIZ / "exemplos" / "envelope" / "cambio.json"


def test_rn_015_carrega_tabela_cambio():
    tabela = cambio.carregar_tabela_cambio(CAMBIO_V4)
    assert tabela.taxas[date(2026, 7, 14)]["EUR"] == Decimal("5.93")


def test_rn_015_converte_moeda_na_data_exata():
    tabela = cambio.carregar_tabela_cambio(CAMBIO_V4)
    valor = cambio.converter_para_brl(Decimal("22.00"), "EUR", date(2026, 7, 14), tabela)
    assert valor == Decimal("22.00") * Decimal("5.93")


def test_rn_015_brl_nao_e_convertido():
    tabela = cambio.carregar_tabela_cambio(CAMBIO_V4)
    valor = cambio.converter_para_brl(Decimal("100.00"), "BRL", date(2026, 7, 14), tabela)
    assert valor == Decimal("100.00")


def test_amb_016_data_sem_cotacao_usa_ultimo_dia_util_anterior():
    """e-004: EUR, 2026-07-18 (sabado), sem cotacao publicada; deve usar
    a taxa do ultimo dia util anterior disponivel (2026-07-17)."""
    tabela = cambio.carregar_tabela_cambio(CAMBIO_V4)
    taxa = cambio.resolver_taxa(tabela, "EUR", date(2026, 7, 18))
    assert taxa == tabela.taxas[date(2026, 7, 17)]["EUR"]


def test_amb_015_moeda_sem_cotacao_levanta_erro():
    """e-006: GBP nunca aparece na tabela de cambio."""
    tabela = cambio.carregar_tabela_cambio(CAMBIO_V4)
    with pytest.raises(cambio.MoedaSemCotacaoError):
        cambio.resolver_taxa(tabela, "GBP", date(2026, 7, 21))
