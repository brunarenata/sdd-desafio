# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Status:** aprovada · **Última alteração:** 2026-10-15
(absorção da Política de Reembolso v4, envelope do Dia 2 — ver
`DECISIONS.md`)

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

Hoje o financeiro confere manualmente, item por item, cada despesa lançada por
cada colaborador contra a política de reembolso. É lento, inconsistente entre
analistas diferentes, e não deixa rastro de por que uma despesa foi aprovada
ou recusada.

## 2. Objetivo

Dado um conjunto de despesas de um colaborador em um período, o sistema
decide o valor reembolsável de cada despesa e devolve, para cada uma, a
justificativa da decisão — sem intervenção humana.

## 3. Fora de escopo

- Não autentica usuários nem gerencia permissões.
- Não persiste dados entre execuções (cada chamada é independente, stateless).
- Não se integra a nenhum sistema de folha de pagamento, contábil ou de notas
  fiscais reais — `tem_nota_fiscal` é um booleano informado na entrada, não é
  verificado contra uma nota real.
- Não calcula imposto, não gera arquivo de pagamento, não envia notificação.
- Não determina se um colaborador está "em viagem" por nenhuma fonte externa
  (agenda, sistema de passagens, etc.) — ver AMB-005.
- Não oferece interface web ou API HTTP — apenas CLI.
- Não corrige nem reescreve dados de entrada mal formados; entrada inválida
  (JSON malformado, campo obrigatório ausente, tipo errado) é um erro fatal
  da execução, não uma decisão de reembolso.

## 4. Entrada e saída

**Entrada:** conforme `exemplos/despesas-exemplo.json`. Campos e significado:

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | string | Identificador do colaborador | Sim |
| `colaborador.nome` | string | Nome do colaborador | Sim |
| `colaborador.centro_custo` | string | Centro de custo, informativo | Sim |
| `periodo.competencia` | string (`AAAA-MM`) | Mês de competência do lançamento | Sim |
| `periodo.inicio` | string (`AAAA-MM-DD`) | Início do período de competência | Sim |
| `periodo.fim` | string (`AAAA-MM-DD`) | Fim do período de competência | Sim |
| `despesas[].id` | string | Identificador único da despesa | Sim |
| `despesas[].data` | string (`AAAA-MM-DD`) | Data em que a despesa ocorreu | Sim |
| `despesas[].categoria` | string | Categoria declarada da despesa | Sim |
| `despesas[].descricao` | string | Texto livre descrevendo a despesa | Sim |
| `despesas[].fornecedor` | string | Nome do fornecedor/estabelecimento | Sim |
| `despesas[].valor` | número | Valor da despesa, na moeda do campo `moeda` | Sim |
| `despesas[].moeda` | string (ISO 4217) | Moeda em que `valor` está expresso. Ausente = `BRL` (ver RN-015) | Não |
| `despesas[].tem_nota_fiscal` | booleano | Se há nota fiscal anexada | Sim |

**Entrada adicional (política e câmbio, fora do JSON de despesas):**
conforme `exemplos/envelope/politica-v4.json` e
`exemplos/envelope/cambio.json`. Caminhos informados via argumento de linha
de comando (ver `plan.md`); se omitidos, o motor usa apenas a política
padrão embutida (equivalente à v3) e nenhuma despesa em moeda estrangeira é
convertida.

**Saída:** definida por mim. Estrutura e significado de cada campo:

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador` | objeto | Cópia do bloco `colaborador` da entrada |
| `periodo` | objeto | Cópia do bloco `periodo` da entrada |
| `despesas[].id` | string | Id da despesa de origem |
| `despesas[].categoria_original` | string | Categoria exatamente como veio na entrada |
| `despesas[].categoria_aplicada` | string | Categoria oficial usada para calcular o limite (após normalização/mapeamento, ver AMB-008) |
| `despesas[].valor_declarado` | número | Valor original da entrada, já convertido para BRL quando `moeda` != `BRL` (ver RN-015) |
| `despesas[].valor_reembolsado` | número | Valor efetivamente reembolsado, em BRL (0 se recusado) |
| `despesas[].status` | string | `"aprovado"`, `"aprovado_parcial"`, `"recusado"`, `"ignorado"`, `"pendente"` ou `"nao_processado"` (ver RN-010, RN-015, RN-017) |
| `despesas[].motivos` | lista de strings | Um ou mais códigos de regra (`RN-00X`) que determinaram o resultado |
| `despesas[].justificativa` | string | Frase legível explicando a decisão |
| `resumo.total_declarado` | número | Soma de `valor_declarado` (já em BRL) de todas as despesas processadas, excluindo estornos ignorados (AMB-009) e despesas `nao_processado` (AMB-015) |
| `resumo.total_reembolsado` | número | Soma de `valor_reembolsado` |
| `resumo.total_recusado` | número | `total_declarado - total_reembolsado` |
| `resumo.quantidade_despesas` | número | Total de despesas na entrada |
| `resumo.quantidade_aprovadas` | número | Despesas com `status` em `{"aprovado", "aprovado_parcial"}` (definição explícita, ver AMB-023) |
| `resumo.quantidade_recusadas` | número | Despesas com `status == "recusado"` |
| `resumo.quantidade_pendentes` | número | Despesas com `status == "pendente"` (ver RN-017, AMB-022) |

Exemplo de saída para duas despesas de alimentação no mesmo dia, somando
acima do limite diário (R$72,50 + R$38,00 = R$110,50, limite R$60):

```json
{
  "colaborador": { "id": "c-0417", "nome": "Marina Volpi", "centro_custo": "CC-ENG-PLATAFORMA" },
  "periodo": { "competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31" },
  "despesas": [
    {
      "id": "d-001",
      "categoria_original": "alimentacao",
      "categoria_aplicada": "alimentacao",
      "valor_declarado": 72.50,
      "valor_reembolsado": 60.00,
      "status": "aprovado_parcial",
      "motivos": ["RN-001"],
      "justificativa": "Soma de alimentação do dia 2026-07-03 (R$ 110,50) excede o limite diário de R$ 60,00; corte sequencial por ordem de lançamento — este item absorveu o limite integral."
    },
    {
      "id": "d-002",
      "categoria_original": "alimentacao",
      "categoria_aplicada": "alimentacao",
      "valor_declarado": 38.00,
      "valor_reembolsado": 0.00,
      "status": "recusado",
      "motivos": ["RN-001"],
      "justificativa": "Soma de alimentação do dia 2026-07-03 já atingiu o limite diário de R$ 60,00 com despesas anteriores; nada resta para este item."
    }
  ],
  "resumo": {
    "total_declarado": 110.50,
    "total_reembolsado": 60.00,
    "total_recusado": 50.50,
    "quantidade_despesas": 2,
    "quantidade_aprovadas": 1,
    "quantidade_recusadas": 1
  }
}
```

---

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks vão referenciar esses IDs.

### RN-001 — Limite diário de alimentação

**Regra:** o limite de R$ 60,00/dia para a categoria `alimentacao` incide
sobre a **soma de todas as despesas de alimentação do colaborador na mesma
data**, não sobre cada despesa isoladamente. O que exceder a soma é glosado
(ver RN-004 sobre como o corte é distribuído entre itens).
**Origem:** política do RH, item 1.
**Aceite:** d-001 (R$72,50) + d-002 (R$38,00), mesma data 2026-07-03 →
soma R$110,50 → reembolso total do dia limitado a R$60,00, distribuído por
ordem de lançamento (d-001 recebe R$60,00, d-002 recebe R$0,00).

### RN-002 — Limite diário de transporte urbano

**Regra:** o limite de R$ 80,00/dia para `transporte_urbano` incide sobre a
soma das despesas de transporte urbano do colaborador na mesma data, com a
mesma lógica de corte da RN-001.
**Origem:** política do RH, item 2.
**Aceite:** despesa isolada de transporte urbano de R$70,00 em um dia sem
outras despesas de transporte → reembolso integral de R$70,00.

### RN-003 — Limite por diária de hospedagem

**Regra:** o limite de R$ 250,00 incide **por diária**, aplicado sobre o
valor total do lançamento de hospedagem dividido pelo número de diárias/
noites identificado (ver AMB-010). O número de diárias é extraído da
`descricao` da despesa por reconhecimento de texto (`N diária(s)`,
`N noite(s)`); se não for possível identificar esse número, a despesa é
recusada integralmente (ver AMB-010b).
**Origem:** política do RH, item 3.
**Aceite:** d-010 "Hotel Rio - 2 diárias", valor R$480,00, `tem_nota_fiscal:
true` → passa por RN-005 → R$240,00/diária → dentro do limite de
R$250,00/diária → reembolso integral de R$480,00.
d-013 "Airbnb 3 noites", valor R$690,00, mas `tem_nota_fiscal: false` →
recusada integralmente ainda no passo de RN-005 (valor > R$100,00 sem nota),
antes de chegar à agregação por diária desta regra (ver ordem da seção 8);
se tivesse nota fiscal, o cálculo seria R$230,00/diária, dentro do limite.

### RN-004 — Distribuição do corte quando a soma do dia excede o limite

**Regra:** quando a soma diária de uma categoria sujeita a limite por dia
(alimentação, transporte urbano) excede o limite, as despesas daquele
dia/categoria são processadas na ordem em que aparecem no array `despesas`
da entrada (ordem de lançamento). Cada despesa recebe reembolso integral até
o limite diário se esgotar; a partir daí, as despesas seguintes do mesmo
dia/categoria são recusadas integralmente (reembolso R$0,00), não apenas
reduzidas proporcionalmente.
**Origem:** decisão de desambiguação da RN-001/RN-002 (AMB-001, AMB-002).
**Aceite:** ver exemplo da seção 4 (d-001 absorve o limite, d-002 fica a
zero).

### RN-005 — Nota fiscal obrigatória acima de R$100

**Regra:** despesas com `valor_declarado` **estritamente maior** que
R$100,00 exigem `tem_nota_fiscal = true`. Despesas de valor igual a R$100,00
não exigem nota fiscal. Despesa que exige nota e não tem (`tem_nota_fiscal =
false`) é recusada integralmente (reembolso R$0,00), independentemente de
estar dentro do limite da categoria.
**Origem:** política do RH, item 5.
**Aceite:** d-003 (R$100,00, sem nota) → não exige nota → segue para as
demais regras. d-004 (R$100,01, sem nota) → exige nota e não tem →
recusada, reembolso R$0,00.

### RN-006 — Ampliação de limites em viagem

**Regra:** o colaborador é considerado "em viagem" **somente na mesma data**
em que há ao menos uma despesa de categoria `hospedagem` lançada (após
mapeamento da AMB-008) no conjunto de despesas processado. Nessa data
específica, os limites diários de `alimentacao` e `transporte_urbano`
(vigentes para o centro de custo do colaborador, ver RN-013) são ampliados
no percentual definido pela política (`acrescimo_em_viagem_percentual`,
50% na v4). O limite de hospedagem não é ampliado — já é, por definição, o
limite de uma despesa de viagem. A categoria `representacao` também não é
ampliada (ver AMB-018): a ampliação de viagem é especificamente desenhada
para compensar o custo extra de estar fora da base (alimentação,
deslocamento), não para despesas de relacionamento comercial, que têm
teto próprio e natureza distinta.
**Origem:** política do RH, item 6; AMB-005; AMB-018 (v4).
**Aceite:** se houvesse uma despesa de alimentação em 2026-07-14 (data de
d-010, hospedagem), o limite diário de alimentação naquela data seria
ampliado em 50% sobre o limite vigente para o centro de custo do
colaborador. Uma despesa de `representacao` na mesma data não recebe
ampliação, mesmo havendo hospedagem no dia.

### RN-007 — Período de competência

**Regra:** uma despesa cuja `data` esteja fora do intervalo
`[periodo.inicio, periodo.fim]` é recusada integralmente (reembolso
R$0,00), independentemente de categoria, valor ou nota fiscal.
**Origem:** política do RH, item 7.
**Aceite:** d-008, data 2026-04-15, fora do período 2026-07-01 a
2026-07-31 → recusada, reembolso R$0,00.

### RN-008 — Tratamento de duplicatas

**Regra:** duas ou mais despesas são consideradas duplicatas quando têm a
mesma `data`, `categoria` (normalizada, ver AMB-012), `valor` e
`fornecedor`. Entre despesas duplicadas, a de menor `id` (primeira na ordem
de lançamento) segue para as demais regras normalmente; as demais são
recusadas integralmente (reembolso R$0,00) com motivo específico de
duplicata.
**Origem:** política do RH, item 8.
**Aceite:** d-006 e d-007, ambas 2026-07-09/alimentacao/R$54,90/Bistro
Central → d-006 segue para as demais regras, d-007 é recusada por
duplicata.

### RN-009 — Categorias fora da política

**Regra:** as categorias reembolsáveis são `alimentacao`,
`transporte_urbano` e `hospedagem` (comparação case-insensitive, ver
AMB-012), sempre disponíveis para qualquer centro de custo, mais
`representacao`, reembolsável **somente** para os centros de custo cuja
entrada em `politica-v4.json` a lista explicitamente (ver RN-013, RN-014).
A categoria `coworking` é mapeada para `hospedagem` antes de aplicar o
limite (ver AMB-008). Qualquer outra categoria não mapeada, ou
`representacao` para um centro de custo que não a lista, é recusada
integralmente, com motivo "categoria fora da política".
**Origem:** política do RH, item 9; política v4, item A (RN-014).
**Aceite:** d-005, categoria `coworking`, valor R$89,00 → mapeada para
`hospedagem` → avaliada com limite de R$250,00/diária; a descrição ("Diaria
em espaco compartilhado") não traz um número de diárias extraível → recusada
integralmente por RN-003/AMB-010b (fallback de dado insuficiente), não
reembolso integral. Reembolso só ocorreria se a descrição citasse o número
de diárias explicitamente (ex.: "1 diária"). e-003 (categoria
`representacao`, centro de custo `CC-SUPORTE-N2`, que não lista
`representacao` em `politica-v4.json`) → recusada por categoria fora da
política para aquele centro de custo.

### RN-010 — Despesas com valor negativo (estornos)

**Regra:** despesas com `valor_declarado` negativo não entram no cálculo de
nenhum limite, não são somadas em `resumo.total_declarado`, e aparecem no
resultado com `status = "ignorado"` e `valor_reembolsado = 0.00`.
**Origem:** política do RH, caso não previsto; AMB-009.
**Aceite:** d-009, valor -45,00 → `status: "ignorado"`, não entra em
nenhuma soma do dia nem do resumo.

### RN-011 — Precisão monetária

**Regra:** todo valor de entrada e todo valor calculado é arredondado para
2 casas decimais usando arredondamento banker's rounding (half-even) antes
de ser comparado a qualquer limite ou somado a outro valor.
**Origem:** AMB-011; necessidade de determinismo em ponto flutuante.
**Aceite:** d-011, valor 33.333 → tratado como 33.33 em todos os cálculos
e na saída.

### RN-012 — Normalização de categoria

**Regra:** a comparação de `categoria` contra as categorias oficiais
(`alimentacao`, `transporte_urbano`, `hospedagem`) é feita após converter
o valor de entrada para minúsculas. O campo `categoria_original` na saída
preserva o valor exatamente como veio na entrada; `categoria_aplicada`
reflete o valor normalizado/mapeado.
**Origem:** AMB-012.
**Aceite:** d-014, categoria `ALIMENTACAO` → normalizada para
`alimentacao` → avaliada normalmente pela RN-001.

### RN-013 — Limites de política por centro de custo

**Regra:** os limites diários/por diária de `alimentacao`,
`transporte_urbano` e `hospedagem`, o percentual de ampliação em viagem
(RN-006) e o gatilho de nota fiscal (RN-005) deixam de ser constantes
fixas e passam a ser lidos de uma tabela de política externa
(`politica-v4.json`), organizada por centro de custo. Para cada despesa,
os limites efetivos são resolvidos assim: (1) se o `centro_custo` do
colaborador existe em `centros_custo` e define a categoria da despesa,
usa o limite daquela entrada; (2) se o `centro_custo` existe mas não
define a categoria, usa o limite do bloco `padrao` para aquela categoria
(ver AMB-013); (3) se o `centro_custo` não existe na tabela nenhuma, usa
o bloco `padrao` por completo para todas as categorias (ver AMB-014). Um
limite explicitamente definido como `0.00` para uma categoria em um
centro de custo significa "não reembolsável" para esse centro de custo
(ver RN-016), e é diferente de "categoria ausente" (que cai no fallback
acima).
**Origem:** política v4, item A; AMB-013, AMB-014.
**Aceite:** d-012 (fictício, `CC-ENG-PLATAFORMA`) usa limite de
alimentação R$75,00/dia (específico do CC). Um colaborador de
`CC-ADM` (que não lista `hospedagem`) usa o limite padrão de R$250,00/
diária para hospedagem. Um colaborador de `CC-SUPORTE-N2` (ausente da
tabela) usa os três limites do bloco `padrao` integralmente.

### RN-014 — Categoria "representação"

**Regra:** `representacao` é uma categoria oficial reembolsável, mas
apenas para os centros de custo cuja entrada em `politica-v4.json` a
define explicitamente (hoje, somente `CC-COMERCIAL`, limite R$300,00/dia,
mesma lógica de soma diária e corte sequencial de RN-001/RN-004). Para
qualquer outro centro de custo — inclusive os ausentes da tabela, que
usam o bloco `padrao`, que não define `representacao` (ver AMB-014) —
uma despesa `representacao` é recusada por RN-009 (categoria fora da
política para aquele centro de custo). `representacao` não recebe a
ampliação de viagem de RN-006 (ver AMB-018), mas está sujeita a RN-005
(nota fiscal) e RN-008 (duplicata) como qualquer outra categoria.
**Origem:** política v4, item A; AMB-014, AMB-018.
**Aceite:** e-001, `CC-COMERCIAL`, `representacao`, R$340,00 → dentro do
limite diário de R$300,00? Não — excede, corte para R$300,00,
`aprovado_parcial`. f-003, `CC-SUPORTE-N2`, `representacao`, R$190,00 →
centro de custo ausente da tabela, usa só o `padrao`, que não tem
`representacao` → recusada por RN-009.

### RN-015 — Conversão de moeda estrangeira

**Regra:** quando `despesas[].moeda` está presente e é diferente de
`BRL`, o `valor` da despesa é convertido para BRL usando a taxa de
câmbio da **data da despesa** (campo `data`, não a data de execução do
motor), lida de uma tabela externa (`cambio.json`). Se a data exata não
tiver cotação publicada (ex.: fim de semana), usa-se a cotação do último
dia útil anterior disponível na tabela (ver AMB-016). Se a moeda
declarada não existir na tabela em nenhuma data, a despesa não é
processada: recebe `status = "nao_processado"`, `valor_reembolsado =
0.00`, e uma justificativa pedindo verificação manual do RH — e o
processamento das demais despesas continua normalmente (ver AMB-015). A
conversão ocorre **antes** de qualquer outra regra que dependa do valor
em BRL (nota fiscal, limite por diária, arredondamento final — ver
AMB-017 e seção 8). Despesas sem o campo `moeda` são tratadas como já
estando em `BRL`, sem conversão.
**Origem:** política v4, item B; AMB-015, AMB-016, AMB-017.
**Aceite:** e-002, `EUR` 22,00, data 2026-07-14 → taxa EUR do dia
(5,93) → R$130,46 → segue para as demais regras já em BRL. e-004, `EUR`
30,00, data 2026-07-18 (sábado, sem cotação publicada) → usa a taxa de
EUR do último dia útil anterior disponível (2026-07-17). e-006, `GBP`
55,00 → `GBP` não existe em `cambio.json` em nenhuma data → `status:
"nao_processado"`, processamento das demais despesas do colaborador
continua.

### RN-016 — Hospedagem não reembolsável por política do centro de custo

**Regra:** quando a tabela de política define o limite de `hospedagem`
como `0.00` para o centro de custo do colaborador (ver RN-013), toda
despesa de `hospedagem` (ou mapeada por analogia, ver AMB-008) daquele
centro de custo é recusada integralmente, com motivo próprio e distinto
de RN-003/AMB-010b: aqui a categoria é válida e o número de diárias pode
até ser identificável — a recusa é por decisão de política do centro de
custo, não por falta de dado (ver AMB-019).
**Origem:** política v4, item A; AMB-019.
**Aceite:** uma despesa de `hospedagem` de um colaborador de
`CC-ENG-PLATAFORMA`, com descrição "Hotel - 2 diárias" (número
perfeitamente identificável), é recusada integralmente porque o limite
daquele centro de custo para `hospedagem` é R$0,00 — não por AMB-010b.

### RN-017 — Fila de aprovação manual

**Regra:** despesas que, após todas as demais regras, teriam
`valor_reembolsado` **estritamente maior** que R$500,00 não são
aprovadas automaticamente. O status que seria `aprovado` ou
`aprovado_parcial` é substituído por `pendente`, mantendo o mesmo
`valor_reembolsado` calculado (o valor não muda, só o status), acrescido
do motivo RN-017 e de uma justificativa indicando que o item aguarda
aprovação do gestor. Despesas recusadas, ignoradas ou não processadas
nunca entram na fila — a verificação de R$500,00 só se aplica a despesas
que, de outra forma, seriam aprovadas (ver AMB-020, AMB-021). Despesas
`pendente` contam em `resumo.quantidade_pendentes`, um contador próprio,
separado de `quantidade_aprovadas` (ver AMB-022).
**Origem:** política v4, item C (opcional); AMB-020, AMB-021, AMB-022.
**Aceite:** e-007, `CC-COMERCIAL`, `hospedagem`, "Hotel Londres - 3
noites", R$1.200,00 → R$400,00/diária (limite de `CC-COMERCIAL`) → dentro
do limite → reembolso integral de R$1.200,00 > R$500,00 → status
`pendente` em vez de `aprovado`, motivo RN-017 acrescentado aos motivos
de RN-003.

---

## 6. Ambiguidades identificadas e decisões

> **Esta seção é o coração da spec e vale a maior parte dos 25 pontos do
> critério 1.** Uma ambiguidade que você resolveu no código sem registrar
> aqui conta como não resolvida.

### AMB-001 — Unidade de aplicação do limite de alimentação/transporte

**Texto original do RH:** "Alimentação tem limite de R$ 60 por dia."
/ "Transporte urbano tem limite de R$ 80 por dia."
**O que não está claro:** "por dia" pode significar por despesa individual
lançada naquele dia, ou pela soma de todas as despesas daquela categoria
naquele dia.
**Decisão:** o limite incide sobre a soma de todas as despesas da mesma
categoria lançadas na mesma data.
**Justificativa:** "por dia" é uma unidade de tempo, não de lançamento; se
fosse por despesa a política diria "por despesa" ou "por refeição". Permitir
múltiplos lançamentos ilimitados no mesmo dia tornaria o limite diário sem
efeito prático.
**Regra afetada:** RN-001, RN-002.

### AMB-002 — Significado de "reembolsado parcialmente"

**Texto original do RH:** "Despesas acima do limite são reembolsadas
parcialmente."
**O que não está claro:** pode significar que o sistema paga até o teto e
descarta o excedente, ou que o item inteiro é recusado quando ultrapassa o
limite (porque toda a despesa "ultrapassou", logo é inválida).
**Decisão:** o sistema reembolsa até o limite (corta no teto) e descarta
apenas o excedente.
**Justificativa:** a própria política usa a palavra "parcialmente" — se a
intenção fosse recusa total, diria "despesas acima do limite não são
reembolsadas".
**Regra afetada:** RN-001, RN-002, RN-003.

### AMB-003 — Fronteira do gatilho de nota fiscal

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** se "acima de R$100" inclui o valor de R$100,00
exato (>=) ou é estritamente maior (>).
**Decisão:** estritamente maior (>). R$100,00 exatos não exigem nota
fiscal.
**Justificativa:** "acima de" em português indica fronteira exclusiva; se a
intenção fosse incluir o próprio valor, diria "a partir de R$100" ou "R$100
ou mais".
**Regra afetada:** RN-005.

### AMB-004 — Consequência de nota fiscal ausente quando devida

**Texto original do RH:** item 5 só diz que a nota é obrigatória, não diz
o que acontece se faltar.
**O que não está claro:** se a ausência de nota fiscal obrigatória recusa o
item inteiro ou reduz o reembolso a um teto menor.
**Decisão:** recusa total (reembolso R$0,00) quando a nota é exigida e não
está presente.
**Justificativa:** "obrigatória" é uma condição binária de elegibilidade,
não um fator de desconto; tratar como glosa parcial criaria um teto que a
política nunca definiu.
**Regra afetada:** RN-005.

### AMB-005 — Definição de "em viagem"

**Texto original do RH:** "Colaborador em viagem tem limites ampliados em
50%." A entrada não tem nenhum campo que marque viagem.
**O que não está claro:** não há dado explícito de viagem; é preciso
inferir a condição a partir de outro sinal, ou simplesmente nunca aplicar a
regra.
**Decisão:** infere-se viagem pela presença de uma despesa de hospedagem na
mesma data; a ampliação de 50% vale apenas no(s) dia(s) em que há
hospedagem lançada, e apenas para alimentação e transporte urbano (não para
o próprio limite de hospedagem).
**Justificativa:** hospedagem é o sinal mais direto e verificável disponível
nos dados de que o colaborador estava fora de sua base; aplicar a ampliação
sobre o limite de hospedagem seria redundante, pois esse limite já é
desenhado para despesa de viagem.
**Regra afetada:** RN-006.

### AMB-006 — Despesa fora do período de competência

**Texto original do RH:** "Despesas devem ser lançadas dentro do período de
competência."
**O que não está claro:** a política não diz a consequência de uma despesa
com data fora do período — recusa, aceita com ressalva, ou desloca para o
período correto.
**Decisão:** recusa integral (reembolso R$0,00) de qualquer despesa cuja
data esteja fora do intervalo `periodo.inicio`–`periodo.fim`.
**Justificativa:** a palavra "devem" indica obrigação; uma obrigação
descumprida sem consequência não é uma regra, é uma sugestão — e o motor
precisa de uma decisão operacional, não de uma reprimenda.
**Regra afetada:** RN-007.

### AMB-007 — Definição e tratamento de duplicata

**Texto original do RH:** "Duplicatas devem ser tratadas."
**O que não está claro:** não define o que caracteriza uma duplicata (mesmo
valor? mesmo dia? mesmo fornecedor? todas as combinações?) nem qual ação
tomar.
**Decisão:** duplicata = mesma data + categoria (normalizada) + valor +
fornecedor. Entre duplicatas, mantém a de menor id (primeiro lançamento) e
recusa integralmente as demais.
**Justificativa:** esses quatro campos juntos descrevem o mesmo evento
econômico relatado mais de uma vez; exigir todos os quatro evita falsos
positivos (duas corridas de taxi de mesmo valor em dias diferentes não são
duplicata).
**Regra afetada:** RN-008.

### AMB-008 — Categorias fora da lista oficial (dado ausente de mapeamento)

**Texto original do RH:** "Categorias fora da política não são
reembolsáveis", mas a política só define limite para alimentação,
transporte urbano e hospedagem.
**O que não está claro:** se uma categoria presente na entrada mas não
citada literalmente (ex.: `coworking`) deve ser recusada por não constar na
lista, ou mapeada para a categoria oficial mais próxima por analogia de
natureza do gasto.
**Decisão:** mapear por analogia quando a natureza do gasto é equivalente;
`coworking` é tratado como `hospedagem` (espaço de trabalho temporário,
mesma lógica de diária) e segue o limite de R$250,00/diária.
**Justificativa:** recusar automaticamente qualquer rótulo que não bata
letra por letra com a política penaliza a variação natural de nomenclatura
de fornecedores/sistemas de despesa; mapear por natureza do gasto é mais
fiel à intenção da política do que ao texto literal dela. Qualquer
categoria sem analogia razoável continua recusada (RN-009).
**Regra afetada:** RN-009.

### AMB-009 — Despesas com valor negativo (estorno)

**Texto original do RH:** a política não menciona valores negativos em
nenhum item.
**O que não está claro:** se um estorno deve ser ignorado, compensar o
total do dia/categoria, ou ser tratado como erro de entrada.
**Decisão:** despesas com valor negativo são ignoradas — não participam de
nenhuma soma (diária, de categoria ou do resumo) e aparecem na saída com
status próprio (`ignorado`).
**Justificativa:** um estorno de despesa cancelada não representa gasto
nem reembolso; não é papel do motor de cálculo de reembolso reconciliar
lançamentos de cancelamento — isso é operação de bilhetagem/cobrança, fora
do escopo deste sistema.
**Regra afetada:** RN-010.

### AMB-010 — Número de diárias de hospedagem (dado ausente)

**Texto original do RH:** "Hospedagem tem limite de R$250 por diária." A
entrada não tem campo estruturado de número de diárias/noites.
**O que não está claro:** como aplicar um limite "por diária" quando a
única informação sobre quantidade de diárias está em texto livre na
descrição (ex.: "2 diárias", "3 noites").
**Decisão:** extrai-se o número de diárias/noites por reconhecimento de
texto na descrição; se nenhum número for identificável, a despesa é
recusada integralmente por falta de dado suficiente para aplicar a regra
com segurança.
**Justificativa:** calcular o limite sobre o valor total sem dividir pelas
diárias tornaria hospedagens de várias noites artificialmente mais
restritivas que uma única diária cara; recusar no fallback evita assumir
"1 diária" por padrão quando a descrição sugere claramente que há mais de
uma, o que mascararia uma violação real do limite.
**Regra afetada:** RN-003.

### AMB-011 — Precisão e arredondamento monetário

**Texto original do RH:** a política não menciona precisão numérica em
nenhum item; a entrada tem um valor com 3 casas decimais (d-011: 33.333).
**O que não está claro:** qual regra de arredondamento aplicar para que o
resultado seja determinístico e auditável.
**Decisão:** todo valor é arredondado para 2 casas decimais com
arredondamento banker's rounding (half-even) antes de qualquer comparação
ou soma.
**Justificativa:** half-even é o padrão usado por sistemas financeiros para
evitar viés sistemático de arredondamento ao longo de muitas operações
(diferente do half-up, que sempre arredonda para cima em empates e
acumula um viés positivo).
**Regra afetada:** RN-011.

### AMB-012 — Sensibilidade a maiúsculas/minúsculas na categoria

**Texto original do RH:** a política não especifica formatação; a entrada
tem uma categoria em maiúsculas (d-014: `ALIMENTACAO`).
**O que não está claro:** se a comparação de categoria deve ser exata
(diferenciando caixa) ou normalizada.
**Decisão:** comparação case-insensitive — a categoria de entrada é
normalizada para minúsculas antes de qualquer comparação com as categorias
oficiais.
**Justificativa:** a variação de caixa é um detalhe de formatação de
origem (ex.: sistema legado, erro de digitação), não uma informação de
negócio distinta; penalizar isso recusando a despesa seria tratar um
problema de dados como se fosse uma regra de política.
**Regra afetada:** RN-012.

### AMB-013 — Categoria ausente dentro de um centro de custo parcialmente definido

**Texto original do RH:** "Alguns centros de custo não têm entrada na
tabela. Nesse caso, aplica-se a política padrão." O comunicado só cobre
o CC totalmente ausente; não diz o que fazer quando o CC existe mas não
lista uma categoria específica (ex.: `CC-ADM` não lista `hospedagem`).
**O que não está claro:** se a ausência da categoria dentro de um CC que
existe parcialmente herda o limite padrão só para aquela categoria, ou é
equivalente a "não reembolsável" (como o `limite: 0.00` explícito de
`CC-ENG-PLATAFORMA` para hospedagem).
**Decisão:** herda o limite do bloco `padrao` apenas para a categoria
ausente; as demais categorias do mesmo CC continuam usando os valores
específicos que ele define.
**Justificativa:** "não reembolsável" é uma decisão de política que a
tabela sempre expressa explicitamente com `limite: 0.00` (como fez para
`CC-ENG-PLATAFORMA`/hospedagem); ausência de entrada é diferente de
zero explícito, e tratar os dois da mesma forma faria uma lacuna de
cadastro (categoria nunca preenchida) se comportar como uma decisão
deliberada de política, que ninguém tomou.
**Regra afetada:** RN-013.

### AMB-014 — Centro de custo totalmente ausente da tabela

**Texto original do RH:** "Alguns centros de custo não têm entrada na
tabela. Nesse caso, aplica-se a política padrão."
**O que não está claro:** se "aplica-se a política padrão" significa usar
só o bloco `padrao` (que não define `representacao`), ou se o CC ausente
deveria herdar também categorias extras definidas para outros CCs.
**Decisão:** usa o bloco `padrao` integralmente, sem herdar nada de
outros centros de custo. Como `representacao` não existe no bloco
`padrao`, um colaborador de um CC ausente da tabela nunca tem
`representacao` reembolsável.
**Justificativa:** "política padrão" é um conceito definido e nomeado na
própria tabela (`politica-v4.json`, chave `padrao`); herdar categorias de
outro CC específico exigiria uma regra de qual CC "doa" a categoria, que
a política nunca definiu — e inventar essa regra seria o mesmo erro de
"assumir dado ausente" que AMB-010 já rejeitou para diárias de
hospedagem.
**Regra afetada:** RN-013, RN-009, RN-014.

### AMB-015 — Moeda declarada sem cotação em `cambio.json`

**Texto original do RH:** "A conversão usa a taxa da data da despesa...
As taxas estão em `cambio.json`." O comunicado não cobre o caso de uma
moeda que simplesmente não existe na tabela.
**O que não está claro:** se a ausência total da moeda na tabela de
câmbio deve recusar a despesa, interromper toda a execução como erro
fatal, ou alguma terceira opção.
**Decisão:** a despesa não é processada — recebe `status =
"nao_processado"`, `valor_reembolsado = 0.00` e uma justificativa
explícita pedindo verificação manual do RH; o processamento das demais
despesas do colaborador e dos demais colaboradores continua
normalmente.
**Justificativa:** não é um erro de formato de entrada (a estrutura do
JSON está correta, a moeda é um código ISO 4217 válido) para justificar
abortar a execução inteira como se fosse JSON malformado; também não é
uma recusa de mérito de negócio (RN-009/RN-005/etc.) porque o motor não
tem como avaliar o mérito sem a taxa. É dado externo insuficiente para
decidir com segurança — mesmo princípio de AMB-010b (hospedagem sem
diárias identificáveis), mas como aqui a causa é uma lacuna de cadastro
do financeiro, não do colaborador, o rótulo é "não processado", não
"recusado", para deixar claro que a bola está com quem mantém
`cambio.json`.
**Regra afetada:** RN-015.

### AMB-016 — Data da despesa sem cotação publicada (dia não útil)

**Texto original do RH:** "A conversão usa a taxa da data da despesa."
`cambio.json` só publica cotações em dias úteis bancários.
**O que não está claro:** o que fazer quando a data exata da despesa cai
em um dia sem publicação (fim de semana, feriado) e portanto sem entrada
na tabela.
**Decisão:** usa a cotação do último dia útil anterior disponível na
tabela.
**Justificativa:** é a convenção padrão de mercado para cotações PTAX
(a própria fonte citada em `cambio.json`) — o câmbio de uma despesa de
sábado é, na prática financeira real, resolvido pela taxa de fechamento
de sexta-feira, porque não existe pregão no fim de semana. Usar a taxa
do dia seguinte inverteria causalidade (taxa que ainda não existia no
momento da despesa); recusar a despesa só por cair num fim de semana
seria uma barreira operacional que a política nunca pediu.
**Regra afetada:** RN-015.

### AMB-017 — Ordem da conversão de moeda em relação às demais regras

**Texto original do RH:** "Os limites da política são sempre em BRL. Uma
despesa em EUR é convertida antes de ser comparada ao limite." O
comunicado não diz se a conversão também antecede RN-005 (nota fiscal)
e RN-011 (arredondamento).
**O que não está claro:** se o gatilho de nota fiscal (R$100,00) e o
cálculo de diárias de hospedagem avaliam o valor na moeda original ou já
convertido.
**Decisão:** a conversão para BRL ocorre logo após a resolução de
categoria/centro de custo, antes de qualquer regra que compare ou some
valores (RN-005, RN-003, RN-001/002/004, RN-011). Toda regra seguinte na
ordem de aplicação (seção 8) vê apenas o valor já em BRL e já
arredondado.
**Justificativa:** o próprio comunicado afirma que os limites "são
sempre em BRL" e que a conversão acontece "antes de ser comparada ao
limite" — isso só é consistente se toda comparação numérica (não só o
limite diário, mas também o gatilho de nota fiscal, que é igualmente
"uma comparação contra um valor em BRL") ocorrer sobre o valor
convertido; avaliar RN-005 na moeda original criaria um gatilho que
muda de significado dependendo da moeda declarada, o que o comunicado
não sugere em nenhum momento.
**Regra afetada:** RN-015, RN-005, RN-003, RN-011.

### AMB-018 — Ampliação de viagem e a categoria "representação"

**Texto original do RH:** o comunicado define `representacao` como
categoria nova com limite diário, mas não menciona se ela participa da
ampliação de viagem (política original, item 6).
**O que não está claro:** se o acréscimo de 50% em dia de viagem
(RN-006) se estende à nova categoria `representacao`, que também tem
limite por dia.
**Decisão:** não. A ampliação de viagem continua restrita a
`alimentacao` e `transporte_urbano`.
**Justificativa:** a ampliação de viagem, desde a decisão original
(AMB-005), compensa o custo inevitável de estar fora da base
(alimentação, deslocamento) — uma despesa de representação comercial
(jantar com cliente/fornecedor) não é um custo que aumenta por estar em
viagem, é uma decisão de relacionamento comercial com teto próprio e
razão de ser independente de o colaborador estar ou não viajando.
Estender a ampliação a ela extrapolaria a política além do que o RH
pediu.
**Regra afetada:** RN-006, RN-014.

### AMB-019 — Hospedagem zerada por política de centro de custo vs. falta de dado

**Texto original do RH:** "`CC-ENG-PLATAFORMA` não reembolsa hospedagem
de forma alguma."
**O que não está claro:** se essa recusa usa o mesmo motivo de
RN-003/AMB-010b (diárias não identificáveis) ou é um motivo diferente.
**Decisão:** motivo próprio (RN-016), distinto de AMB-010b. A recusa por
`limite: 0.00` de política de CC acontece mesmo quando o número de
diárias é perfeitamente identificável na descrição.
**Justificativa:** confundir os dois motivos esconderia a causa real da
recusa de quem lê a saída — um auditor que veja "RN-003: diárias não
identificáveis" tentaria corrigir a descrição da despesa, quando o
problema real é que aquele centro de custo nunca reembolsa hospedagem,
independentemente da qualidade da descrição. Motivos de recusa precisam
apontar para a causa que, se corrigida, mudaria o resultado — e aqui
nada que o colaborador faça na descrição mudaria o resultado.
**Regra afetada:** RN-016, RN-013.

### AMB-020 — Fronteira do limiar de aprovação manual (R$500)

**Texto original do RH:** "Itens cujo valor reembolsável passe de
R$ 500 não são mais aprovados automaticamente."
**O que não está claro:** se "passe de R$500" inclui o valor de R$500,00
exato (>=) ou é estritamente maior (>) — mesma classe de ambiguidade de
AMB-003 (nota fiscal).
**Decisão:** estritamente maior (>). R$500,00 exato continua aprovado
automaticamente.
**Justificativa:** mesma leitura linguística de AMB-003 — "passar de"
indica fronteira exclusiva; manter a mesma convenção para os dois
gatilhos de valor desta spec (R$100 de nota fiscal, R$500 de aprovação
manual) evita que o motor use critérios de fronteira inconsistentes
entre regras parecidas sem motivo de negócio para a diferença.
**Regra afetada:** RN-017.

### AMB-021 — Como o status "pendente" se encaixa nos status existentes

**Texto original do RH:** "Eles entram em estado de pendência... cada
item passa a ter um estado." O comunicado não detalha a mecânica do
novo estado frente aos status já existentes.
**O que não está claro:** se `pendente` substitui `aprovado`/
`aprovado_parcial` quando o valor ultrapassa R$500, ou se é um status
que pode coexistir com qualquer resultado anterior (inclusive recusa).
**Decisão:** `pendente` substitui `aprovado`/`aprovado_parcial` quando
`valor_reembolsado` > R$500,00. Despesas recusadas, ignoradas ou não
processadas nunca entram na fila — a verificação só se aplica ao
resultado que, de outra forma, seria uma aprovação.
**Justificativa:** uma despesa recusada já teve seu mérito decidido
negativamente; não existe "pendência de aprovação" sobre um valor que é
R$0,00. A fila de aprovação manual é, pela própria descrição do RH, uma
trava adicional sobre o caminho de aprovação, não um status paralelo
independente do resultado das demais regras.
**Regra afetada:** RN-017.

### AMB-022 — Contagem de despesas pendentes no resumo

**Texto original do RH:** não cobre o impacto no relatório agregado; é
inferência direta da introdução do novo status.
**O que não está claro:** se `resumo.quantidade_aprovadas` deveria
continuar contando despesas `pendente` (porque "seriam aprovadas se não
fosse o valor") ou se merece contador próprio.
**Decisão:** novo campo `resumo.quantidade_pendentes`, separado de
`quantidade_aprovadas`. Uma despesa `pendente` não é contada em
`quantidade_aprovadas`.
**Justificativa:** o próprio objetivo do item C é parar de tratar esses
itens como aprovados automaticamente — contá-los dentro de
`quantidade_aprovadas` do relatório contradiria a razão de existir da
regra. Um contador próprio é a única forma de o relatório refletir
fielmente que esses itens aguardam decisão humana.
**Regra afetada:** RN-017.

### AMB-023 — Redefinição de `quantidade_aprovadas` como conjunto explícito

**Texto original do RH:** não se aplica; é correção de uma fragilidade
da própria spec, exposta pela introdução dos novos status `pendente` e
`nao_processado`.
**O que não está claro:** a definição herdada da v1.0
(`quantidade_aprovadas` = "status != recusado") já incluía
implicitamente `ignorado` (estornos) de forma potencialmente enganosa
(ver `docs/auditoria-resultado-2026-07.md`); com dois status novos
(`pendente`, `nao_processado`), manter essa definição por exclusão
tornaria a contagem cada vez mais distante do que o nome do campo sugere.
**Decisão:** `quantidade_aprovadas` passa a ser definida por inclusão
explícita: contagem de despesas com `status` em `{"aprovado",
"aprovado_parcial"}`. `ignorado`, `nao_processado` e `pendente` cada um
tem (ou, no caso de `ignorado`, poderia ter) seu próprio contador, fora
de `quantidade_aprovadas` e `quantidade_recusadas`.
**Justificativa:** um campo chamado "quantidade_aprovadas" deve contar
exatamente o que foi aprovado — definição por exclusão ("tudo que não é
recusado") é um atalho que só funcionava enquanto só existiam dois
status finais opostos; com cinco status possíveis, a definição por
exclusão deixou de ser uma simplificação razoável e passou a ser uma
fonte de leitura equivocada do relatório.
**Regra afetada:** seção 4 (saída), RN-017.

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Duas despesas de alimentação no mesmo dia somam acima do limite | d-001, d-002 | Primeira absorve o limite; segunda é recusada integralmente | RN-001, RN-004 |
| Transporte urbano exatamente no limite de nota fiscal | d-003 (R$100,00) | Não exige nota fiscal; segue para demais regras | RN-005, AMB-003 |
| Transporte urbano um centavo acima do limite de nota, sem nota | d-004 (R$100,01) | Recusado integralmente por falta de nota | RN-005 |
| Categoria não citada na política mas análoga a uma oficial, sem diária identificável na descrição | d-005 (`coworking`) | Mapeada para hospedagem; sem número de diárias extraível → recusada integralmente | RN-009, AMB-008, RN-003, AMB-010b |
| Despesa fora do período de competência | d-008 (data de abril, período julho) | Recusada integralmente | RN-007 |
| Estorno/valor negativo | d-009 (-R$45,00) | Ignorado; não entra em nenhuma soma | RN-010 |
| Hospedagem multi-diária com número extraível da descrição | d-010 | Limite aplicado por diária (valor total / nº diárias) | RN-003 |
| Hospedagem multi-diária que exigiria nota fiscal e não tem | d-013 (R$690,00, sem nota) | Recusada por falta de nota (RN-005), antes de chegar à agregação por diária | RN-005 |
| Valor com mais de 2 casas decimais | d-011 (33.333) | Arredondado para 33,33 antes de qualquer cálculo | RN-011 |
| Despesas idênticas em data/categoria/valor/fornecedor | d-006, d-007 | A de menor id segue normalmente; a outra é recusada por duplicata | RN-008 |
| Categoria em caixa diferente da oficial | d-014 (`ALIMENTACAO`) | Normalizada para minúsculas e avaliada normalmente | RN-012 |
| Despesa lançada em fim de semana | d-012 (sábado) | Tratada como qualquer outro dia; nenhuma regra especial | — (ver seção 10) |
| Hospedagem sem número de diárias identificável na descrição | hipotético, não presente no exemplo | Recusada integralmente por falta de dado | RN-003, AMB-010 |
| Centro de custo com limite específico para a categoria | e-001 (`CC-COMERCIAL`, `representacao`, R$340,00) | Limite diário de R$300,00 (específico do CC); excede, corte para R$300,00 | RN-013, RN-014 |
| Categoria `representacao` em centro de custo sem essa categoria na tabela | f-003 (`CC-SUPORTE-N2`, `representacao`) | Recusada por categoria fora da política para aquele CC | RN-009, RN-014, AMB-014 |
| Hospedagem com diárias identificáveis mas CC não reembolsa a categoria | hipotético, `CC-ENG-PLATAFORMA` | Recusada por política do CC (RN-016), não por falta de dado (AMB-010b) | RN-016, AMB-019 |
| Despesa em moeda estrangeira com cotação na data exata | e-002 (`EUR` 22,00, 2026-07-14) | Convertida para BRL pela taxa do dia antes de qualquer outra regra | RN-015 |
| Despesa em moeda estrangeira em dia sem cotação publicada | e-004 (`EUR`, sábado 2026-07-18) | Convertida pela taxa do último dia útil anterior | RN-015, AMB-016 |
| Despesa em moeda sem nenhuma cotação na tabela | e-006 (`GBP`) | `status: "nao_processado"`; demais despesas continuam sendo processadas | RN-015, AMB-015 |
| Valor reembolsável final acima de R$500 | e-007 (`CC-COMERCIAL`, hospedagem, R$1.200,00) | `status: "pendente"` em vez de `aprovado`, mesmo valor reembolsado | RN-017, AMB-020, AMB-021 |

## 8. Ordem de aplicação das regras

Cada despesa passa pelas regras na seguinte ordem. A primeira regra que
recusa a despesa integralmente interrompe a avaliação das regras
seguintes (a despesa não acumula múltiplos motivos de recusa):

1. **Valor negativo (RN-010):** se negativo, marca como `ignorado` e
   encerra — não participa de nenhuma soma.
2. **Categoria válida/mapeável para o centro de custo (RN-009, RN-012,
   RN-014):** normaliza a categoria; se não for uma das oficiais
   disponíveis para aquele centro de custo (considerando `representacao`
   apenas onde a política a lista), nem mapeável por analogia, recusa.
3. **Conversão de moeda (RN-015):** se `moeda` != `BRL`, converte para
   BRL pela taxa da data da despesa (ou do último dia útil anterior); se
   a moeda não existir na tabela de câmbio, marca como `nao_processado` e
   encerra — não participa de nenhuma soma, mas não interrompe o
   processamento das demais despesas.
4. **Período de competência (RN-007):** se a data está fora do período,
   recusa.
5. **Duplicata (RN-008):** se é duplicata de uma despesa de menor id já
   processada, recusa.
6. **Nota fiscal obrigatória (RN-005):** se o valor (já em BRL) exige
   nota e ela não existe, recusa.
7. **Hospedagem não reembolsável por política do CC (RN-016):** se a
   categoria é hospedagem e o centro de custo tem limite R$0,00 para
   ela, recusa — antes de tentar extrair diárias da descrição.
8. **Agregação por dia e aplicação do limite (RN-001, RN-002, RN-003,
   RN-004, RN-006, RN-013, RN-014):** só despesas que passaram pelos
   passos 1–7 entram na soma diária por categoria; o limite vigente para
   o centro de custo (ampliado em viagem quando aplicável e quando a
   categoria participa da ampliação) é aplicado sobre essa soma, com
   corte sequencial por ordem de lançamento.
9. **Fila de aprovação manual (RN-017):** se o `valor_reembolsado` final
   de uma despesa que seria `aprovado`/`aprovado_parcial` é maior que
   R$500,00, o status é substituído por `pendente`.

Essa ordem importa porque garante que uma despesa recusada por motivo
estrutural (duplicata, fora do período, sem nota, moeda sem cotação)
nunca "ocupa" espaço do limite diário de outra despesa legítima do mesmo
dia, e que a fila de aprovação manual (último passo) só reage ao valor
já definitivo de cada despesa.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] Processa `exemplos/despesas-exemplo.json` e produz saída conforme a
      seção 4, sem erros.
- [ ] Cada uma das 14 despesas do exemplo recebe o status e valor
      reembolsado previstos nas seções 5 e 7 desta spec.
- [ ] Processa `exemplos/envelope/despesas-envelope.json` (com
      `exemplos/envelope/politica-v4.json` e `exemplos/envelope/cambio.json`)
      e produz o status/valor previstos nas seções 5 e 7 para cada despesa
      (e-001 a e-010), incluindo conversão de moeda, limites por centro de
      custo e fila de aprovação manual.
- [ ] Processa `exemplos/envelope/despesas-envelope-cc-desconhecido.json` e
      aplica a política padrão integralmente (RN-013/AMB-014), recusando
      `representacao` por categoria fora da política (RN-009/RN-014).
- [ ] RN-001 a RN-017 têm, cada uma, ao menos um teste automatizado que
      verifica o caso de aceite descrito na seção 5.
- [ ] Todas as linhas da tabela de casos de borda (seção 7) têm teste
      correspondente.
- [ ] A soma de `resumo.total_reembolsado` + `resumo.total_recusado` é
      igual a `resumo.total_declarado` para qualquer entrada válida
      (despesas `ignorado`/`nao_processado` continuam fora dessa soma).
- [ ] Entrada com JSON malformado ou campo obrigatório ausente produz erro
      claro na CLI, sem gerar arquivo de saída parcial.
- [ ] Nenhuma regra de negócio desta spec está codificada apenas em
      comentário de código ou apenas na conversa com o agente — toda regra
      usada no cálculo tem um RN-00X correspondente aqui.

## 10. O que fica em aberto

- **Fim de semana / plantão (d-012):** a política não fala nada sobre
  despesas em fins de semana ou fora do horário comercial. Decisão
  provisória: tratar como dia normal, sem regra especial — criar uma regra
  não solicitada seria inventar política que o RH nunca escreveu. Se essa
  leitura estiver errada, é uma mudança de requisito, não um bug.
- **Mapeamento de categorias por analogia (AMB-008):** hoje só existe uma
  entrada mapeada (`coworking` → `hospedagem`). Se aparecerem outras
  categorias não oficiais no futuro, cada uma precisará de uma decisão
  explícita registrada aqui antes de entrar no mapeamento — não existe uma
  regra geral de "o que é análogo a quê".
- **Limite de diárias de hospedagem sem padrão de texto reconhecível:**
  a extração de número de diárias da descrição depende de um padrão de
  texto razoavelmente previsível ("N diárias", "N noites"). Descrições em
  formatos muito diferentes do exemplo podem não ser reconhecidas e cair
  no fallback de recusa (RN-003) mesmo quando a despesa seria legítima —
  risco aceito nesta versão.
- **`politica-v4.json`/`cambio.json` ausentes ou não informados (v4):** se
  os caminhos não forem passados na execução, o motor usa a política
  padrão embutida (equivalente à v3, sem `representacao`) e não converte
  nenhuma despesa em moeda estrangeira — toda despesa com `moeda` != `BRL`
  cairia em `nao_processado` (RN-015/AMB-015) por falta de tabela de
  câmbio, não por a moeda ser desconhecida. É uma decisão de
  degradação segura: processar sem política/câmbio nunca inventa uma
  taxa ou limite, apenas marca o que não pôde ser decidido.
- **Mudança de tabela de política/câmbio em tempo de execução:** o
  comunicado diz que a tabela "muda sem aviso". Esta versão lê o arquivo
  uma vez no início da execução (cada chamada da CLI é stateless, como já
  definido na seção 3); não há cache entre execuções nem recarregamento a
  meio da execução — se o arquivo mudar, a próxima chamada da CLI já usa
  a versão nova, o que é suficiente para o escopo deste sistema (ver
  seção 3, "não persiste dados entre execuções").
