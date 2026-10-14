"""Estruturas de dados internas do motor de reembolso.

Ver specs/001-motor-reembolso/plan.md secao 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

StatusDespesa = Literal["aprovado", "aprovado_parcial", "recusado", "ignorado"]


@dataclass(frozen=True)
class Despesa:
    """Uma despesa apos leitura e conversao de tipos, antes de qualquer regra."""

    id: str
    data: date
    categoria_original: str
    descricao: str
    fornecedor: str
    valor: Decimal
    tem_nota_fiscal: bool
    categoria_normalizada: str | None = None


@dataclass(frozen=True)
class ResultadoDespesa:
    """Resultado da avaliacao de uma despesa pelo motor de regras."""

    despesa: Despesa
    valor_reembolsado: Decimal
    status: StatusDespesa
    motivos: list[str] = field(default_factory=list)
    justificativa: str = ""


@dataclass(frozen=True)
class Resumo:
    """Totais agregados de uma execucao do motor."""

    total_declarado: Decimal
    total_reembolsado: Decimal
    total_recusado: Decimal
    quantidade_despesas: int
    quantidade_aprovadas: int
    quantidade_recusadas: int


@dataclass(frozen=True)
class ResultadoCalculo:
    """Saida completa do motor para um colaborador/periodo."""

    colaborador: dict
    periodo: dict
    resultados: list[ResultadoDespesa]
    resumo: Resumo
