"""Constantes da politica de reembolso.

Fonte: specs/001-motor-reembolso/spec.md secao 5 (RN-001 a RN-012).
Qualquer alteracao de limite deve vir acompanhada de atualizacao da spec
e de entrada em DECISIONS.md.
"""

from decimal import Decimal

LIMITE_ALIMENTACAO_DIA = Decimal("60.00")
LIMITE_TRANSPORTE_URBANO_DIA = Decimal("80.00")
LIMITE_HOSPEDAGEM_DIARIA = Decimal("250.00")

GATILHO_NOTA_FISCAL = Decimal("100.00")

AMPLIACAO_VIAGEM = Decimal("1.5")

CATEGORIA_ALIMENTACAO = "alimentacao"
CATEGORIA_TRANSPORTE_URBANO = "transporte_urbano"
CATEGORIA_HOSPEDAGEM = "hospedagem"

CATEGORIAS_OFICIAIS = {
    CATEGORIA_ALIMENTACAO,
    CATEGORIA_TRANSPORTE_URBANO,
    CATEGORIA_HOSPEDAGEM,
}

CATEGORIAS_COM_LIMITE_DIARIO = {
    CATEGORIA_ALIMENTACAO,
    CATEGORIA_TRANSPORTE_URBANO,
}

# AMB-008: categorias fora da lista oficial mapeadas por analogia de natureza
# do gasto. Qualquer categoria nao mapeada aqui e recusada (RN-009).
MAPEAMENTO_ANALOGIA = {
    "coworking": CATEGORIA_HOSPEDAGEM,
}
