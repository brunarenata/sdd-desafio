"""Constantes e resolucao da politica de reembolso.

Fonte: specs/001-motor-reembolso/spec.md secao 5 (RN-001 a RN-017).
Qualquer alteracao de limite deve vir acompanhada de atualizacao da spec
e de entrada em DECISIONS.md.

A partir da v4 (RN-013/RN-014), os limites podem ser lidos de uma tabela
externa (`politica-v4.json`) e resolvidos por centro de custo; quando
nenhuma tabela e informada, usa-se a politica padrao embutida (equivalente
a v3) definida em `politica_padrao_embutida()`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

LIMITE_ALIMENTACAO_DIA = Decimal("60.00")
LIMITE_TRANSPORTE_URBANO_DIA = Decimal("80.00")
LIMITE_HOSPEDAGEM_DIARIA = Decimal("250.00")

GATILHO_NOTA_FISCAL = Decimal("100.00")

AMPLIACAO_VIAGEM = Decimal("1.5")

# RN-017/AMB-020: limiar da fila de aprovacao manual, fronteira exclusiva.
LIMITE_APROVACAO_MANUAL = Decimal("500.00")

CATEGORIA_ALIMENTACAO = "alimentacao"
CATEGORIA_TRANSPORTE_URBANO = "transporte_urbano"
CATEGORIA_HOSPEDAGEM = "hospedagem"
CATEGORIA_REPRESENTACAO = "representacao"

CATEGORIAS_OFICIAIS = {
    CATEGORIA_ALIMENTACAO,
    CATEGORIA_TRANSPORTE_URBANO,
    CATEGORIA_HOSPEDAGEM,
}

CATEGORIAS_COM_LIMITE_DIARIO = {
    CATEGORIA_ALIMENTACAO,
    CATEGORIA_TRANSPORTE_URBANO,
}

# AMB-018: representacao tem limite diario, mas nao participa da
# ampliacao de viagem de RN-006.
CATEGORIAS_SEM_AMPLIACAO_VIAGEM = {
    CATEGORIA_REPRESENTACAO,
}

# AMB-008: categorias fora da lista oficial mapeadas por analogia de natureza
# do gasto. Qualquer categoria nao mapeada aqui e recusada (RN-009).
MAPEAMENTO_ANALOGIA = {
    "coworking": CATEGORIA_HOSPEDAGEM,
}


@dataclass(frozen=True)
class TabelaPolitica:
    """Politica de reembolso completa (RN-013), independente de CC.

    `padrao` traz o limite por categoria oficial usado como fallback.
    `centros_custo` traz, por centro de custo, os limites que sobrescrevem
    o padrao para as categorias que ele lista explicitamente (AMB-013) —
    incluindo `representacao`, que so existe para quem a lista (AMB-014).
    """

    padrao: dict[str, Decimal]
    centros_custo: dict[str, dict[str, Decimal]] = field(default_factory=dict)
    gatilho_nota_fiscal: Decimal = GATILHO_NOTA_FISCAL
    ampliacao_viagem_percentual: Decimal = Decimal("50")


@dataclass(frozen=True)
class PoliticaCentroCusto:
    """Politica ja resolvida (RN-013) para um centro de custo especifico."""

    limites: dict[str, Decimal]
    gatilho_nota_fiscal: Decimal
    ampliacao_viagem: Decimal
    categorias_disponiveis: set[str]


def politica_padrao_embutida() -> TabelaPolitica:
    """Politica padrao equivalente a v3, usada quando nenhuma tabela
    externa e informada (ver spec.md secao 10, fallback de arquivo
    ausente)."""
    return TabelaPolitica(
        padrao={
            CATEGORIA_ALIMENTACAO: LIMITE_ALIMENTACAO_DIA,
            CATEGORIA_TRANSPORTE_URBANO: LIMITE_TRANSPORTE_URBANO_DIA,
            CATEGORIA_HOSPEDAGEM: LIMITE_HOSPEDAGEM_DIARIA,
        },
        centros_custo={},
        gatilho_nota_fiscal=GATILHO_NOTA_FISCAL,
        ampliacao_viagem_percentual=Decimal("50"),
    )


def carregar_tabela_politica(caminho: str | Path) -> TabelaPolitica:
    """Le `politica-v4.json` (ver exemplos/envelope/politica-v4.json)."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))

    padrao = {
        categoria: Decimal(str(valores["limite"]))
        for categoria, valores in dados["padrao"].items()
    }
    centros_custo = {
        centro: {
            categoria: Decimal(str(valores["limite"]))
            for categoria, valores in categorias.items()
        }
        for centro, categorias in dados.get("centros_custo", {}).items()
    }

    return TabelaPolitica(
        padrao=padrao,
        centros_custo=centros_custo,
        gatilho_nota_fiscal=Decimal(str(dados["nota_fiscal_obrigatoria_acima_de"])),
        ampliacao_viagem_percentual=Decimal(str(dados["acrescimo_em_viagem_percentual"])),
    )


def resolver_politica_centro_custo(
    tabela: TabelaPolitica, centro_custo: str
) -> PoliticaCentroCusto:
    """RN-013: resolve os limites efetivos para um centro de custo.

    AMB-013: categoria ausente dentro de um CC que existe parcialmente na
    tabela herda o limite do bloco `padrao` so para aquela categoria.
    AMB-014: CC totalmente ausente da tabela usa o `padrao` integralmente;
    como `representacao` nunca esta no `padrao`, esses CCs nunca a tem
    disponivel.
    """
    bloco_cc = tabela.centros_custo.get(centro_custo, {})

    limites: dict[str, Decimal] = {}
    for categoria in CATEGORIAS_OFICIAIS:
        limites[categoria] = bloco_cc.get(categoria, tabela.padrao.get(categoria, Decimal("0.00")))

    categorias_disponiveis = set(CATEGORIAS_OFICIAIS)
    if CATEGORIA_REPRESENTACAO in bloco_cc:
        limites[CATEGORIA_REPRESENTACAO] = bloco_cc[CATEGORIA_REPRESENTACAO]
        categorias_disponiveis.add(CATEGORIA_REPRESENTACAO)

    ampliacao = Decimal("1") + (tabela.ampliacao_viagem_percentual / Decimal("100"))

    return PoliticaCentroCusto(
        limites=limites,
        gatilho_nota_fiscal=tabela.gatilho_nota_fiscal,
        ampliacao_viagem=ampliacao,
        categorias_disponiveis=categorias_disponiveis,
    )
