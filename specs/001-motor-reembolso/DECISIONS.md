# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

---

## 2026-10-15 — Correção editorial: "Aceite" de RN-015 trocava os dados de e-004/e-005

**O que mudou:** o texto de "Aceite" de RN-015 e a linha correspondente da
tabela de casos de borda (seção 7) foram corrigidos. Nenhuma regra de
negócio foi alterada; o código já implementava o comportamento correto.

**Por que mudou:** uma auditoria da implementação do envelope v4 (igual à
já feita para a v3) encontrou que o texto atribuía a `e-004` os valores
`USD 40,00, 2026-07-20, sábado, sem cotação publicada`. Os dados reais em
`exemplos/envelope/despesas-envelope.json` são: `e-004` é `EUR 30,00` em
`2026-07-18` (sábado real, sem cotação — o fallback de AMB-016 realmente
se aplica aqui); `USD 40,00`/`2026-07-20` pertence a `e-005`
(transporte_urbano), cuja data é segunda-feira e **tem** cotação
publicada em `cambio.json` — não é um caso de fallback. Os dados de
`e-004` e `e-005` foram trocados por engano ao redigir o "Aceite".

**Decisão:** corrigido o texto para `e-004, EUR 30,00, data 2026-07-18
(sábado, sem cotação publicada) → usa a taxa de EUR do último dia útil
anterior (2026-07-17)`. Ajustada também a docstring de
`tests/test_cambio.py::test_amb_016_data_sem_cotacao_usa_ultimo_dia_util_anterior`,
que replicava o mesmo engano (o teste em si já usava a lógica correta,
só a referência de rastreabilidade estava errada).

**Evidência:** auditoria desta sessão sobre a implementação do envelope
v4; mesmo padrão de erro editorial já corrigido em 2026-10-15 para
RN-003/RN-009 (ver entrada abaixo).

---

## 2026-10-15 — Absorção do envelope do Dia 2: Política de Reembolso v4

**O que mudou:** `spec.md` passou de v1.0 para v2.0. Mudança de requisito
recebida via envelope do Dia 2 (comunicado do RH, "Política de Reembolso
v4"), com três eixos:

- **A — Limites por centro de custo.** Os limites de `alimentacao`,
  `transporte_urbano` e `hospedagem`, o gatilho de nota fiscal e o
  percentual de ampliação em viagem deixam de ser constantes fixas e
  passam a ser lidos de uma tabela externa (`politica-v4.json`),
  resolvida por `centro_custo` com fallback para uma política padrão.
  Categoria nova `representacao` (R$300,00/dia), reembolsável só para os
  CCs que a listam explicitamente (hoje, só `CC-COMERCIAL`).
  `CC-ENG-PLATAFORMA` zera hospedagem (`limite: 0.00`, não reembolsável).
- **B — Despesas internacionais.** Campo novo `despesas[].moeda` (ISO
  4217, opcional, default `BRL`). Conversão para BRL pela taxa da data
  da despesa, lida de `cambio.json`, antes de qualquer regra que compare
  valores.
- **C — Fila de aprovação manual (opcional, incluída nesta rodada por
  decisão do humano).** Despesas com `valor_reembolsado` > R$500,00 têm o
  status substituído por `pendente` em vez de aprovação automática.

**Requisitos invalidados pela v1.0:**
- RN-001/002/003/005/006 deixam de citar valores fixos no texto
  normativo — passam a referenciar "o limite vigente para o centro de
  custo" (RN-013).
- RN-009 ("apenas três categorias são reembolsáveis") deixa de ser
  verdade de forma incondicional — `representacao` é a quarta, condicional
  ao centro de custo (RN-014).
- Seção 4 (entrada): `despesas[].valor` deixa de ser sempre "em reais";
  passa a depender do campo novo `moeda`.
- Seção 4 (saída): `status` ganha dois valores novos (`pendente`,
  `nao_processado`); `resumo` ganha `quantidade_pendentes`; a definição
  de `quantidade_aprovadas` é redefinida por inclusão explícita em vez de
  exclusão (ver AMB-023 — aproveitamos para corrigir a fragilidade já
  apontada em `docs/auditoria-resultado-2026-07.md`).
- `plan.md` seção 4 ("Decisão deliberada: constantes em código, não
  arquivo de configuração externo") fica formalmente superada — o próprio
  risco que o `plan.md` antecipava ("se a política mudar com frequência...
  esse é o primeiro ponto a extrair para configuração") se concretizou.
- `plan.md` DT-002 (assinatura `calcular(despesas, periodo)`) precisa
  passar a receber também o centro de custo do colaborador, hoje só
  repassado para a saída sem influenciar o cálculo.

**Ambiguidades novas identificadas e decididas** (processo idêntico ao da
v3: uma pergunta por vez, com opções e justificativa, decisão do humano):
AMB-013 a AMB-023 — ver `spec.md` seção 6 para o texto completo de cada
uma. Resumo:

| ID | Resumo da decisão |
|---|---|
| AMB-013 | Categoria ausente num CC parcial → herda limite padrão só para aquela categoria |
| AMB-014 | CC ausente da tabela → usa só o bloco padrão integral; `representacao` não existe para ele |
| AMB-015 | Moeda sem cotação em nenhuma data → `status: nao_processado`, não interrompe as demais despesas |
| AMB-016 | Data sem cotação (dia não útil) → usa a taxa do último dia útil anterior |
| AMB-017 | Conversão de moeda ocorre antes de nota fiscal, diária e arredondamento |
| AMB-018 | Ampliação de viagem não se estende a `representacao` |
| AMB-019 | Hospedagem zerada por política de CC usa motivo próprio (RN-016), distinto de AMB-010b |
| AMB-020 | Limiar de aprovação manual (R$500) é estritamente maior, mesma convenção de AMB-003 |
| AMB-021 | `pendente` substitui `aprovado`/`aprovado_parcial`; nunca se aplica a despesa recusada |
| AMB-022 | Novo campo `resumo.quantidade_pendentes`, fora de `quantidade_aprovadas` |
| AMB-023 | `quantidade_aprovadas` redefinida como conjunto explícito `{aprovado, aprovado_parcial}` |

**Regras novas criadas:** RN-013 (limites por centro de custo), RN-014
(categoria `representacao`), RN-015 (conversão de moeda), RN-016
(hospedagem zerada por política de CC), RN-017 (fila de aprovação
manual). Regras alteradas: RN-006 (exclui `representacao` da ampliação de
viagem), RN-009 (inclui `representacao` condicional ao CC).

**Tasks que precisam ser refeitas/criadas:** ver `tasks.md`, Fase 5 — a
numeração continua de T-021 (T-001 a T-020 permanecem válidas e intocadas,
RN-001 a RN-012 não mudaram de comportamento, só de redação onde citavam
valor fixo).

**Arquivos do envelope commitados:** `exemplos/envelope/` —
`00-ENVELOPE-LACRADO.md`, `politica-v4.json`, `cambio.json`,
`despesas-envelope.json`, `despesas-envelope-cc-desconhecido.json`.

**Evidência:** `docs/envelope-impacto.html` (mapeamento de impacto
produzido antes de qualquer decisão de ambiguidade, conforme exigido pelo
próprio comunicado do RH — "primeiro a spec", "registre no
DECISIONS.md").

---

## 2026-10-15 — Correção editorial: "Aceite" de RN-003 e RN-009 contradizia AMB-010b/RN-005

**O que mudou:** o texto de "Aceite" de RN-003 (d-013) e RN-009 (d-005) em
`spec.md`, e a linha correspondente da tabela de casos de borda (seção 7),
foram corrigidos. Nenhuma regra de negócio nova foi criada; o motor de
cálculo não foi alterado.

**Por que mudou:** uma auditoria despesa-a-despesa do resultado real contra
a spec (ver `docs/auditoria-resultado-2026-07.md`) encontrou duas frases de
"Aceite" que contradiziam decisões de ambiguidade já registradas na própria
spec:
- RN-009 afirmava reembolso integral de R$89,00 para d-005 assumindo
  "1 diária implícita", o que contradiz textualmente a decisão de AMB-010b
  (recusar quando o número de diárias não é extraível da descrição, para
  não mascarar uma violação real do limite). A descrição real de d-005
  ("Diaria em espaco compartilhado") não contém nenhum número.
- RN-003 e a tabela da seção 7 afirmavam reembolso integral de R$690,00 para
  d-013, ignorando que `tem_nota_fiscal: false` e valor > R$100,00 — a
  ordem de regras da seção 8 (nota fiscal antes de agregação por diária)
  e RN-005/AMB-004 exigem recusa integral antes mesmo de calcular diárias.

**Decisão:** a spec estava errada nesses dois trechos de exemplo, não o
código — o comportamento implementado já seguia a decisão de ambiguidade
correta (AMB-010b) e a ordem de regras explícita (seção 8). Corrigido o
texto da spec para eliminar a contradição interna, sem mudar nenhuma regra
de negócio nem o resultado do motor.

**Evidência:** `docs/auditoria-resultado-2026-07.md`, achados 1 e 2.

---

*Nenhuma mudança de spec registrada até agora.* A spec v1.0 foi escrita e
aprovada diretamente com as 16 ambiguidades já identificadas e decididas
durante a sessão de autoria (ver `spec.md` seção 6) — não houve, portanto,
uma versão anterior divergente para registrar como mudança.

A próxima entrada esperada aqui é a absorção da mudança de requisito do
Dia 2 (o "envelope"), quando chegar.
