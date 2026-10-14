"""Leitura e validacao do JSON de entrada.

Ver specs/001-motor-reembolso/spec.md secao 4 (entrada) e secao 9
(criterio de aceite "entrada invalida produz erro claro").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path

from motor_reembolso.modelos import Despesa

CAMPOS_OBRIGATORIOS_DESPESA = (
    "id",
    "data",
    "categoria",
    "descricao",
    "fornecedor",
    "valor",
    "tem_nota_fiscal",
)


class EntradaInvalidaError(Exception):
    """Levantada quando o JSON de entrada e malformado ou incompleto."""


@dataclass(frozen=True)
class Periodo:
    competencia: str
    inicio: date
    fim: date


@dataclass(frozen=True)
class EntradaDespesas:
    colaborador: dict
    periodo: Periodo
    despesas: list[Despesa]


def _quantizar(valor: Decimal) -> Decimal:
    """RN-011: arredondamento half-even a 2 casas decimais."""
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def _parse_data(valor: str, contexto: str) -> date:
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError) as exc:
        raise EntradaInvalidaError(
            f"{contexto}: data invalida '{valor}', esperado formato AAAA-MM-DD"
        ) from exc


def _parse_valor(valor, contexto: str) -> Decimal:
    try:
        return _quantizar(Decimal(str(valor)))
    except (InvalidOperation, TypeError) as exc:
        raise EntradaInvalidaError(
            f"{contexto}: valor invalido '{valor}', esperado numero"
        ) from exc


def _validar_campos(dados: dict, campos: tuple[str, ...], contexto: str) -> None:
    ausentes = [campo for campo in campos if campo not in dados]
    if ausentes:
        raise EntradaInvalidaError(
            f"{contexto}: campo(s) obrigatorio(s) ausente(s): {', '.join(ausentes)}"
        )


def _parse_despesa(dados: dict, indice: int) -> Despesa:
    contexto = f"despesas[{indice}]"
    if not isinstance(dados, dict):
        raise EntradaInvalidaError(f"{contexto}: deve ser um objeto")
    _validar_campos(dados, CAMPOS_OBRIGATORIOS_DESPESA, contexto)

    if not isinstance(dados["tem_nota_fiscal"], bool):
        raise EntradaInvalidaError(
            f"{contexto}: 'tem_nota_fiscal' deve ser booleano"
        )

    return Despesa(
        id=str(dados["id"]),
        data=_parse_data(dados["data"], contexto),
        categoria_original=str(dados["categoria"]),
        descricao=str(dados["descricao"]),
        fornecedor=str(dados["fornecedor"]),
        valor=_parse_valor(dados["valor"], contexto),
        tem_nota_fiscal=dados["tem_nota_fiscal"],
    )


def carregar_despesas(caminho: str | Path) -> EntradaDespesas:
    """Le e valida o JSON de entrada, convertendo tipos para uso interno.

    Levanta EntradaInvalidaError para qualquer problema estrutural, sem
    gerar nenhum resultado parcial.
    """
    caminho = Path(caminho)
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        raise EntradaInvalidaError(f"nao foi possivel ler o arquivo: {exc}") from exc

    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise EntradaInvalidaError(f"JSON malformado: {exc}") from exc

    if not isinstance(dados, dict):
        raise EntradaInvalidaError("entrada deve ser um objeto JSON")

    _validar_campos(dados, ("colaborador", "periodo", "despesas"), "entrada")

    colaborador = dados["colaborador"]
    if not isinstance(colaborador, dict):
        raise EntradaInvalidaError("colaborador: deve ser um objeto")
    _validar_campos(colaborador, ("id", "nome", "centro_custo"), "colaborador")

    periodo_dados = dados["periodo"]
    if not isinstance(periodo_dados, dict):
        raise EntradaInvalidaError("periodo: deve ser um objeto")
    _validar_campos(periodo_dados, ("competencia", "inicio", "fim"), "periodo")
    periodo = Periodo(
        competencia=str(periodo_dados["competencia"]),
        inicio=_parse_data(periodo_dados["inicio"], "periodo.inicio"),
        fim=_parse_data(periodo_dados["fim"], "periodo.fim"),
    )

    lista_despesas = dados["despesas"]
    if not isinstance(lista_despesas, list):
        raise EntradaInvalidaError("despesas: deve ser uma lista")

    despesas = [_parse_despesa(item, i) for i, item in enumerate(lista_despesas)]

    return EntradaDespesas(colaborador=colaborador, periodo=periodo, despesas=despesas)
