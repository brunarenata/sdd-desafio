from datetime import date
from decimal import Decimal

from motor_reembolso.modelos import Despesa, Resumo, ResultadoCalculo, ResultadoDespesa


def test_despesa_instancia_com_dados_minimos():
    despesa = Despesa(
        id="d-001",
        data=date(2026, 7, 3),
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Restaurante Tavola",
        valor=Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    assert despesa.id == "d-001"
    assert despesa.categoria_normalizada is None


def test_resultado_despesa_instancia_com_dados_minimos():
    despesa = Despesa(
        id="d-001",
        data=date(2026, 7, 3),
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Restaurante Tavola",
        valor=Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    resultado = ResultadoDespesa(
        despesa=despesa,
        valor_reembolsado=Decimal("60.00"),
        status="aprovado_parcial",
        motivos=["RN-001"],
        justificativa="teste",
    )
    assert resultado.status == "aprovado_parcial"


def test_resumo_instancia_com_dados_minimos():
    resumo = Resumo(
        total_declarado=Decimal("100.00"),
        total_reembolsado=Decimal("60.00"),
        total_recusado=Decimal("40.00"),
        quantidade_despesas=2,
        quantidade_aprovadas=1,
        quantidade_recusadas=1,
    )
    assert resumo.total_declarado == resumo.total_reembolsado + resumo.total_recusado
    assert resumo.quantidade_pendentes == 0


def test_despesa_aceita_moeda_e_centro_custo():
    despesa = Despesa(
        id="e-002",
        data=date(2026, 7, 14),
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Taberna do Chiado",
        valor=Decimal("22.00"),
        tem_nota_fiscal=True,
        centro_custo="CC-COMERCIAL",
        moeda="EUR",
    )
    assert despesa.moeda == "EUR"
    assert despesa.centro_custo == "CC-COMERCIAL"


def test_despesa_moeda_padrao_e_brl():
    despesa = Despesa(
        id="d-001",
        data=date(2026, 7, 3),
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Restaurante Tavola",
        valor=Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    assert despesa.moeda == "BRL"
    assert despesa.centro_custo == ""


def test_resultado_calculo_instancia_com_dados_minimos():
    resumo = Resumo(
        total_declarado=Decimal("0"),
        total_reembolsado=Decimal("0"),
        total_recusado=Decimal("0"),
        quantidade_despesas=0,
        quantidade_aprovadas=0,
        quantidade_recusadas=0,
    )
    calculo = ResultadoCalculo(
        colaborador={"id": "c-0417"},
        periodo={"competencia": "2026-07"},
        resultados=[],
        resumo=resumo,
    )
    assert calculo.colaborador["id"] == "c-0417"
