"""Conversao de moeda estrangeira para BRL (RN-015).

Fonte: specs/001-motor-reembolso/spec.md, RN-015, AMB-015, AMB-016, AMB-017.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

MOEDA_BASE = "BRL"


class MoedaSemCotacaoError(Exception):
    """AMB-015: a moeda nunca aparece na tabela de cambio, em nenhuma data,
    ou a despesa e anterior a qualquer cotacao disponivel para ela."""

    def __init__(self, moeda: str) -> None:
        self.moeda = moeda
        super().__init__(f"moeda sem cotacao disponivel: {moeda}")


@dataclass(frozen=True)
class TabelaCambio:
    """Taxas de cambio por data (ver exemplos/envelope/cambio.json)."""

    taxas: dict[date, dict[str, Decimal]] = field(default_factory=dict)


def carregar_tabela_cambio(caminho: str | Path) -> TabelaCambio:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    taxas: dict[date, dict[str, Decimal]] = {}
    for data_str, moedas in dados["taxas"].items():
        taxas[date.fromisoformat(data_str)] = {
            moeda: Decimal(str(valor)) for moeda, valor in moedas.items()
        }
    return TabelaCambio(taxas=taxas)


def _moeda_existe_na_tabela(tabela: TabelaCambio, moeda: str) -> bool:
    return any(moeda in moedas_do_dia for moedas_do_dia in tabela.taxas.values())


def resolver_taxa(tabela: TabelaCambio, moeda: str, data: date) -> Decimal:
    """Taxa da data exata da despesa; se ausente, usa o ultimo dia util
    anterior disponivel na tabela (AMB-016). Levanta MoedaSemCotacaoError
    se a moeda nunca aparecer na tabela, ou se nao houver nenhuma data
    anterior ou igual com cotacao para ela (AMB-015)."""
    if not _moeda_existe_na_tabela(tabela, moeda):
        raise MoedaSemCotacaoError(moeda)

    datas_com_cotacao = sorted(
        d for d, moedas_do_dia in tabela.taxas.items() if moeda in moedas_do_dia
    )
    candidatas = [d for d in datas_com_cotacao if d <= data]
    if not candidatas:
        raise MoedaSemCotacaoError(moeda)

    data_resolvida = max(candidatas)
    return tabela.taxas[data_resolvida][moeda]


def converter_para_brl(
    valor: Decimal, moeda: str, data: date, tabela: TabelaCambio
) -> Decimal:
    """RN-015: converte `valor` (na moeda informada) para BRL usando a
    taxa da data da despesa. Despesas em BRL retornam o valor inalterado."""
    if moeda == MOEDA_BASE:
        return valor
    taxa = resolver_taxa(tabela, moeda, data)
    return valor * taxa
