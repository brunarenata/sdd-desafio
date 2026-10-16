"""Ponto de entrada da CLI: `calcular --input despesas.json --output resultado.json`.

Ver DESAFIO.md (interface fixa) e specs/001-motor-reembolso/spec.md secao 9
(entrada invalida nao gera saida parcial).

A partir da v4 (envelope do Dia 2), aceita opcionalmente `--politica` e
`--cambio` para resolver limites por centro de custo (RN-013) e converter
despesas em moeda estrangeira (RN-015). Sem eles, usa-se a politica padrao
embutida e nenhuma despesa em moeda estrangeira e convertida (spec.md
secao 10).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from motor_reembolso import cambio, politica
from motor_reembolso.io_despesas import EntradaInvalidaError, carregar_despesas
from motor_reembolso.motor import calcular
from motor_reembolso.relatorio import montar_resultado_calculo, serializar


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="motor-reembolso",
        description="Motor de calculo de reembolso de despesas corporativas.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    calcular_parser = subparsers.add_parser(
        "calcular", help="Calcula o reembolso de um conjunto de despesas."
    )
    calcular_parser.add_argument(
        "--input", required=True, help="Caminho do JSON de despesas de entrada."
    )
    calcular_parser.add_argument(
        "--output", required=True, help="Caminho onde o JSON de resultado sera gravado."
    )
    calcular_parser.add_argument(
        "--politica",
        required=False,
        help=(
            "Caminho de politica-v4.json (limites por centro de custo). "
            "Sem este argumento, usa a politica padrao embutida (v3)."
        ),
    )
    calcular_parser.add_argument(
        "--cambio",
        required=False,
        help=(
            "Caminho de cambio.json (taxas de conversao). Sem este "
            "argumento, despesas em moeda estrangeira ficam nao_processado."
        ),
    )

    return parser


def executar_calculo(
    caminho_entrada: str,
    caminho_saida: str,
    caminho_politica: str | None = None,
    caminho_cambio: str | None = None,
) -> None:
    entrada = carregar_despesas(caminho_entrada)

    tabela_politica = None
    if caminho_politica is not None:
        try:
            tabela_politica = politica.carregar_tabela_politica(caminho_politica)
        except (OSError, ValueError, KeyError) as exc:
            raise EntradaInvalidaError(
                f"nao foi possivel carregar a politica em '{caminho_politica}': {exc}"
            ) from exc

    tabela_cambio = None
    if caminho_cambio is not None:
        try:
            tabela_cambio = cambio.carregar_tabela_cambio(caminho_cambio)
        except (OSError, ValueError, KeyError) as exc:
            raise EntradaInvalidaError(
                f"nao foi possivel carregar o cambio em '{caminho_cambio}': {exc}"
            ) from exc

    resultados = calcular(
        entrada.despesas,
        entrada.periodo.inicio,
        entrada.periodo.fim,
        tabela_politica=tabela_politica,
        tabela_cambio=tabela_cambio,
    )
    resultado = montar_resultado_calculo(entrada, resultados)
    saida = serializar(resultado)

    Path(caminho_saida).write_text(
        json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    if args.comando == "calcular":
        try:
            executar_calculo(args.input, args.output, args.politica, args.cambio)
        except EntradaInvalidaError as exc:
            print(f"erro: entrada invalida: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.error(f"comando desconhecido: {args.comando}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
