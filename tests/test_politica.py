from decimal import Decimal

from motor_reembolso import politica


def test_limites_diarios():
    assert politica.LIMITE_ALIMENTACAO_DIA == Decimal("60.00")
    assert politica.LIMITE_TRANSPORTE_URBANO_DIA == Decimal("80.00")
    assert politica.LIMITE_HOSPEDAGEM_DIARIA == Decimal("250.00")


def test_gatilho_nota_fiscal():
    assert politica.GATILHO_NOTA_FISCAL == Decimal("100.00")


def test_ampliacao_viagem():
    assert politica.AMPLIACAO_VIAGEM == Decimal("1.5")


def test_categorias_oficiais():
    assert politica.CATEGORIAS_OFICIAIS == {"alimentacao", "transporte_urbano", "hospedagem"}


def test_mapeamento_analogia_coworking():
    assert politica.MAPEAMENTO_ANALOGIA["coworking"] == "hospedagem"
