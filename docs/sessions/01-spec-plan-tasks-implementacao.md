# Sessão 01 — Spec, Plan, Tasks e Implementação Completa

**Data:** 2026-07 (ver timestamps dos commits para precisão)
**Ferramenta:** aXet.code (não há `/export` nativo nesta ferramenta; este
arquivo é um resumo estruturado reconstruído manualmente a partir do
histórico real da sessão, conforme orientação do `FAQ.md` do desafio para
quando o export automático não está disponível).

> Nomes de diretório pessoais do usuário foram omitidos/generalizados onde
> apareciam nos logs de comando.

---

## 1. Objetivo da sessão

Conduzir o desafio de SDD do zero: ler `DESAFIO.md`/`RUBRICA.md`/`FAQ.md`,
identificar e decidir as ambiguidades da política de reembolso, escrever
`spec.md` → `plan.md` → `tasks.md`, implementar o motor com testes, e deixar
o produto rodando via CLI.

## 2. Leitura inicial e setup

- Lido `README.md`, `DESAFIO.md`, `RUBRICA.md`, `FAQ.md`, todo o `template/`
  (`CLAUDE.md`, `docs/RELATORIO.md`, `specs/001-motor-reembolso/{spec,plan,tasks,DECISIONS}.md`)
  e `exemplos/despesas-exemplo.json`.
- Setup inicial do fork: copiado `template/CLAUDE.md`, `template/specs/`,
  `template/docs/` para a raiz, criado `src/`, `tests/`, `docs/sessions/`.
  Commit: `chore: estrutura inicial a partir do template` (`e43606c`).
- Stack escolhida com o usuário via pergunta estruturada: **Python**.

## 3. Decisão das ambiguidades (16 no total, acima do mínimo de 8 exigido)

Conduzidas uma a uma com o usuário via perguntas de múltipla escolha,
cruzando a política do RH item a item contra `exemplos/despesas-exemplo.json`:

| ID | Ambiguidade | Decisão |
|---|---|---|
| AMB-001 | Limite de alimentação por despesa ou por dia | Soma por dia |
| AMB-002 | "Reembolsado parcialmente" = corte ou recusa total | Corta no limite |
| AMB-003 | R$100,00 exatos exige nota fiscal? | Fronteira exclusiva (`>`) |
| AMB-004 | Falta de nota obrigatória: recusa total ou glosa parcial | Recusa total |
| AMB-005/005b/005c | Definição de "em viagem" sem campo explícito | Inferida pela data de hospedagem lançada; só o dia do lançamento; não amplia o próprio limite de hospedagem |
| AMB-006 | Despesa fora do período de competência | Recusa total |
| AMB-007 | Critério e ação de duplicata | Mesma data+categoria+valor+fornecedor; mantém a de menor id |
| AMB-008/008b | Categoria fora da lista oficial (`coworking`) | Mapeada por analogia para `hospedagem` — **ponto de maior discussão da sessão**, ver seção 5 |
| AMB-009 | Valor negativo (estorno) | Ignorado, não entra em nenhuma soma |
| AMB-010/010b | Nº de diárias de hospedagem sem campo estruturado | Extraído da descrição por regex; fallback = recusa |
| AMB-011 | Precisão/arredondamento monetário | `ROUND_HALF_EVEN`, 2 casas |
| AMB-012 | Categoria em caixa diferente | Case-insensitive |
| Ordem de aplicação | Qual regra "ganha" quando duas incidem | Filtra estruturalmente primeiro, agrega limite diário depois |
| Distribuição de corte no limite diário | Proporcional ou sequencial por ordem de lançamento | Sequencial por ordem de lançamento |

## 4. Escrita de spec.md / plan.md / tasks.md

- `spec.md`: 12 regras de negócio (RN-001 a RN-012), 16 ambiguidades
  documentadas com texto original do RH, decisão e justificativa, casos de
  borda, ordem de aplicação, critérios de aceite.
  Commit: `docs(spec): define regras de negocio e resolve ambiguidades da
  politica de reembolso` (`18415e5`).
- `plan.md`: stack Python 3.11+/`Decimal`/`pytest`/`argparse`, arquitetura em
  módulos (`io_despesas`, `modelos`, `politica`, `motor`, `relatorio`, `cli`),
  3 decisões técnicas justificadas (DT-001 a DT-003).
  Commit: `docs(plan): define stack Python, arquitetura e decisoes tecnicas`
  (`7c72dc7`).
- `tasks.md`: T-001 a T-020 em 4 fases, com matriz de cobertura RN→task→teste.
  Commit: `docs(tasks): define T-001 a T-020 rastreando regras de negocio da
  spec` (`a259fdb`).

## 5. Discernimento: ponto de maior deliberação (AMB-008)

O agente propôs inicialmente comparar categoria por **match literal estrito**
(`coworking` seria recusado por não estar na lista oficial). O usuário
questionou se isso fazia sentido comparando com um caso diferente (transporte
urbano identificado literalmente). Essa pergunta expôs que "match literal"
escondia uma decisão de negócio não examinada. Resultado final: mapear por
analogia de natureza do gasto, com `coworking → hospedagem` registrado
explicitamente — e qualquer categoria nova futura exigiria decisão
equivalente (documentado em `spec.md` seção 10, "O que fica em aberto").

## 6. Implementação (T-001 a T-020)

Implementado módulo a módulo, um commit por task, com testes a cada passo:

- T-001 a T-004: estrutura do projeto, `modelos.py`, `politica.py`,
  `io_despesas.py`.
- T-005 a T-013: cada regra de negócio isolada em `motor.py`
  (`_regra_valor_negativo`, `_regra_categoria`, `_regra_periodo`,
  `_regra_duplicata`, `_regra_nota_fiscal`, `_regra_hospedagem`,
  `_calcular_dias_viagem`, `_limite_diario`, `_aplicar_limites_diarios`,
  `_quantizar`).
- T-014: orquestração do pipeline completo (`motor.py::calcular`), seguindo
  a ordem fixa da seção 8 da spec.
- T-015/T-016: caso de borda de fim de semana, invariante de soma de totais.
- T-017: `relatorio.py` (montagem e serialização da saída).
- T-018/T-019: `cli.py` (`calcular --input --output`), tratamento de entrada
  inválida sem gerar saída parcial.
- T-020: `README.md`/`CLAUDE.md` preenchidos com comandos reais, verificados
  manualmente rodando o comando documentado.

Resultado: **46 testes automatizados passando**, CLI validada ponta a ponta
contra `exemplos/despesas-exemplo.json` (8 aprovadas, 6 recusadas, totais
consistentes).

## 7. Incidente real detectado e corrigido (ver Discernimento no RELATORIO.md)

Após uma interrupção de sessão (chamadas de ferramenta encerradas sem
confirmação), o agente **reescreveu do zero** `spec.md`/`plan.md`/`tasks.md`
com estrutura de regras incompatível com a implementação já existente e
testada (commits `3258d3c`, `7795273`, `2452759`), sem perceber que já havia
uma versão aprovada com código correspondente.

**Detecção:** uma checagem de rotina (`git log`/`git status`) antes de
continuar a implementação revelou "ahead of origin by 20 commits" — número
incompatível com o esperado. Investigação com `git show` nos dois commits de
spec confirmou duplicação com numeração de regra divergente.

**Correção:** `git reset --hard fbad5f1`, descartando os três commits
duplicados e retomando a partir da última versão consistente com código e
testes construídos sobre ela. Suíte de 37 testes confirmada passando antes
de continuar a implementação (T-014 em diante).

## 8. Correção de remote git

O remote `origin` apontava para o repositório do instrutor
(`Sassine/sdd-desafio`), não para o fork do usuário. Corrigido com
`git remote set-url origin git@github.com:brunarenata/sdd-desafio.git` e
`git push origin main` (`bc3d841..4850f6a`).

## 9. Estado final desta sessão

- `spec.md`, `plan.md`, `tasks.md`, `DECISIONS.md` completos e consistentes
  com o código.
- 20 tasks implementadas e marcadas `[x]` com hash de commit.
- 46 testes passando.
- CLI funcional, validada manualmente pelo usuário.
- `README.md`/`CLAUDE.md` do projeto preenchidos.
- `docs/RELATORIO.md` rascunhado com evidências objetivas (hashes, caso de
  discernimento real), campos de reflexão pessoal deixados como
  `<preencher>` para o usuário.
- Pendente: envelope do Dia 2 (ainda não recebido) e exports de sessão
  (este arquivo é o primeiro).
