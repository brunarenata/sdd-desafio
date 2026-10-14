"""Motor de regras de negocio do calculo de reembolso.

Funcao pura: recebe despesas normalizadas e periodo, devolve resultados.
Nao faz I/O. Ver specs/001-motor-reembolso/plan.md secoes 2 e 5 (DT-002, DT-003).

A ordem das regras implementadas aqui segue a secao 8 da spec.
"""

from __future__ import annotations

from decimal import Decimal

from motor_reembolso import politica
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


def _normalizar_categoria(despesa: Despesa) -> str | None:
    """RN-012: normaliza para minusculas. RN-009: mapeia por analogia.

    Devolve a categoria oficial aplicavel, ou None se nao reconhecida/mapeavel.
    """
    categoria = despesa.categoria_original.strip().lower()
    if categoria in politica.CATEGORIAS_OFICIAIS:
        return categoria
    return politica.MAPEAMENTO_ANALOGIA.get(categoria)


def _regra_categoria(despesa: Despesa) -> tuple[ResultadoDespesa | None, str | None]:
    """RN-009: recusa categoria fora da politica e sem mapeamento de analogia.

    Devolve (resultado_de_recusa_ou_None, categoria_normalizada_ou_None).
    """
    categoria = _normalizar_categoria(despesa)
    if categoria is None:
        resultado = ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-009"],
            justificativa=(
                f"Categoria '{despesa.categoria_original}' fora da politica "
                "e sem mapeamento por analogia; nao reembolsavel."
            ),
        )
        return resultado, None
    return None, categoria
