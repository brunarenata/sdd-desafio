from datetime import date
from decimal import Decimal
from pathlib import Path

from motor_reembolso import cambio, politica
from motor_reembolso.modelos import Despesa
from motor_reembolso.motor import (
    _aplicar_limites_diarios,
    _calcular_dias_viagem,
    _limite_diario,
    _quantizar,
    _regra_categoria,
    _regra_conversao_moeda,
    _regra_duplicata,
    _regra_hospedagem,
    _regra_hospedagem_zerada_cc,
    _regra_nota_fiscal,
    _regra_periodo,
    _regra_valor_negativo,
    calcular,
)

RAIZ = Path(__file__).resolve().parents[1]
POLITICA_V4 = RAIZ / "exemplos" / "envelope" / "politica-v4.json"
CAMBIO_V4 = RAIZ / "exemplos" / "envelope" / "cambio.json"


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


def test_ordem_regras_estrutural_nao_consome_limite_diario():
    """T-014: duplicata (etapa 4) e filtrada antes da agregacao diaria
    (etapa 6); nao deve ocupar espaco do limite de outra despesa valida
    do mesmo dia/categoria."""
    d_x = _despesa(id="d-x", data=date(2026, 7, 5), valor=Decimal("50.00"), fornecedor="A")
    d_y = _despesa(id="d-y", data=date(2026, 7, 5), valor=Decimal("50.00"), fornecedor="A")
    d_z = _despesa(id="d-z", data=date(2026, 7, 5), valor=Decimal("20.00"), fornecedor="B")

    resultados = calcular([d_x, d_y, d_z], inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    por_id = {r.despesa.id: r for r in resultados}

    assert por_id["d-y"].status == "recusado"
    assert "RN-008" in por_id["d-y"].motivos
    assert por_id["d-x"].status == "aprovado"
    assert por_id["d-x"].valor_reembolsado == Decimal("50.00")
    assert por_id["d-z"].status == "aprovado_parcial"
    assert por_id["d-z"].valor_reembolsado == Decimal("10.00")


def test_calcular_preserva_ordem_de_entrada():
    d1 = _despesa(id="d-1", data=date(2026, 7, 1))
    d2 = _despesa(id="d-2", data=date(2026, 7, 2))
    resultados = calcular([d1, d2], inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert [r.despesa.id for r in resultados] == ["d-1", "d-2"]


def test_borda_fim_de_semana_sem_regra_especial():
    """Caso de borda da secao 7 da spec: d-012 (sabado) nao recebe
    tratamento diferente de qualquer outro dia."""
    sabado = _despesa(id="d-012", data=date(2026, 7, 18), valor=Decimal("47.20"))
    resultados = calcular([sabado], inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert resultados[0].status == "aprovado"
    assert resultados[0].valor_reembolsado == Decimal("47.20")


# --- Envelope do Dia 2 (Politica de Reembolso v4) ---------------------


def test_rn_013_limite_por_centro_custo():
    """CC-ENG-PLATAFORMA tem limite de alimentacao especifico (R$75,00),
    diferente do limite padrao (R$60,00)."""
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="g-001", centro_custo="CC-ENG-PLATAFORMA", valor=Decimal("70.00")
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "aprovado"
    assert resultados[0].valor_reembolsado == Decimal("70.00")


def test_amb_013_cc_parcial_herda_limite_padrao_na_categoria_ausente():
    """CC-ADM nao lista hospedagem; usa o limite padrao (R$250,00/diaria)."""
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="g-002",
        centro_custo="CC-ADM",
        categoria_original="hospedagem",
        descricao="Hotel - 1 diaria",
        valor=Decimal("240.00"),
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "aprovado"
    assert resultados[0].valor_reembolsado == Decimal("240.00")


def test_rn_014_representacao_aprovada_para_cc_que_lista():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="e-001",
        centro_custo="CC-COMERCIAL",
        categoria_original="representacao",
        valor=Decimal("250.00"),
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "aprovado"
    assert "RN-014" in resultados[0].motivos


def test_amb_014_representacao_recusada_para_cc_ausente_da_tabela():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="f-003",
        centro_custo="CC-SUPORTE-N2",
        categoria_original="representacao",
        valor=Decimal("190.00"),
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "recusado"
    assert "RN-009" in resultados[0].motivos


def test_rn_015_conversao_moeda_antes_de_demais_regras():
    tabela_cambio = cambio.carregar_tabela_cambio(CAMBIO_V4)
    despesa = _despesa(
        id="e-002",
        data=date(2026, 7, 14),
        valor=Decimal("10.00"),
        moeda="EUR",
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_cambio=tabela_cambio
    )
    assert resultados[0].valor_reembolsado == Decimal("10.00") * Decimal("5.93")
    assert resultados[0].status == "aprovado"


def test_amb_016_conversao_usa_ultimo_dia_util_anterior():
    tabela_cambio = cambio.carregar_tabela_cambio(CAMBIO_V4)
    despesa = _despesa(
        id="e-004",
        data=date(2026, 7, 18),
        valor=Decimal("30.00"),
        moeda="EUR",
    )
    resultado_cambio, valor_brl = _regra_conversao_moeda(despesa, tabela_cambio)
    assert resultado_cambio is None
    assert valor_brl == Decimal("30.00") * Decimal("5.96")


def test_amb_015_moeda_sem_cotacao_fica_nao_processado():
    tabela_cambio = cambio.carregar_tabela_cambio(CAMBIO_V4)
    despesa = _despesa(id="e-006", valor=Decimal("55.00"), moeda="GBP")
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_cambio=tabela_cambio
    )
    assert resultados[0].status == "nao_processado"
    assert "RN-015" in resultados[0].motivos


def test_amb_015_sem_tabela_cambio_moeda_estrangeira_fica_nao_processado():
    despesa = _despesa(id="e-002", valor=Decimal("22.00"), moeda="EUR")
    resultados = calcular([despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert resultados[0].status == "nao_processado"


def test_rn_016_hospedagem_zerada_por_politica_do_cc():
    """CC-ENG-PLATAFORMA nao reembolsa hospedagem, mesmo com diarias
    identificaveis na descricao (motivo distinto de AMB-010b)."""
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="g-003",
        centro_custo="CC-ENG-PLATAFORMA",
        categoria_original="hospedagem",
        descricao="Hotel - 2 diarias",
        valor=Decimal("400.00"),
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "recusado"
    assert "RN-016" in resultados[0].motivos
    assert "RN-003" not in resultados[0].motivos


def test_amb_019_hospedagem_zerada_distingue_de_diarias_nao_identificaveis():
    politica_cc = politica.resolver_politica_centro_custo(
        politica.carregar_tabela_politica(POLITICA_V4), "CC-ENG-PLATAFORMA"
    )
    despesa = _despesa(categoria_original="hospedagem", descricao="sem numero")
    resultado = _regra_hospedagem_zerada_cc(despesa, "hospedagem", politica_cc)
    assert resultado is not None
    assert resultado.motivos == ["RN-016"]


def test_amb_018_representacao_nao_recebe_ampliacao_de_viagem():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    hospedagem = _despesa(
        id="e-007",
        centro_custo="CC-COMERCIAL",
        categoria_original="hospedagem",
        data=date(2026, 7, 22),
        descricao="Hotel - 3 noites",
        valor=Decimal("1200.00"),
    )
    representacao = _despesa(
        id="e-006b",
        centro_custo="CC-COMERCIAL",
        categoria_original="representacao",
        data=date(2026, 7, 22),
        valor=Decimal("300.00"),
    )
    resultados = calcular(
        [hospedagem, representacao],
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
        tabela_politica=tabela,
    )
    por_id = {r.despesa.id: r for r in resultados}
    assert por_id["e-006b"].valor_reembolsado == Decimal("300.00")
    assert por_id["e-006b"].status == "aprovado"


def test_rn_017_fila_aprovacao_manual_acima_de_500():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    despesa = _despesa(
        id="e-007",
        centro_custo="CC-COMERCIAL",
        categoria_original="hospedagem",
        descricao="Hotel Londres - 3 noites",
        valor=Decimal("1200.00"),
    )
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "pendente"
    assert resultados[0].valor_reembolsado == Decimal("1200.00")
    assert "RN-017" in resultados[0].motivos


def test_amb_020_limite_de_500_exato_nao_entra_na_fila():
    despesa = _despesa(
        id="g-004",
        categoria_original="hospedagem",
        descricao="Hotel - 1 diaria",
        valor=Decimal("500.00"),
    )
    tabela = politica.TabelaPolitica(padrao={"hospedagem": Decimal("500.00"), "alimentacao": Decimal("60.00"), "transporte_urbano": Decimal("80.00")})
    resultados = calcular(
        [despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31), tabela_politica=tabela
    )
    assert resultados[0].status == "aprovado"
    assert resultados[0].valor_reembolsado == Decimal("500.00")


def test_amb_021_despesa_recusada_nunca_entra_na_fila():
    despesa = _despesa(
        id="g-005",
        valor=Decimal("600.00"),
        tem_nota_fiscal=False,
    )
    resultados = calcular([despesa], inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    assert resultados[0].status == "recusado"
