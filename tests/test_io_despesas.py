import json
from decimal import Decimal
from pathlib import Path

import pytest

from motor_reembolso.io_despesas import EntradaInvalidaError, carregar_despesas

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO_OFICIAL = RAIZ / "exemplos" / "despesas-exemplo.json"


def test_le_exemplo_oficial():
    entrada = carregar_despesas(EXEMPLO_OFICIAL)
    assert entrada.colaborador["id"] == "c-0417"
    assert entrada.periodo.competencia == "2026-07"
    assert len(entrada.despesas) == 14


def test_converte_valor_para_decimal_arredondado():
    entrada = carregar_despesas(EXEMPLO_OFICIAL)
    d011 = next(d for d in entrada.despesas if d.id == "d-011")
    assert d011.valor == Decimal("33.33")


def test_rejeita_campo_ausente(tmp_path):
    dados = {"colaborador": {"id": "c-1", "nome": "x", "centro_custo": "y"}, "periodo": {}}
    caminho = tmp_path / "invalido.json"
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    with pytest.raises(EntradaInvalidaError):
        carregar_despesas(caminho)


def test_rejeita_json_malformado(tmp_path):
    caminho = tmp_path / "malformado.json"
    caminho.write_text("{nao-e-json", encoding="utf-8")
    with pytest.raises(EntradaInvalidaError):
        carregar_despesas(caminho)


def test_rejeita_arquivo_inexistente():
    with pytest.raises(EntradaInvalidaError):
        carregar_despesas("caminho/que/nao/existe.json")
