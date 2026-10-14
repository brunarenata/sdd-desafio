# CLAUDE.md

## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit referencia uma task: `feat(T-003): <descrição>`.
  Mudanças de documentação: `docs(spec):`, `docs(plan):`, `docs(tasks):`.
- Nenhuma regra de negócio entra sem teste.

## Stack e comandos

- Linguagem: Python 3.11+ (stdlib: `decimal`, `datetime`, `argparse`, `json`)
- Rodar: `python -m motor_reembolso.cli calcular --input <entrada.json> --output <saida.json>`
  (com `PYTHONPATH=src`, ou instalando o pacote em modo editável)
- Testes: `pytest` (configurado via `pyproject.toml`, já aponta `pythonpath = ["src"]`)
- Lint/format: não configurado neste projeto (fora de escopo do desafio de 2 dias)

## Convenções de código

- Pacote em `src/motor_reembolso/`: `modelos.py` (estruturas de dados),
  `politica.py` (constantes da política), `io_despesas.py` (leitura/validação
  de entrada), `motor.py` (regras de negócio puras, sem I/O), `relatorio.py`
  (montagem/serialização de saída), `cli.py` (ponto de entrada).
- `motor.py` nunca importa `json`, `argparse` ou faz leitura de arquivo —
  é função pura testável isoladamente.
- Nomes de teste seguem `test_rn_00X_<resumo>` ou `test_amb_00X_<resumo>`,
  referenciando o ID da regra/ambiguidade da spec (rastreabilidade).
- Valores monetários: sempre `decimal.Decimal`, nunca `float`, exceto na
  borda de serialização JSON de saída (onde `float` é inevitável porque
  `json` nativo não serializa `Decimal`). Arredondamento: `ROUND_HALF_EVEN`
  a 2 casas decimais (ver RN-011 em `spec.md`).

## Fora de escopo

- Interface web/API HTTP — apenas CLI.
- Autenticação, persistência entre execuções, integração com folha de
  pagamento ou sistema real de notas fiscais.
- Qualquer regra de negócio não registrada em `specs/001-motor-reembolso/spec.md`.
