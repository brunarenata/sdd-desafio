# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [x] **T-001** — Estrutura do projeto Python (pacote `src/motor_reembolso`, `pyproject.toml`/`requirements.txt`, config do pytest)
  - **Atende:** base para todas as regras
  - **Aceite:** `pytest` roda (mesmo sem testes ainda) sem erro de import
  - **Commit:** `b10854d`

- [x] **T-002** — Modelos de dados (`modelos.py`): `Despesa`, `ResultadoDespesa`, `Resumo`, `ResultadoCalculo`
  - **Atende:** seção 3 do plan.md
  - **Aceite:** teste instancia cada estrutura com dados mínimos sem erro
  - **Commit:** `19cd342`

- [x] **T-003** — Constantes de política (`politica.py`): limites, gatilho de nota fiscal, ampliação de viagem, categorias oficiais, mapeamento de analogia
  - **Atende:** seção 4 do plan.md
  - **Aceite:** teste importa e lê cada constante com o valor esperado
  - **Commit:** `4ee9723`

- [x] **T-004** — Leitura e validação de entrada (`io_despesas.py`): parse do JSON, conversão de valores para `Decimal`, erro claro em campo obrigatório ausente/tipo errado
  - **Atende:** seção 4 (entrada) da spec; critério de aceite "entrada inválida produz erro claro"
  - **Aceite:** `test_io_despesas.py::test_le_exemplo_oficial` carrega `exemplos/despesas-exemplo.json` com 14 despesas; `test_io_despesas.py::test_rejeita_campo_ausente` levanta exceção
  - **Commit:** `1586dcb`

## Fase 2 — Regras de negócio (motor puro)

- [x] **T-005** — RN-010: ignora despesas de valor negativo
  - **Atende:** RN-010, AMB-009
  - **Aceite:** `test_motor.py::test_rn_010_estorno_ignorado` (d-009) passa
  - **Commit:** `26c4f5f`

- [x] **T-006** — RN-012 + RN-009: normalização de categoria (case-insensitive) e mapeamento por analogia (`coworking`→`hospedagem`); recusa categoria não mapeável
  - **Atende:** RN-009, RN-012, AMB-008, AMB-012
  - **Aceite:** `test_motor.py::test_rn_012_categoria_maiuscula` (d-014) e `test_motor.py::test_rn_009_categoria_mapeada` (d-005) passam
  - **Commit:** `0844c2a`

- [x] **T-007** — RN-007: recusa despesa fora do período de competência
  - **Atende:** RN-007, AMB-006
  - **Aceite:** `test_motor.py::test_rn_007_fora_periodo` (d-008) passa
  - **Commit:** `ed10c22`

- [x] **T-008** — RN-008: detecção e recusa de duplicatas (mesma data+categoria+valor+fornecedor, mantém menor id)
  - **Atende:** RN-008, AMB-007
  - **Aceite:** `test_motor.py::test_rn_008_duplicata` (d-006/d-007) passa
  - **Commit:** `bfe11c5`

- [x] **T-009** — RN-005: nota fiscal obrigatória acima de R$100 (fronteira exclusiva), recusa total quando ausente
  - **Atende:** RN-005, AMB-003, AMB-004
  - **Aceite:** `test_motor.py::test_rn_005_limite_sem_nota_na_fronteira` (d-003) e `test_motor.py::test_rn_005_acima_sem_nota` (d-004) passam
  - **Commit:** `f2fa766`

- [x] **T-010** — RN-003: limite de hospedagem por diária, com extração de nº de diárias/noites da descrição e fallback de recusa
  - **Atende:** RN-003, AMB-010
  - **Aceite:** `test_motor.py::test_rn_003_hospedagem_duas_diarias` (d-010), `test_motor.py::test_rn_003_hospedagem_tres_noites` (d-013) e `test_motor.py::test_rn_003_sem_diarias_recusa` (caso sintético) passam
  - **Commit:** `79bc955`

- [x] **T-011** — RN-006: inferência de viagem pela data de hospedagem e ampliação de 50% nos limites de alimentação/transporte urbano naquela data
  - **Atende:** RN-006, AMB-005
  - **Aceite:** `test_motor.py::test_rn_006_ampliacao_viagem` (caso sintético com alimentação na data de d-010) passa
  - **Commit:** `e405b51`

- [x] **T-012** — RN-001/RN-002/RN-004: agregação diária de alimentação e transporte urbano, limite e corte sequencial por ordem de lançamento
  - **Atende:** RN-001, RN-002, RN-004, AMB-001, AMB-002
  - **Aceite:** `test_motor.py::test_rn_001_soma_dia_alimentacao` (d-001/d-002) e `test_motor.py::test_rn_002_transporte_dentro_limite` passam
  - **Commit:** `7078ea4`

- [x] **T-013** — RN-011: arredondamento half-even a 2 casas aplicado em toda entrada e saída monetária
  - **Atende:** RN-011, AMB-011
  - **Aceite:** `test_motor.py::test_rn_011_arredondamento` (d-011, 33.333→33.33) passa
  - **Commit:** `fbad5f1`

- [x] **T-014** — Orquestração do pipeline do motor (`motor.py::calcular`): ordem de regras da seção 8 da spec, com corte antecipado por despesa
  - **Atende:** seção 8 da spec (ordem de aplicação)
  - **Aceite:** `test_motor.py::test_ordem_regras_estrutural_nao_consome_limite_diario` passa (renomeado de `test_ordem_regras_despesa_fora_periodo_nao_consome_limite`: o cenário de "despesa fora do período" é logicamente impossível de coexistir no mesmo dia com uma despesa dentro do período, já que ambas compartilham a mesma data; o teste real cobre duplicata, que é o cenário estrutural genuíno)
  - **Commit:** `e51b294`

## Fase 3 — Casos de borda

- [x] **T-015** — Casos de borda da seção 7 da spec não cobertos pelas tasks acima (ex.: fim de semana sem regra especial)
  - **Atende:** seção 7 da spec
  - **Aceite:** `test_motor.py::test_borda_fim_de_semana_sem_regra_especial` (d-012) passa
  - **Commit:** `e51b294`

- [x] **T-016** — Invariante de soma (`total_declarado = total_reembolsado + total_recusado`) como teste de propriedade sobre o exemplo oficial completo
  - **Atende:** critério de aceite da seção 9 da spec
  - **Aceite:** `test_relatorio.py::test_invariante_soma_totais_exemplo_oficial` passa com `despesas-exemplo.json` (movido para `test_relatorio.py` porque a invariante só existe depois que o `resumo` é montado por `relatorio.py`, criado na T-017)
  - **Commit:** `731f836`

## Fase 4 — Saída e CLI

- [x] **T-017** — Montagem do relatório de saída (`relatorio.py`): resumo agregado + lista de despesas no formato da seção 4 da spec
  - **Atende:** seção 4 da spec (saída)
  - **Aceite:** `test_relatorio.py::test_formato_saida` valida chaves e tipos de cada campo
  - **Commit:** `731f836`

- [x] **T-018** — CLI (`cli.py`): comando `calcular --input --output`, orquestra `io_despesas → motor → relatorio`, grava arquivo
  - **Atende:** interface fixa do DESAFIO.md
  - **Aceite:** `test_cli.py::test_cli_processa_exemplo_oficial` roda a CLI contra `exemplos/despesas-exemplo.json` e confere a saída completa
  - **Commit:** `12f27cb`

- [x] **T-019** — Tratamento de erro de entrada na CLI (JSON malformado / campo ausente não gera saída parcial)
  - **Atende:** critério de aceite da seção 9 da spec
  - **Aceite:** `test_cli.py::test_cli_entrada_invalida_nao_gera_saida` passa
  - **Commit:** `12f27cb`

- [x] **T-020** — README.md do projeto com instruções reais de instalação, execução e teste
  - **Atende:** penalidade transversal da rubrica (README precisa permitir rodar o projeto)
  - **Aceite:** seguir o README do zero roda `calcular` sobre o exemplo oficial com sucesso
  - **Commit:** `65cb420`

---

## Fase 5 — Envelope (Política de Reembolso v4, Dia 2)

> Numeração continua de T-020. Ver `DECISIONS.md` (entrada 2026-10-15,
> "Absorção do envelope do Dia 2") para o que mudou e por quê, e `spec.md`
> seção 5/6 para as regras e ambiguidades novas (RN-013 a RN-017, AMB-013
> a AMB-023).

- [x] **T-021** — Carregamento de política externa (`politica.py`): função
  que lê `politica-v4.json`, resolve limites/gatilho/ampliação por
  `centro_custo` com fallback para o bloco `padrao` (categoria ausente
  dentro de um CC existente) e para o `padrao` integral (CC ausente da
  tabela); mantém as constantes atuais como política padrão embutida
  quando nenhum arquivo é informado
  - **Atende:** RN-013, AMB-013, AMB-014
  - **Aceite:** `test_politica.py::test_rn_013_resolve_limite_especifico_do_cc`,
    `test_amb_013_categoria_ausente_herda_padrao`,
    `test_amb_014_cc_ausente_usa_padrao_integral_sem_representacao`
  - **Commit:** `<pendente>`

- [x] **T-022** — Campos novos no modelo de dados (`modelos.py`,
  `io_despesas.py`): `Despesa.moeda` (opcional, default `BRL`) e
  propagação de `centro_custo` até o ponto de cálculo
  - **Atende:** seção 3/4 da spec (entrada), base para RN-013 a RN-017
  - **Aceite:** `test_modelos.py::test_despesa_aceita_moeda_e_centro_custo`,
    `test_despesa_moeda_padrao_e_brl`
  - **Commit:** `<pendente>`

- [x] **T-023** — RN-015: conversão de moeda estrangeira (taxa da data da
  despesa, fallback de último dia útil anterior, `status: nao_processado`
  quando a moeda não existe na tabela em nenhuma data)
  - **Atende:** RN-015, AMB-015, AMB-016, AMB-017
  - **Aceite:** `test_cambio.py::test_rn_015_converte_moeda_na_data_exata`,
    `test_amb_016_data_sem_cotacao_usa_ultimo_dia_util_anterior`,
    `test_amb_015_moeda_sem_cotacao_levanta_erro`;
    `test_motor.py::test_rn_015_conversao_moeda_antes_de_demais_regras`,
    `test_amb_016_conversao_usa_ultimo_dia_util_anterior`,
    `test_amb_015_moeda_sem_cotacao_fica_nao_processado`
  - **Commit:** `<pendente>`

- [x] **T-024** — RN-013/RN-014: categoria `representacao` condicional ao
  centro de custo e resolução de limite diário/por diária pela tabela de
  política (ajusta `_regra_categoria` e a agregação diária)
  - **Atende:** RN-013, RN-014, RN-009 (atualizada)
  - **Aceite:** `test_motor.py::test_rn_014_representacao_aprovada_para_cc_que_lista`,
    `test_amb_014_representacao_recusada_para_cc_ausente_da_tabela`
  - **Commit:** `<pendente>`

- [x] **T-025** — RN-016: hospedagem não reembolsável por política do
  centro de custo (`limite: 0.00` explícito), motivo próprio distinto de
  AMB-010b
  - **Atende:** RN-016, AMB-019
  - **Aceite:** `test_motor.py::test_rn_016_hospedagem_zerada_por_politica_do_cc`,
    `test_amb_019_hospedagem_zerada_distingue_de_diarias_nao_identificaveis`
  - **Commit:** `<pendente>`

- [x] **T-026** — RN-006 ajustada: ampliação de viagem usa o percentual e
  os limites vigentes da política por CC, e não se aplica a `representacao`
  - **Atende:** RN-006 (atualizada), AMB-018
  - **Aceite:** `test_motor.py::test_amb_018_representacao_nao_recebe_ampliacao_de_viagem`
  - **Commit:** `<pendente>`

- [x] **T-027** — RN-017: fila de aprovação manual (`valor_reembolsado` >
  R$500,00 substitui `aprovado`/`aprovado_parcial` por `pendente`)
  - **Atende:** RN-017, AMB-020, AMB-021
  - **Aceite:** `test_motor.py::test_rn_017_fila_aprovacao_manual_acima_de_500`,
    `test_amb_020_limite_de_500_exato_nao_entra_na_fila`,
    `test_amb_021_despesa_recusada_nunca_entra_na_fila`
  - **Commit:** `<pendente>`

- [x] **T-028** — `relatorio.py`: campo novo `resumo.quantidade_pendentes`
  e redefinição de `quantidade_aprovadas` como conjunto explícito
  `{aprovado, aprovado_parcial}`
  - **Atende:** seção 4 da spec (saída), AMB-022, AMB-023
  - **Aceite:** `test_relatorio.py::test_amb_022_quantidade_pendentes_separada_de_aprovadas`,
    `test_amb_023_ignorado_nao_conta_como_aprovado`,
    `test_amb_015_nao_processado_excluido_do_total_declarado`
  - **Commit:** `<pendente>`

- [x] **T-029** — `cli.py`: argumentos opcionais `--politica` e `--cambio`
  (caminhos para `politica-v4.json`/`cambio.json`); sem eles, usa a
  política padrão embutida e nunca converte moeda
  - **Atende:** seção 4 da spec (entrada adicional), seção 10 (fallback)
  - **Aceite:** `test_cli.py::test_cli_sem_politica_e_cambio_usa_fallback_v3`
  - **Commit:** `<pendente>`

- [x] **T-030** — Teste de integração ponta a ponta com
  `exemplos/envelope/despesas-envelope.json` e
  `exemplos/envelope/despesas-envelope-cc-desconhecido.json`
  - **Atende:** critérios de aceite novos da seção 9 da spec
  - **Aceite:** `test_cli.py::test_cli_processa_envelope_v4_cc_comercial`,
    `test_cli_processa_envelope_v4_cc_desconhecido`
  - **Commit:** `<pendente>`

- [x] **T-031** — README.md atualizado com os novos argumentos de CLI e
  um exemplo de execução contra o envelope
  - **Atende:** penalidade transversal da rubrica (README precisa cobrir
    o estado atual do projeto)
  - **Aceite:** seguir o README do zero roda `calcular` sobre
    `despesas-envelope.json` com `--politica`/`--cambio` com sucesso
  - **Commit:** `<pendente>`

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
| RN-013 | T-021, T-024 | `test_rn_013_resolve_limite_especifico_do_cc`, `test_rn_013_limite_por_centro_custo` |
| RN-014 | T-024 | `test_rn_014_representacao_aprovada_para_cc_que_lista` |
| RN-015 | T-023 | `test_rn_015_conversao_moeda_antes_de_demais_regras`, `test_amb_015_moeda_sem_cotacao_fica_nao_processado` |
| RN-016 | T-025 | `test_rn_016_hospedagem_zerada_por_politica_do_cc` |
| RN-017 | T-027 | `test_rn_017_fila_aprovacao_manual_acima_de_500` |
| AMB-013..023 | ver RN correspondente na seção 5/6 da spec | ver T-021 a T-028 acima |
| Ordem de aplicação (seção 8) | T-014 | `test_ordem_regras_estrutural_nao_consome_limite_diario` |
| Caso de borda fim de semana (seção 7) | T-015 | `test_borda_fim_de_semana_sem_regra_especial` |
| Invariante de soma (seção 9) | T-016 | `test_invariante_soma_totais_exemplo_oficial` |
| Formato de saída (seção 4) | T-017 | `test_formato_saida` |
| CLI ponta a ponta | T-018 | `test_cli_processa_exemplo_oficial` |
| Entrada inválida não gera saída (seção 9) | T-019 | `test_cli_entrada_invalida_nao_gera_saida` |
| CLI ponta a ponta — envelope v4 | T-030 | `test_cli_processa_envelope_v4_cc_comercial`, `test_cli_processa_envelope_v4_cc_desconhecido` |
