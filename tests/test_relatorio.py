from datetime import date
from decimal import Decimal
from pathlib import Path

from motor_reembolso.io_despesas import carregar_despesas
from motor_reembolso.modelos import Despesa, ResultadoDespesa
from motor_reembolso.motor import calcular
from motor_reembolso.relatorio import montar_resultado_calculo, serializar

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO_OFICIAL = RAIZ / "exemplos" / "despesas-exemplo.json"


def test_formato_saida():
    despesa = Despesa(
        id="d-001",
        data=date(2026, 7, 3),
        categoria_original="alimentacao",
        categoria_normalizada="alimentacao",
        descricao="Almoco",
        fornecedor="Restaurante Tavola",
        valor=Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    resultado_despesa = ResultadoDespesa(
        despesa=despesa,
        valor_reembolsado=Decimal("60.00"),
        status="aprovado_parcial",
        motivos=["RN-001", "RN-004"],
        justificativa="teste",
    )
    entrada = carregar_despesas(EXEMPLO_OFICIAL)
    resultado = montar_resultado_calculo(entrada, [resultado_despesa])
    saida = serializar(resultado)

    assert saida["colaborador"]["id"] == "c-0417"
    assert saida["periodo"]["competencia"] == "2026-07"
    item = saida["despesas"][0]
    assert item["id"] == "d-001"
    assert item["categoria_aplicada"] == "alimentacao"
    assert item["valor_declarado"] == 72.50
    assert item["valor_reembolsado"] == 60.00
    assert item["status"] == "aprovado_parcial"
    assert saida["resumo"]["total_declarado"] == 72.50
    assert saida["resumo"]["total_reembolsado"] == 60.00
    assert saida["resumo"]["total_recusado"] == 12.50
    assert saida["resumo"]["quantidade_despesas"] == 1


def test_invariante_soma_totais_exemplo_oficial():
    """Criterio de aceite da secao 9 da spec: total_reembolsado +
    total_recusado == total_declarado para o conjunto oficial completo."""
    entrada = carregar_despesas(EXEMPLO_OFICIAL)
    resultados = calcular(entrada.despesas, entrada.periodo.inicio, entrada.periodo.fim)
    resultado = montar_resultado_calculo(entrada, resultados)

    assert (
        resultado.resumo.total_reembolsado + resultado.resumo.total_recusado
        == resultado.resumo.total_declarado
    )
    assert resultado.resumo.quantidade_despesas == 14


def test_estorno_excluido_do_total_declarado():
    entrada = carregar_despesas(EXEMPLO_OFICIAL)
    resultados = calcular(entrada.despesas, entrada.periodo.inicio, entrada.periodo.fim)
    resultado = montar_resultado_calculo(entrada, resultados)
    saida = serializar(resultado)

    item_estorno = next(d for d in saida["despesas"] if d["id"] == "d-009")
    assert item_estorno["status"] == "ignorado"
    assert item_estorno["valor_reembolsado"] == 0.0
