import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO_OFICIAL = RAIZ / "exemplos" / "despesas-exemplo.json"
ENVELOPE_DESPESAS = RAIZ / "exemplos" / "envelope" / "despesas-envelope.json"
ENVELOPE_CC_DESCONHECIDO = RAIZ / "exemplos" / "envelope" / "despesas-envelope-cc-desconhecido.json"
ENVELOPE_POLITICA = RAIZ / "exemplos" / "envelope" / "politica-v4.json"
ENVELOPE_CAMBIO = RAIZ / "exemplos" / "envelope" / "cambio.json"


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


def test_cli_processa_envelope_v4_cc_comercial(tmp_path):
    """T-030: ponta a ponta com os arquivos do envelope do Dia 2 e os
    argumentos --politica/--cambio."""
    saida = tmp_path / "resultado.json"
    resultado = _rodar_cli(
        "calcular",
        "--input", str(ENVELOPE_DESPESAS),
        "--output", str(saida),
        "--politica", str(ENVELOPE_POLITICA),
        "--cambio", str(ENVELOPE_CAMBIO),
    )

    assert resultado.returncode == 0, resultado.stderr
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["colaborador"]["id"] == "c-0912"
    assert len(dados["despesas"]) == 10

    por_id = {d["id"]: d for d in dados["despesas"]}
    assert por_id["e-001"]["status"] == "aprovado_parcial"
    assert por_id["e-001"]["valor_reembolsado"] == 300.0
    assert por_id["e-006"]["status"] == "nao_processado"
    assert por_id["e-007"]["status"] == "pendente"
    assert por_id["e-007"]["valor_reembolsado"] == 1200.0

    resumo = dados["resumo"]
    assert resumo["quantidade_despesas"] == 10
    assert resumo["quantidade_pendentes"] == 1
    assert round(resumo["total_reembolsado"] + resumo["total_recusado"], 2) == round(
        resumo["total_declarado"], 2
    )


def test_cli_processa_envelope_v4_cc_desconhecido(tmp_path):
    """AMB-014: centro de custo ausente da tabela usa a politica padrao
    integral; representacao fica fora da politica para ele."""
    saida = tmp_path / "resultado.json"
    resultado = _rodar_cli(
        "calcular",
        "--input", str(ENVELOPE_CC_DESCONHECIDO),
        "--output", str(saida),
        "--politica", str(ENVELOPE_POLITICA),
        "--cambio", str(ENVELOPE_CAMBIO),
    )

    assert resultado.returncode == 0, resultado.stderr
    dados = json.loads(saida.read_text(encoding="utf-8"))
    por_id = {d["id"]: d for d in dados["despesas"]}
    assert por_id["f-001"]["status"] == "aprovado"
    assert por_id["f-002"]["status"] == "aprovado_parcial"
    assert por_id["f-002"]["valor_reembolsado"] == 250.0
    assert por_id["f-003"]["status"] == "recusado"
    assert "RN-009" in por_id["f-003"]["motivos"]
    assert por_id["f-004"]["status"] == "aprovado"


def test_cli_sem_politica_e_cambio_usa_fallback_v3(tmp_path):
    """Sem --politica/--cambio, a CLI continua funcionando sobre o
    exemplo oficial v3 sem regressao."""
    saida = tmp_path / "resultado.json"
    resultado = _rodar_cli(
        "calcular", "--input", str(EXEMPLO_OFICIAL), "--output", str(saida)
    )

    assert resultado.returncode == 0, resultado.stderr
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["resumo"]["quantidade_despesas"] == 14
    assert dados["resumo"]["quantidade_pendentes"] == 0
