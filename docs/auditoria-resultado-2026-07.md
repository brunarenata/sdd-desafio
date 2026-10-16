# Auditoria despesa a despesa — `exemplos/despesas-exemplo.json` → `_resultado_20261014.json`

> Objetivo: percorrer cada uma das 14 despesas do exemplo oficial, confirmar
> contra `spec.md` (regras RN-00X e ambiguidades AMB-00X) e contra a
> aritmética real do arquivo de resultado, para que o valor final seja
> auditável e confiável — não apenas "o programa rodou sem erro".
>
> Entrada: `exemplos/despesas-exemplo.json` · Saída auditada:
> `_resultado_20261014.json` · Spec: `specs/001-motor-reembolso/spec.md`.
> Suite de testes rodada antes desta auditoria: `pytest -q` → **46/46
> passando**.

## Tabela-resumo

| id | categoria_aplicada | valor_declarado | valor_reembolsado | status | regras aplicadas | veredito |
|---|---|---|---|---|---|---|
| d-001 | alimentacao | 72,50 | 60,00 | aprovado_parcial | RN-001, RN-004 | confere |
| d-002 | alimentacao | 38,00 | 0,00 | recusado | RN-001, RN-004 | confere |
| d-003 | transporte_urbano | 100,00 | 80,00 | aprovado_parcial | RN-002, RN-004, AMB-003 | confere |
| d-004 | transporte_urbano | 100,01 | 0,00 | recusado | RN-005 | confere |
| d-005 | hospedagem | 89,00 | 0,00 | recusado | RN-003, AMB-010b (via AMB-008) | confere com ressalva — spec corrigida (ver abaixo) |
| d-006 | alimentacao | 54,90 | 54,90 | aprovado | RN-001, RN-004 | confere |
| d-007 | alimentacao | 54,90 | 0,00 | recusado | RN-008 | confere |
| d-008 | alimentacao | 41,00 | 0,00 | recusado | RN-007 | confere |
| d-009 | — (ignorado) | -45,00 | 0,00 | ignorado | RN-010, AMB-009 | confere |
| d-010 | hospedagem | 480,00 | 480,00 | aprovado | RN-003, AMB-010 | confere |
| d-011 | alimentacao | 33,33 | 33,33 | aprovado | RN-001, RN-004, RN-011/AMB-011 | confere |
| d-012 | alimentacao | 47,20 | 47,20 | aprovado | RN-001, RN-004 | confere |
| d-013 | hospedagem | 690,00 | 0,00 | recusado | RN-005 | confere com ressalva — spec corrigida (ver abaixo) |
| d-014 | alimentacao | 61,00 | 60,00 | aprovado_parcial | RN-001, RN-004, RN-012/AMB-012 | confere |

Todas as 14 despesas conferem com o comportamento normativo da spec. Duas
delas (d-005, d-013) expuseram frases de exemplo ("Aceite") que
contradiziam a própria spec — corrigidas em `spec.md` e registradas em
`DECISIONS.md` (ver seção final).

## d-001 — alimentação, R$72,50, 2026-07-03

Entrada: Restaurante Tavola, nota=true, "Almoco com cliente".
d-001 e d-002 são o mesmo dia/categoria: soma = 72,50 + 38,00 = 110,50 >
limite diário de R$60,00 (RN-001). Por RN-004 (corte sequencial por ordem
de lançamento), o primeiro item absorve o limite integral: reembolso =
min(72,50; 60,00) = **60,00**, `aprovado_parcial`. Bate com o exemplo da
seção 4 da spec.

## d-002 — alimentação, R$38,00, 2026-07-03

Mesmo dia/categoria de d-001. Limite diário já esgotado (60,00 − 60,00 =
0,00) → reembolso **0,00**, `recusado`. Bate com RN-001/RN-004.

## d-003 — transporte urbano, R$100,00, 2026-07-06

TaxiApp, nota=false, "Corrida aeroporto". R$100,00 exato **não** exige nota
fiscal (AMB-003: fronteira exclusiva, só exige acima de R$100,00) → passa
para RN-002 (limite diário R$80,00). d-004 (mesmo dia) é recusada por
RN-005 *antes* de competir pelo limite diário (seção 8), então d-003 é a
única despesa válida de transporte do dia → reembolso = min(100,00; 80,00)
= **80,00**, `aprovado_parcial`.

## d-004 — transporte urbano, R$100,01, 2026-07-06

Um centavo acima do limite de nota fiscal, sem nota → RN-005 recusa
integralmente, independentemente de limite diário → **0,00**, `recusado`.

## d-005 — coworking→hospedagem, R$89,00, 2026-07-07

HubOffice, nota=true, descrição "Diaria em espaco compartilhado". AMB-008
mapeia `coworking` → `hospedagem` (`categoria_aplicada: hospedagem`). RN-003
exige extrair o número de diárias da descrição por reconhecimento de texto;
a descrição não contém nenhum dígito seguido de "diária(s)"/"noite(s)" —
**nenhum número identificável** → fallback de recusa integral (AMB-010b) →
**0,00**, `recusado`.

**Achado corrigido na spec:** o "Aceite" original de RN-009 assumia "1
diária implícita" e previa reembolso integral de R$89,00 para este mesmo
item — texto que contradizia diretamente a justificativa de AMB-010b
("recusar no fallback evita assumir '1 diária' por padrão... o que
mascararia uma violação real do limite"). O resultado auditado segue a
decisão de ambiguidade específica (AMB-010b), que é a mais recente e mais
específica para este cenário; o texto da spec foi corrigido para refletir
isso (ver `DECISIONS.md`, entrada 2026-10-15).

## d-006 — alimentação, R$54,90, 2026-07-09

Bistro Central, nota=true, "Almoco". Primeira ocorrência do par duplicado
d-006/d-007 (menor id) → segue normalmente por RN-008. Única despesa de
alimentação do dia que entra na soma (d-007 é excluída estruturalmente) →
54,90 ≤ 60,00 → reembolso integral **54,90**, `aprovado`.

## d-007 — alimentação, R$54,90, 2026-07-09

Idêntica a d-006 em data+categoria+valor+fornecedor → duplicata (RN-008/
AMB-007), id maior → recusada integralmente, **0,00**, `recusado`, e não
disputa o limite diário com d-006.

## d-008 — alimentação, R$41,00, data 2026-04-15

Fora do período de competência (2026-07-01 a 2026-07-31) → RN-007 recusa
integralmente antes de qualquer agregação diária → **0,00**, `recusado`.

## d-009 — transporte urbano, R$-45,00, 2026-07-11

Estorno de corrida cancelada. Valor negativo → RN-010/AMB-009: `status:
ignorado`, `valor_reembolsado: 0,00`, não entra em nenhuma soma (nem diária
nem do resumo) — é o primeiro passo da ordem de regras (seção 8), antes
até da normalização de categoria (por isso `categoria_aplicada: null`).

## d-010 — hospedagem, R$480,00, 2026-07-14

Hotel Copa Sul, nota=true, "Hotel Rio - 2 diarias". Passa por RN-005 (tem
nota). RN-003 extrai "2" da descrição → 480,00 / 2 = **240,00/diária** ≤
250,00 → sem corte → reembolso integral **480,00**, `aprovado`.

## d-011 — alimentação, R$33,333, 2026-07-15

Hotel Copa Sul, nota=true, "Cafe da manha hotel". RN-011/AMB-011:
arredondamento half-even a 2 casas na ingestão → 33,333 → **33,33** (sem
empate em .005, arredonda normalmente para baixo). Único item de
alimentação do dia → reembolso integral **33,33**, `aprovado`.

## d-012 — alimentação, R$47,20, 2026-07-18 (sábado)

Padaria Uniao, "Almoco de sabado - plantao". Seção 10 confirma: sem regra
especial de fim de semana. Único item do dia, 47,20 ≤ 60,00 → reembolso
integral **47,20**, `aprovado`.

## d-013 — hospedagem, R$690,00, 2026-07-22

Airbnb, **nota=false**, "Airbnb 3 noites". Valor > R$100,00 sem nota fiscal
→ RN-005 recusa integralmente **no passo 5** da ordem de regras (seção 8),
*antes* de chegar ao passo 6 (RN-003, agregação por diária) → **0,00**,
`recusado`. Se tivesse nota fiscal, o cálculo seria 690,00/3 = 230,00/diária
≤ 250,00 (sem corte) — mas essa conta nunca é executada.

**Achado corrigido na spec:** o "Aceite" original de RN-003 e a tabela de
casos de borda (seção 7) previam reembolso integral de R$690,00 para
d-013, ignorando `tem_nota_fiscal: false`. A ordem explícita da seção 8
(nota fiscal antes de diária) e RN-005/AMB-004 ("recusa total...
independentemente de estar dentro do limite da categoria") prevalecem. O
resultado auditado está correto; o texto da spec foi corrigido (ver
`DECISIONS.md`, entrada 2026-10-15).

## d-014 — ALIMENTACAO (maiúsculas), R$61,00, 2026-07-31

Restaurante Tavola, "Jantar de encerramento". RN-012/AMB-012: comparação
case-insensitive → `categoria_aplicada: alimentacao`. Único item do dia,
61,00 > limite 60,00 → corte no teto → reembolso **60,00**,
`aprovado_parcial`.

## Aritmética do bloco `resumo`

Recalculada a partir dos 14 itens individuais do próprio resultado:

- `total_declarado` = soma de `valor_declarado` **exceto d-009** (RN-010):
  72,50+38,00+100,00+100,01+89,00+54,90+54,90+41,00+480,00+33,33+47,20+690,00+61,00
  = **1.861,84** ✓ (bate com o resumo)
- `total_reembolsado` = soma de `valor_reembolsado` de todos os 14 itens:
  60,00+0+80,00+0+0+54,90+0+0+0+480,00+33,33+47,20+0+60,00 = **815,43** ✓
- `total_recusado` = total_declarado − total_reembolsado = **1.046,41** ✓
  (satisfaz o critério de aceite da seção 9: reembolsado + recusado =
  declarado)
- `quantidade_despesas` = 14 ✓ (contagem bruta de itens de entrada)
- `quantidade_aprovadas` (status != "recusado") = d-001, d-003, d-006,
  d-009, d-010, d-011, d-012, d-014 = **8** ✓
  - *Nota de nomenclatura:* d-009 (`ignorado`, estorno) entra em
    `quantidade_aprovadas` porque a definição literal da seção 4 é
    "status != recusado", não "status == aprovado". O cálculo está correto
    pela definição da spec, mas o nome do campo pode induzir leitura
    equivocada — vale considerar renomear ou adicionar `quantidade_ignoradas`
    numa futura revisão de contrato de saída (não é bug, é um risco de
    leitura).
- `quantidade_recusadas` = d-002, d-004, d-005, d-007, d-008, d-013 = **6** ✓
- d-009 confirmado fora de todas as somas (RN-010/AMB-009) ✓

## Conclusão

Todas as 14 despesas e o bloco `resumo` conferem com o comportamento
normativo e aritmético esperado. A auditoria encontrou **duas contradições
internas na própria spec** (frases de "Aceite" desatualizadas em RN-003 e
RN-009, que descreviam um resultado diferente do que a decisão de
ambiguidade dedicada — AMB-010b — e a ordem de regras da seção 8 realmente
produzem). O motor de cálculo **não** tinha bug: ele já seguia a leitura
correta e mais específica da spec. O texto da spec foi corrigido para
eliminar a contradição, e a mudança está registrada em
`specs/001-motor-reembolso/DECISIONS.md` (entrada 2026-10-15), conforme a
regra de trabalho do projeto (`CLAUDE.md`: "se a spec estiver errada,
corrigimos a spec primeiro e registramos em DECISIONS.md").
