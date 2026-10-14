"""Motor de regras de negocio do calculo de reembolso.

Funcao pura: recebe despesas normalizadas e periodo, devolve resultados.
Nao faz I/O. Ver specs/001-motor-reembolso/plan.md secoes 2 e 5 (DT-002, DT-003).

A ordem das regras implementadas aqui segue a secao 8 da spec.
"""

from __future__ import annotations

from decimal import Decimal

from motor_reembolso.modelos import Despesa, ResultadoDespesa


def _regra_valor_negativo(despesa: Despesa) -> ResultadoDespesa | None:
    """RN-010: estornos (valor negativo) sao ignorados, nao recusados."""
    if despesa.valor < 0:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="ignorado",
            motivos=["RN-010"],
            justificativa="Valor negativo (estorno); despesa ignorada no calculo.",
        )
    return None
