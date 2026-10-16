from decimal import Decimal
from pathlib import Path

from motor_reembolso import politica

RAIZ = Path(__file__).resolve().parents[1]
POLITICA_V4 = RAIZ / "exemplos" / "envelope" / "politica-v4.json"


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


def test_rn_013_carrega_tabela_politica_v4():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    assert tabela.padrao["alimentacao"] == Decimal("60.00")
    assert tabela.gatilho_nota_fiscal == Decimal("100.00")
    assert tabela.ampliacao_viagem_percentual == Decimal("50")


def test_rn_013_resolve_limite_especifico_do_cc():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    resolvida = politica.resolver_politica_centro_custo(tabela, "CC-ENG-PLATAFORMA")
    assert resolvida.limites["alimentacao"] == Decimal("75.00")


def test_amb_013_categoria_ausente_herda_padrao():
    """CC-ADM nao lista hospedagem; deve herdar o limite padrao so para
    essa categoria."""
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    resolvida = politica.resolver_politica_centro_custo(tabela, "CC-ADM")
    assert resolvida.limites["hospedagem"] == Decimal("250.00")
    assert resolvida.limites["alimentacao"] == Decimal("45.00")


def test_amb_014_cc_ausente_usa_padrao_integral_sem_representacao():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    resolvida = politica.resolver_politica_centro_custo(tabela, "CC-SUPORTE-N2")
    assert resolvida.limites["alimentacao"] == Decimal("60.00")
    assert resolvida.limites["transporte_urbano"] == Decimal("80.00")
    assert resolvida.limites["hospedagem"] == Decimal("250.00")
    assert "representacao" not in resolvida.categorias_disponiveis


def test_rn_014_representacao_disponivel_so_para_cc_que_lista():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    comercial = politica.resolver_politica_centro_custo(tabela, "CC-COMERCIAL")
    assert "representacao" in comercial.categorias_disponiveis
    assert comercial.limites["representacao"] == Decimal("300.00")

    adm = politica.resolver_politica_centro_custo(tabela, "CC-ADM")
    assert "representacao" not in adm.categorias_disponiveis


def test_rn_016_hospedagem_zerada_para_cc_eng_plataforma():
    tabela = politica.carregar_tabela_politica(POLITICA_V4)
    resolvida = politica.resolver_politica_centro_custo(tabela, "CC-ENG-PLATAFORMA")
    assert resolvida.limites["hospedagem"] == Decimal("0.00")

