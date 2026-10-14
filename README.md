# Motor de Cálculo de Reembolso de Despesas

CLI que recebe o conjunto de despesas de um colaborador em um período e
devolve, para cada despesa, o valor reembolsável e a justificativa da
decisão — aplicando a política de reembolso já desambiguada em
[`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md).

> Este é o projeto entregue para o [Desafio Prático de Spec Driven
> Development](DESAFIO.md). O enunciado original do desafio, a rubrica e os
> materiais de apoio continuam disponíveis neste repositório para referência;
> este README documenta **o projeto construído**, não o desafio em si.

## Requisitos

- Python 3.11 ou superior
- `pytest` (único pacote externo, usado apenas para os testes)

## Instalação

```bash
pip install -r requirements.txt
```

Não há instalação do pacote em si — a CLI é executada diretamente do
código-fonte em `src/`.

## Como rodar

```bash
PYTHONPATH=src python -m motor_reembolso.cli calcular \
  --input exemplos/despesas-exemplo.json \
  --output resultado.json
```

No PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m motor_reembolso.cli calcular --input exemplos\despesas-exemplo.json --output resultado.json
```

O arquivo `resultado.json` é gravado com a estrutura descrita na seção 4 de
[`spec.md`](specs/001-motor-reembolso/spec.md): colaborador, período, lista de
despesas com `valor_reembolsado`/`status`/`motivos`/`justificativa` por item,
e um `resumo` com os totais agregados.

Entrada com JSON malformado ou campo obrigatório ausente retorna código de
saída diferente de zero, imprime o erro em `stderr` e **não** gera o arquivo
de saída (nem parcialmente).

## Como testar

```bash
pytest
```

A configuração do `pytest` (`pyproject.toml`) já aponta `pythonpath = ["src"]`,
então os testes rodam sem precisar exportar `PYTHONPATH` manualmente.

Estrutura dos testes, um arquivo por módulo:

- `tests/test_modelos.py` — estruturas de dados internas
- `tests/test_politica.py` — constantes da política de reembolso
- `tests/test_io_despesas.py` — leitura/validação do JSON de entrada
- `tests/test_motor.py` — cada regra de negócio (`RN-001` a `RN-012`) isolada,
  mais o pipeline completo (`calcular`) e casos de borda
- `tests/test_relatorio.py` — montagem e serialização da saída, invariante de
  soma dos totais
- `tests/test_cli.py` — ponta a ponta via subprocesso contra
  `exemplos/despesas-exemplo.json`

## Agentes customizados e skill (aXet.code)

Além da CLI, o projeto tem dois agentes customizados em `.axet-code/agents/`
e uma skill que os orquestra, pensados para quem for revisar/rodar o motor
usando o aXet.code em vez do terminal puro:

- **`calculo-reembolso`** — executa a CLI sobre um JSON de despesas e devolve
  o resultado já resumido em linguagem natural (quantas despesas foram
  aprovadas/recusadas, totais, motivo de cada recusa). Não edita nenhum
  arquivo.
- **`auditor-ambiguidades`** — roda a suíte `pytest`, confere se a tabela de
  cobertura de `tasks.md` tem teste real para cada `RN-00X`, e cruza as 16
  ambiguidades da seção 6 de `spec.md` contra a implementação. Quando recebe
  um resultado de cálculo específico, também confirma se a justificativa de
  cada despesa recusada é coerente com a regra citada. Devolve um veredito
  `APROVADO` ou `ATENCAO` com a lista de achados. Também não edita nada —
  é um papel de auditoria/relato.

**Como usar:** dentro de uma sessão do aXet.code, digite:

```
%calcular-reembolso exemplos/despesas-exemplo.json
```

A skill pergunta o arquivo de entrada (se não informado), aciona o
`calculo-reembolso`, repassa o resultado para o `auditor-ambiguidades`, e
apresenta os dois resultados juntos — priorizando o veredito de auditoria
caso ele aponte algo em `ATENCAO`.

> Agentes e skills são lidos no início da sessão: se você acabou de clonar o
> repositório, abra uma nova sessão do aXet.code antes de usar `%calcular-reembolso`.

## Estrutura do projeto

```
src/motor_reembolso/
├── modelos.py      # Despesa, ResultadoDespesa, Resumo, ResultadoCalculo
├── politica.py      # limites, gatilho de nota fiscal, mapeamento de categorias
├── io_despesas.py   # leitura e validação do JSON de entrada
├── motor.py          # regras de negócio puras (RN-001 a RN-012), sem I/O
├── relatorio.py      # monta e serializa a saída
└── cli.py            # ponto de entrada: calcular --input --output
tests/                # um arquivo de teste por módulo acima
specs/001-motor-reembolso/
├── spec.md           # o quê e o porquê — regras de negócio e ambiguidades resolvidas
├── plan.md           # o como — stack, arquitetura, decisões técnicas
├── tasks.md          # T-001..T-0NN, rastreando spec → código → teste
└── DECISIONS.md       # log de mudanças de spec
.axet-code/
├── agents/            # calculo-reembolso.md, auditor-ambiguidades.md
└── skills/            # calcular-reembolso/SKILL.md (%calcular-reembolso)
docs/
├── sessions/          # exports das sessões de trabalho com o agente
└── RELATORIO.md       # relatório final do desafio
```

## Política de reembolso implementada

A política original do RH tinha ambiguidades reais, todas identificadas e
resolvidas em [`spec.md`](specs/001-motor-reembolso/spec.md) seção 6. Resumo
rápido das regras implementadas (`RN-001` a `RN-012`):

| Regra | O quê |
|---|---|
| RN-001/002 | Limite diário de alimentação (R$60) e transporte urbano (R$80), somado por categoria/dia |
| RN-003 | Limite de R$250/diária de hospedagem, com nº de diárias extraído da descrição |
| RN-004 | Excedente é cortado sequencialmente por ordem de lançamento, não proporcionalmente |
| RN-005 | Nota fiscal obrigatória para valor estritamente > R$100 |
| RN-006 | Limites de alimentação/transporte ampliados em 50% em dias com hospedagem lançada ("viagem") |
| RN-007 | Despesa fora do período de competência é recusada |
| RN-008 | Duplicatas (mesma data+categoria+valor+fornecedor) são recusadas, exceto a primeira |
| RN-009 | Categorias fora da política são recusadas; `coworking` é mapeada para `hospedagem` |
| RN-010 | Valores negativos (estornos) são ignorados no cálculo |
| RN-011 | Arredondamento `half-even` a 2 casas decimais em todo cálculo monetário |
| RN-012 | Comparação de categoria é case-insensitive |

## Fora de escopo

Ver seção 3 de [`spec.md`](specs/001-motor-reembolso/spec.md): sem
autenticação, sem persistência entre execuções, sem integração com sistemas
reais de nota fiscal/folha de pagamento, sem interface além da CLI.
