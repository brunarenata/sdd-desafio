"""Ponto de entrada da CLI: `calcular --input despesas.json --output resultado.json`.

Ver DESAFIO.md (interface fixa) e specs/001-motor-reembolso/spec.md secao 9
(entrada invalida nao gera saida parcial).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

    return parser


def executar_calculo(caminho_entrada: str, caminho_saida: str) -> None:
    entrada = carregar_despesas(caminho_entrada)
    resultados = calcular(entrada.despesas, entrada.periodo.inicio, entrada.periodo.fim)
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
            executar_calculo(args.input, args.output)
        except EntradaInvalidaError as exc:
            print(f"erro: entrada invalida: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.error(f"comando desconhecido: {args.comando}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
