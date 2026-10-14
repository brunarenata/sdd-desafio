from datetime import date
from decimal import Decimal

from motor_reembolso.modelos import Despesa
from motor_reembolso.motor import (
    _aplicar_limites_diarios,
    _calcular_dias_viagem,
    _limite_diario,
    _quantizar,
    _regra_categoria,
    _regra_duplicata,
    _regra_hospedagem,
    _regra_nota_fiscal,
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


def test_rn_005_limite_sem_nota_na_fronteira():
    despesa = _despesa(id="d-003", valor=Decimal("100.00"), tem_nota_fiscal=False)
    assert _regra_nota_fiscal(despesa) is None


def test_rn_005_acima_sem_nota():
    despesa = _despesa(id="d-004", valor=Decimal("100.01"), tem_nota_fiscal=False)
    resultado = _regra_nota_fiscal(despesa)
    assert resultado is not None
    assert resultado.status == "recusado"
    assert "RN-005" in resultado.motivos


def test_rn_005_acima_com_nota():
    despesa = _despesa(valor=Decimal("150.00"), tem_nota_fiscal=True)
    assert _regra_nota_fiscal(despesa) is None


def test_rn_003_hospedagem_duas_diarias():
    despesa = _despesa(
        id="d-010", descricao="Hotel Rio - 2 diarias", valor=Decimal("480.00"),
    )
    resultado = _regra_hospedagem(despesa, "hospedagem")
    assert resultado is not None
    assert resultado.status == "aprovado"
    assert resultado.valor_reembolsado == Decimal("480.00")


def test_rn_003_hospedagem_tres_noites():
    despesa = _despesa(
        id="d-013", descricao="Airbnb 3 noites", valor=Decimal("690.00"),
    )
    resultado = _regra_hospedagem(despesa, "hospedagem")
    assert resultado is not None
    assert resultado.status == "aprovado"
    assert resultado.valor_reembolsado == Decimal("690.00")


def test_rn_003_sem_diarias_recusa():
    despesa = _despesa(id="d-999", descricao="Hospedagem sem detalhe", valor=Decimal("300.00"))
    resultado = _regra_hospedagem(despesa, "hospedagem")
    assert resultado is not None
    assert resultado.status == "recusado"
    assert "RN-003" in resultado.motivos


def test_rn_003_acima_do_limite_corta():
    despesa = _despesa(descricao="Hotel caro 1 diaria", valor=Decimal("400.00"))
    resultado = _regra_hospedagem(despesa, "hospedagem")
    assert resultado is not None
    assert resultado.status == "aprovado_parcial"
    assert resultado.valor_reembolsado == Decimal("250.00")


def test_rn_003_categoria_diferente_nao_avaliada():
    despesa = _despesa(categoria_original="alimentacao")
    assert _regra_hospedagem(despesa, "alimentacao") is None


def test_rn_006_calcula_dias_viagem_pela_hospedagem():
    hospedagem = _despesa(id="d-010", data=date(2026, 7, 14), categoria_original="hospedagem")
    alimentacao = _despesa(id="d-012", data=date(2026, 7, 18), categoria_original="alimentacao")
    dias_viagem = _calcular_dias_viagem(
        [(hospedagem, "hospedagem"), (alimentacao, "alimentacao")]
    )
    assert dias_viagem == {date(2026, 7, 14)}


def test_rn_006_ampliacao_viagem():
    dias_viagem = {date(2026, 7, 14)}
    assert _limite_diario("alimentacao", date(2026, 7, 14), dias_viagem) == Decimal("90.00")
    assert _limite_diario("transporte_urbano", date(2026, 7, 14), dias_viagem) == Decimal("120.00")


def test_rn_006_sem_viagem_limite_padrao():
    dias_viagem: set = set()
    assert _limite_diario("alimentacao", date(2026, 7, 3), dias_viagem) == Decimal("60.00")
    assert _limite_diario("transporte_urbano", date(2026, 7, 3), dias_viagem) == Decimal("80.00")


def test_rn_001_soma_dia_alimentacao():
    d001 = _despesa(id="d-001", data=date(2026, 7, 3), valor=Decimal("72.50"))
    d002 = _despesa(id="d-002", data=date(2026, 7, 3), valor=Decimal("38.00"))
    resultados = _aplicar_limites_diarios(
        [(d001, "alimentacao"), (d002, "alimentacao")], dias_viagem=set()
    )
    assert resultados[0].status == "aprovado_parcial"
    assert resultados[0].valor_reembolsado == Decimal("60.00")
    assert resultados[1].status == "recusado"
    assert resultados[1].valor_reembolsado == Decimal("0.00")


def test_rn_002_transporte_dentro_limite():
    d003 = _despesa(id="d-003", categoria_original="transporte_urbano", valor=Decimal("70.00"))
    resultados = _aplicar_limites_diarios([(d003, "transporte_urbano")], dias_viagem=set())
    assert resultados[0].status == "aprovado"
    assert resultados[0].valor_reembolsado == Decimal("70.00")


def test_rn_011_arredondamento():
    assert _quantizar(Decimal("33.333")) == Decimal("33.33")
    assert _quantizar(Decimal("33.335")) == Decimal("33.34")
    assert _quantizar(Decimal("33.345")) == Decimal("33.34")
