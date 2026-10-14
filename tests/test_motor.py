from datetime import date
from decimal import Decimal

from motor_reembolso.modelos import Despesa
from motor_reembolso.motor import (
    _regra_categoria,
    _regra_duplicata,
    _regra_periodo,
    _regra_valor_negativo,
)


def _despesa(**kwargs) -> Despesa:
    base = dict(
        id="d-999",
        data=date(2026, 7, 1),
        categoria_original="alimentacao",
        descricao="teste",
        fornecedor="fornecedor",
        valor=Decimal("10.00"),
        tem_nota_fiscal=True,
    )
    base.update(kwargs)
    return Despesa(**base)


def test_rn_010_estorno_ignorado():
    despesa = _despesa(id="d-009", categoria_original="transporte_urbano", valor=Decimal("-45.00"))
    resultado = _regra_valor_negativo(despesa)
    assert resultado is not None
    assert resultado.status == "ignorado"
    assert resultado.valor_reembolsado == Decimal("0.00")
    assert "RN-010" in resultado.motivos


def test_rn_010_valor_positivo_nao_ignorado():
    despesa = _despesa(valor=Decimal("10.00"))
    assert _regra_valor_negativo(despesa) is None


def test_rn_012_categoria_maiuscula():
    despesa = _despesa(id="d-014", categoria_original="ALIMENTACAO")
    resultado, categoria = _regra_categoria(despesa)
    assert resultado is None
    assert categoria == "alimentacao"


def test_rn_009_categoria_mapeada():
    despesa = _despesa(id="d-005", categoria_original="coworking", valor=Decimal("89.00"))
    resultado, categoria = _regra_categoria(despesa)
    assert resultado is None
    assert categoria == "hospedagem"


def test_rn_009_categoria_fora_da_politica():
    despesa = _despesa(categoria_original="brinde")
    resultado, categoria = _regra_categoria(despesa)
    assert resultado is not None
    assert resultado.status == "recusado"
    assert "RN-009" in resultado.motivos
    assert categoria is None


def test_rn_007_fora_periodo():
    despesa = _despesa(id="d-008", data=date(2026, 4, 15), valor=Decimal("41.00"))
    resultado = _regra_periodo(despesa, inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert resultado is not None
    assert resultado.status == "recusado"
    assert "RN-007" in resultado.motivos


def test_rn_007_dentro_periodo():
    despesa = _despesa(data=date(2026, 7, 15))
    resultado = _regra_periodo(despesa, inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert resultado is None


def test_rn_008_duplicata():
    d006 = _despesa(
        id="d-006", data=date(2026, 7, 9), categoria_original="alimentacao",
        fornecedor="Bistro Central", valor=Decimal("54.90"),
    )
    d007 = _despesa(
        id="d-007", data=date(2026, 7, 9), categoria_original="alimentacao",
        fornecedor="Bistro Central", valor=Decimal("54.90"),
    )
    chaves_vistas: set = set()
    resultado_1 = _regra_duplicata(d006, "alimentacao", chaves_vistas)
    assert resultado_1 is None
    resultado_2 = _regra_duplicata(d007, "alimentacao", chaves_vistas)
    assert resultado_2 is not None
    assert resultado_2.status == "recusado"
    assert "RN-008" in resultado_2.motivos


def test_rn_008_despesas_diferentes_nao_sao_duplicata():
    d001 = _despesa(id="d-001", data=date(2026, 7, 3), valor=Decimal("72.50"))
    d002 = _despesa(id="d-002", data=date(2026, 7, 3), valor=Decimal("38.00"))
    chaves_vistas: set = set()
    assert _regra_duplicata(d001, "alimentacao", chaves_vistas) is None
    assert _regra_duplicata(d002, "alimentacao", chaves_vistas) is None
