# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [ ] **T-001** — Estrutura do projeto Python (pacote `src/motor_reembolso`, `pyproject.toml`/`requirements.txt`, config do pytest)
  - **Atende:** base para todas as regras
  - **Aceite:** `pytest` roda (mesmo sem testes ainda) sem erro de import
  - **Commit:**

- [ ] **T-002** — Modelos de dados (`modelos.py`): `Despesa`, `ResultadoDespesa`, `Resumo`, `ResultadoCalculo`
  - **Atende:** seção 3 do plan.md
  - **Aceite:** teste instancia cada estrutura com dados mínimos sem erro
  - **Commit:**

- [ ] **T-003** — Constantes de política (`politica.py`): limites, gatilho de nota fiscal, ampliação de viagem, categorias oficiais, mapeamento de analogia
  - **Atende:** seção 4 do plan.md
  - **Aceite:** teste importa e lê cada constante com o valor esperado
  - **Commit:**

- [ ] **T-004** — Leitura e validação de entrada (`io_despesas.py`): parse do JSON, conversão de valores para `Decimal`, erro claro em campo obrigatório ausente/tipo errado
  - **Atende:** seção 4 (entrada) da spec; critério de aceite "entrada inválida produz erro claro"
  - **Aceite:** `test_io_despesas.py::test_le_exemplo_oficial` carrega `exemplos/despesas-exemplo.json` com 14 despesas; `test_io_despesas.py::test_rejeita_campo_ausente` levanta exceção
  - **Commit:**

## Fase 2 — Regras de negócio (motor puro)

- [ ] **T-005** — RN-010: ignora despesas de valor negativo
  - **Atende:** RN-010, AMB-009
  - **Aceite:** `test_motor.py::test_rn_010_estorno_ignorado` (d-009) passa
  - **Commit:**

- [ ] **T-006** — RN-012 + RN-009: normalização de categoria (case-insensitive) e mapeamento por analogia (`coworking`→`hospedagem`); recusa categoria não mapeável
  - **Atende:** RN-009, RN-012, AMB-008, AMB-012
  - **Aceite:** `test_motor.py::test_rn_012_categoria_maiuscula` (d-014) e `test_motor.py::test_rn_009_categoria_mapeada` (d-005) passam
  - **Commit:**

- [ ] **T-007** — RN-007: recusa despesa fora do período de competência
  - **Atende:** RN-007, AMB-006
  - **Aceite:** `test_motor.py::test_rn_007_fora_periodo` (d-008) passa
  - **Commit:**

- [ ] **T-008** — RN-008: detecção e recusa de duplicatas (mesma data+categoria+valor+fornecedor, mantém menor id)
  - **Atende:** RN-008, AMB-007
  - **Aceite:** `test_motor.py::test_rn_008_duplicata` (d-006/d-007) passa
  - **Commit:**

- [ ] **T-009** — RN-005: nota fiscal obrigatória acima de R$100 (fronteira exclusiva), recusa total quando ausente
  - **Atende:** RN-005, AMB-003, AMB-004
  - **Aceite:** `test_motor.py::test_rn_005_limite_sem_nota_na_fronteira` (d-003) e `test_motor.py::test_rn_005_acima_sem_nota` (d-004) passam
  - **Commit:**

- [ ] **T-010** — RN-003: limite de hospedagem por diária, com extração de nº de diárias/noites da descrição e fallback de recusa
  - **Atende:** RN-003, AMB-010
  - **Aceite:** `test_motor.py::test_rn_003_hospedagem_duas_diarias` (d-010), `test_motor.py::test_rn_003_hospedagem_tres_noites` (d-013) e `test_motor.py::test_rn_003_sem_diarias_recusa` (caso sintético) passam
  - **Commit:**

- [ ] **T-011** — RN-006: inferência de viagem pela data de hospedagem e ampliação de 50% nos limites de alimentação/transporte urbano naquela data
  - **Atende:** RN-006, AMB-005
  - **Aceite:** `test_motor.py::test_rn_006_ampliacao_viagem` (caso sintético com alimentação na data de d-010) passa
  - **Commit:**

- [ ] **T-012** — RN-001/RN-002/RN-004: agregação diária de alimentação e transporte urbano, limite e corte sequencial por ordem de lançamento
  - **Atende:** RN-001, RN-002, RN-004, AMB-001, AMB-002
  - **Aceite:** `test_motor.py::test_rn_001_soma_dia_alimentacao` (d-001/d-002) e `test_motor.py::test_rn_002_transporte_dentro_limite` passam
  - **Commit:**

- [ ] **T-013** — RN-011: arredondamento half-even a 2 casas aplicado em toda entrada e saída monetária
  - **Atende:** RN-011, AMB-011
  - **Aceite:** `test_motor.py::test_rn_011_arredondamento` (d-011, 33.333→33.33) passa
  - **Commit:**

- [ ] **T-014** — Orquestração do pipeline do motor (`motor.py::calcular`): ordem de regras da seção 8 da spec, com corte antecipado por despesa
  - **Atende:** seção 8 da spec (ordem de aplicação)
  - **Aceite:** `test_motor.py::test_ordem_regras_despesa_fora_periodo_nao_consome_limite` passa
  - **Commit:**

## Fase 3 — Casos de borda

- [ ] **T-015** — Casos de borda da seção 7 da spec não cobertos pelas tasks acima (ex.: fim de semana sem regra especial)
  - **Atende:** seção 7 da spec
  - **Aceite:** `test_motor.py::test_borda_fim_de_semana_sem_regra_especial` (d-012) passa
  - **Commit:**

- [ ] **T-016** — Invariante de soma (`total_declarado = total_reembolsado + total_recusado`) como teste de propriedade sobre o exemplo oficial completo
  - **Atende:** critério de aceite da seção 9 da spec
  - **Aceite:** `test_motor.py::test_invariante_soma_totais` passa com `despesas-exemplo.json`
  - **Commit:**

## Fase 4 — Saída e CLI

- [ ] **T-017** — Montagem do relatório de saída (`relatorio.py`): resumo agregado + lista de despesas no formato da seção 4 da spec
  - **Atende:** seção 4 da spec (saída)
  - **Aceite:** `test_relatorio.py::test_formato_saida` valida chaves e tipos de cada campo
  - **Commit:**

- [ ] **T-018** — CLI (`cli.py`): comando `calcular --input --output`, orquestra `io_despesas → motor → relatorio`, grava arquivo
  - **Atende:** interface fixa do DESAFIO.md
  - **Aceite:** `test_cli.py::test_cli_processa_exemplo_oficial` roda a CLI contra `exemplos/despesas-exemplo.json` e confere a saída completa
  - **Commit:**

- [ ] **T-019** — Tratamento de erro de entrada na CLI (JSON malformado / campo ausente não gera saída parcial)
  - **Atende:** critério de aceite da seção 9 da spec
  - **Aceite:** `test_cli.py::test_cli_entrada_invalida_nao_gera_saida` passa
  - **Commit:**

- [ ] **T-020** — README.md do projeto com instruções reais de instalação, execução e teste
  - **Atende:** penalidade transversal da rubrica (README precisa permitir rodar o projeto)
  - **Aceite:** seguir o README do zero roda `calcular` sobre o exemplo oficial com sucesso
  - **Commit:**

---

## Fase 5 — Envelope (criar no Dia 2)

<Novas tasks a partir da mudança de requisito. Numeração continua de onde parou —
não reinicie e não renumere as antigas: a numeração é o eixo da rastreabilidade.>

---

## Cobertura

Preencha ao fechar cada fase. É a sua própria checagem de rastreabilidade — e é
exatamente a matriz que a correção vai montar.

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-012 | `test_rn_001_soma_dia_alimentacao` |
| RN-002 | T-012 | `test_rn_002_transporte_dentro_limite` |
| RN-003 | T-010 | `test_rn_003_hospedagem_duas_diarias`, `test_rn_003_hospedagem_tres_noites`, `test_rn_003_sem_diarias_recusa` |
| RN-004 | T-012 | `test_rn_001_soma_dia_alimentacao` |
| RN-005 | T-009 | `test_rn_005_limite_sem_nota_na_fronteira`, `test_rn_005_acima_sem_nota` |
| RN-006 | T-011 | `test_rn_006_ampliacao_viagem` |
| RN-007 | T-007 | `test_rn_007_fora_periodo` |
| RN-008 | T-008 | `test_rn_008_duplicata` |
| RN-009 | T-006 | `test_rn_009_categoria_mapeada` |
| RN-010 | T-005 | `test_rn_010_estorno_ignorado` |
| RN-011 | T-013 | `test_rn_011_arredondamento` |
| RN-012 | T-006 | `test_rn_012_categoria_maiuscula` |
| AMB-001..012 | ver RN correspondente na seção 5/6 da spec | — |
| Ordem de aplicação (seção 8) | T-014 | `test_ordem_regras_despesa_fora_periodo_nao_consome_limite` |
| Invariante de soma (seção 9) | T-016 | `test_invariante_soma_totais` |
