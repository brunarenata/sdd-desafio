"""Montagem e serializacao da saida do motor de reembolso.

Ver specs/001-motor-reembolso/spec.md secao 4 (saida).
"""

from __future__ import annotations

from decimal import Decimal

from motor_reembolso.io_despesas import EntradaDespesas
from motor_reembolso.modelos import ResultadoCalculo, ResultadoDespesa, Resumo


def _montar_resumo(resultados: list[ResultadoDespesa]) -> Resumo:
    """RN-010/AMB-009: estornos (status 'ignorado') nao entram em
    total_declarado. total_recusado e a diferenca entre declarado e
    reembolsado, conforme definido na secao 4 da spec."""
    total_declarado = sum(
        (r.despesa.valor for r in resultados if r.status != "ignorado"),
        start=Decimal("0.00"),
    )
    total_reembolsado = sum(
        (r.valor_reembolsado for r in resultados), start=Decimal("0.00")
    )
    total_recusado = total_declarado - total_reembolsado
    quantidade_aprovadas = sum(1 for r in resultados if r.status != "recusado")
    quantidade_recusadas = sum(1 for r in resultados if r.status == "recusado")

    return Resumo(
        total_declarado=total_declarado,
        total_reembolsado=total_reembolsado,
        total_recusado=total_recusado,
        quantidade_despesas=len(resultados),
        quantidade_aprovadas=quantidade_aprovadas,
        quantidade_recusadas=quantidade_recusadas,
    )


def montar_resultado_calculo(
    entrada: EntradaDespesas, resultados: list[ResultadoDespesa]
) -> ResultadoCalculo:
    """Monta a estrutura interna de saida a partir do resultado do motor."""
    periodo = {
        "competencia": entrada.periodo.competencia,
        "inicio": entrada.periodo.inicio.isoformat(),
        "fim": entrada.periodo.fim.isoformat(),
    }
    return ResultadoCalculo(
        colaborador=entrada.colaborador,
        periodo=periodo,
        resultados=resultados,
        resumo=_montar_resumo(resultados),
    )


def _para_numero(valor: Decimal) -> float:
    return float(valor)


def serializar(resultado: ResultadoCalculo) -> dict:
    """Converte ResultadoCalculo para um dict pronto para `json.dump`.

    Formato conforme secao 4 da spec.
    """
    return {
        "colaborador": resultado.colaborador,
        "periodo": resultado.periodo,
        "despesas": [
            {
                "id": r.despesa.id,
                "categoria_original": r.despesa.categoria_original,
                "categoria_aplicada": r.despesa.categoria_normalizada,
                "valor_declarado": _para_numero(r.despesa.valor),
                "valor_reembolsado": _para_numero(r.valor_reembolsado),
                "status": r.status,
                "motivos": r.motivos,
                "justificativa": r.justificativa,
            }
            for r in resultado.resultados
        ],
        "resumo": {
            "total_declarado": _para_numero(resultado.resumo.total_declarado),
            "total_reembolsado": _para_numero(resultado.resumo.total_reembolsado),
            "total_recusado": _para_numero(resultado.resumo.total_recusado),
            "quantidade_despesas": resultado.resumo.quantidade_despesas,
            "quantidade_aprovadas": resultado.resumo.quantidade_aprovadas,
            "quantidade_recusadas": resultado.resumo.quantidade_recusadas,
        },
    }
