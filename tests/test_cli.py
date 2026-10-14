import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO_OFICIAL = RAIZ / "exemplos" / "despesas-exemplo.json"


def _rodar_cli(*args: str) -> subprocess.CompletedProcess:
    env = {"PYTHONPATH": str(RAIZ / "src")}
    import os

    env = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, "-m", "motor_reembolso.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_processa_exemplo_oficial(tmp_path):
    saida = tmp_path / "resultado.json"
    resultado = _rodar_cli(
        "calcular", "--input", str(EXEMPLO_OFICIAL), "--output", str(saida)
    )

    assert resultado.returncode == 0, resultado.stderr
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["colaborador"]["id"] == "c-0417"
    assert len(dados["despesas"]) == 14
    assert dados["resumo"]["quantidade_despesas"] == 14


def test_cli_entrada_invalida_nao_gera_saida(tmp_path):
    entrada_invalida = tmp_path / "invalido.json"
    entrada_invalida.write_text("{nao-e-json", encoding="utf-8")
    saida = tmp_path / "resultado.json"

    resultado = _rodar_cli(
        "calcular", "--input", str(entrada_invalida), "--output", str(saida)
    )

    assert resultado.returncode != 0
    assert "entrada invalida" in resultado.stderr
    assert not saida.exists()


def test_cli_arquivo_inexistente_nao_gera_saida(tmp_path):
    saida = tmp_path / "resultado.json"
    resultado = _rodar_cli(
        "calcular", "--input", str(tmp_path / "nao-existe.json"), "--output", str(saida)
    )

    assert resultado.returncode != 0
    assert not saida.exists()
