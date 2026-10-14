"""Motor de regras de negocio do calculo de reembolso.

Funcao pura: recebe despesas normalizadas e periodo, devolve resultados.
Nao faz I/O. Ver specs/001-motor-reembolso/plan.md secoes 2 e 5 (DT-002, DT-003).

A ordem das regras implementadas aqui segue a secao 8 da spec.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from motor_reembolso import politica
from motor_reembolso.modelos import Despesa, ResultadoDespesa


def _quantizar(valor: Decimal) -> Decimal:
    """RN-011: arredondamento half-even a 2 casas decimais."""
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


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


def _regra_periodo(despesa: Despesa, inicio: date, fim: date) -> ResultadoDespesa | None:
    """RN-007: recusa despesa com data fora do periodo de competencia."""
    if not (inicio <= despesa.data <= fim):
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-007"],
            justificativa=(
                f"Data {despesa.data.isoformat()} fora do periodo de "
                f"competencia {inicio.isoformat()} a {fim.isoformat()}."
            ),
        )
    return None


def _chave_duplicata(despesa: Despesa, categoria: str) -> tuple:
    return (despesa.data, categoria, despesa.valor, despesa.fornecedor)


def _regra_duplicata(
    despesa: Despesa, categoria: str, chaves_vistas: set[tuple]
) -> ResultadoDespesa | None:
    """RN-008: recusa despesa duplicada (mesma data+categoria+valor+fornecedor).

    Muta `chaves_vistas` registrando a chave da primeira ocorrencia (menor id,
    assumindo chamadas na ordem de lancamento) como valida.
    """
    chave = _chave_duplicata(despesa, categoria)
    if chave in chaves_vistas:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-008"],
            justificativa=(
                "Duplicata de despesa com mesma data, categoria, valor e "
                "fornecedor ja processada."
            ),
        )
    chaves_vistas.add(chave)
    return None


def _regra_nota_fiscal(despesa: Despesa) -> ResultadoDespesa | None:
    """RN-005: nota fiscal obrigatoria para valor estritamente > R$100.

    AMB-003: fronteira exclusiva (R$100,00 exatos nao exigem nota).
    AMB-004: ausencia da nota exigida recusa o item integralmente.
    """
    if despesa.valor > politica.GATILHO_NOTA_FISCAL and not despesa.tem_nota_fiscal:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-005"],
            justificativa=(
                f"Valor R$ {despesa.valor} acima de R$ {politica.GATILHO_NOTA_FISCAL} "
                "exige nota fiscal, que nao foi informada."
            ),
        )
    return None


_PADRAO_DIARIAS = re.compile(r"(\d+)\s*(?:di[aá]rias?|noites?)", re.IGNORECASE)


def _extrair_numero_diarias(descricao: str) -> int | None:
    """AMB-010: extrai o numero de diarias/noites de um texto livre."""
    correspondencia = _PADRAO_DIARIAS.search(descricao)
    if correspondencia is None:
        return None
    return int(correspondencia.group(1))


def _regra_hospedagem(despesa: Despesa, categoria: str) -> ResultadoDespesa | None:
    """RN-003: limite de hospedagem por diaria.

    AMB-010: numero de diarias extraido da descricao; fallback de recusa
    quando nao identificavel. AMB-002: excedente e cortado no limite, nao
    recusa o item inteiro.
    """
    if categoria != politica.CATEGORIA_HOSPEDAGEM:
        return None

    numero_diarias = _extrair_numero_diarias(despesa.descricao)
    if numero_diarias is None or numero_diarias <= 0:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-003"],
            justificativa=(
                "Numero de diarias/noites nao identificavel na descricao; "
                "impossivel aplicar o limite por diaria com seguranca."
            ),
        )

    valor_por_diaria = _quantizar(despesa.valor / numero_diarias)
    limite_total = _quantizar(politica.LIMITE_HOSPEDAGEM_DIARIA * numero_diarias)

    if valor_por_diaria > politica.LIMITE_HOSPEDAGEM_DIARIA:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=limite_total,
            status="aprovado_parcial",
            motivos=["RN-003"],
            justificativa=(
                f"Valor por diaria R$ {valor_por_diaria} excede o limite de "
                f"R$ {politica.LIMITE_HOSPEDAGEM_DIARIA}; reembolso cortado em "
                f"R$ {limite_total} ({numero_diarias} diaria(s))."
            ),
        )

    return ResultadoDespesa(
        despesa=despesa,
        valor_reembolsado=despesa.valor,
        status="aprovado",
        motivos=["RN-003"],
        justificativa=(
            f"Dentro do limite de R$ {politica.LIMITE_HOSPEDAGEM_DIARIA}/diaria "
            f"({numero_diarias} diaria(s))."
        ),
    )


def _calcular_dias_viagem(despesas_categorizadas: list[tuple[Despesa, str | None]]) -> set[date]:
    """RN-006/AMB-005: datas em que ha hospedagem lancada contam como viagem."""
    return {
        despesa.data
        for despesa, categoria in despesas_categorizadas
        if categoria == politica.CATEGORIA_HOSPEDAGEM
    }


def _limite_diario(categoria: str, data: date, dias_viagem: set[date]) -> Decimal:
    """RN-001/RN-002 com ampliacao de RN-006 quando a data e dia de viagem."""
    if categoria == politica.CATEGORIA_ALIMENTACAO:
        limite = politica.LIMITE_ALIMENTACAO_DIA
    elif categoria == politica.CATEGORIA_TRANSPORTE_URBANO:
        limite = politica.LIMITE_TRANSPORTE_URBANO_DIA
    else:
        raise ValueError(f"categoria sem limite diario: {categoria}")

    if data in dias_viagem:
        limite = _quantizar(limite * politica.AMPLIACAO_VIAGEM)
    return limite
