# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** aprovada · **Última alteração:** 2026-07-01

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
| `despesas[].valor` | número | Valor da despesa em reais | Sim |
| `despesas[].tem_nota_fiscal` | booleano | Se há nota fiscal anexada | Sim |

**Saída:** definida por mim. Estrutura e significado de cada campo:

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador` | objeto | Cópia do bloco `colaborador` da entrada |
| `periodo` | objeto | Cópia do bloco `periodo` da entrada |
| `despesas[].id` | string | Id da despesa de origem |
| `despesas[].categoria_original` | string | Categoria exatamente como veio na entrada |
| `despesas[].categoria_aplicada` | string | Categoria oficial usada para calcular o limite (após normalização/mapeamento, ver AMB-008) |
| `despesas[].valor_declarado` | número | Valor original da entrada |
| `despesas[].valor_reembolsado` | número | Valor efetivamente reembolsado (0 se recusado) |
| `despesas[].status` | string | `"aprovado"`, `"aprovado_parcial"` ou `"recusado"` |
| `despesas[].motivos` | lista de strings | Um ou mais códigos de regra (`RN-00X`) que determinaram o resultado |
| `despesas[].justificativa` | string | Frase legível explicando a decisão |
| `resumo.total_declarado` | número | Soma de `valor_declarado` de todas as despesas processadas (excluindo estornos ignorados, ver AMB-009) |
| `resumo.total_reembolsado` | número | Soma de `valor_reembolsado` |
| `resumo.total_recusado` | número | `total_declarado - total_reembolsado` |
| `resumo.quantidade_despesas` | número | Total de despesas na entrada |
| `resumo.quantidade_aprovadas` | número | Despesas com `status != "recusado"` |
| `resumo.quantidade_recusadas` | número | Despesas com `status == "recusado"` |

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
**Aceite:** d-010 "Hotel Rio - 2 diárias", valor R$480,00 → R$240,00/diária
→ dentro do limite de R$250,00/diária → reembolso integral de R$480,00.
d-013 "Airbnb 3 noites", valor R$690,00 → R$230,00/diária → dentro do
limite → reembolso integral de R$690,00.

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
específica, os limites diários de `alimentacao` (R$60,00) e
`transporte_urbano` (R$80,00) são ampliados em 50% (R$90,00 e R$120,00,
respectivamente). O limite de hospedagem (R$250,00/diária) não é ampliado —
já é, por definição, o limite de uma despesa de viagem.
**Origem:** política do RH, item 6; AMB-005.
**Aceite:** se houvesse uma despesa de alimentação em 2026-07-14 (data de
d-010, hospedagem), o limite diário de alimentação naquela data seria
R$90,00 em vez de R$60,00.

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

**Regra:** apenas três categorias são reembolsáveis: `alimentacao`,
`transporte_urbano` e `hospedagem` (comparação case-insensitive, ver
AMB-012). A categoria `coworking` é mapeada para `hospedagem` antes de
aplicar o limite (ver AMB-008). Qualquer outra categoria não mapeada é
recusada integralmente, com motivo "categoria fora da política".
**Origem:** política do RH, item 9.
**Aceite:** d-005, categoria `coworking`, valor R$89,00 → mapeada para
`hospedagem` → avaliada com limite de R$250,00/diária (1 diária implícita,
ver RN-003) → dentro do limite → reembolso integral de R$89,00.

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

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Duas despesas de alimentação no mesmo dia somam acima do limite | d-001, d-002 | Primeira absorve o limite; segunda é recusada integralmente | RN-001, RN-004 |
| Transporte urbano exatamente no limite de nota fiscal | d-003 (R$100,00) | Não exige nota fiscal; segue para demais regras | RN-005, AMB-003 |
| Transporte urbano um centavo acima do limite de nota, sem nota | d-004 (R$100,01) | Recusado integralmente por falta de nota | RN-005 |
| Categoria não citada na política mas análoga a uma oficial | d-005 (`coworking`) | Mapeada para hospedagem; avaliada com limite de R$250/diária | RN-009, AMB-008 |
| Despesa fora do período de competência | d-008 (data de abril, período julho) | Recusada integralmente | RN-007 |
| Estorno/valor negativo | d-009 (-R$45,00) | Ignorado; não entra em nenhuma soma | RN-010 |
| Hospedagem multi-diária com número extraível da descrição | d-010, d-013 | Limite aplicado por diária (valor total / nº diárias) | RN-003 |
| Valor com mais de 2 casas decimais | d-011 (33.333) | Arredondado para 33,33 antes de qualquer cálculo | RN-011 |
| Despesas idênticas em data/categoria/valor/fornecedor | d-006, d-007 | A de menor id segue normalmente; a outra é recusada por duplicata | RN-008 |
| Categoria em caixa diferente da oficial | d-014 (`ALIMENTACAO`) | Normalizada para minúsculas e avaliada normalmente | RN-012 |
| Despesa lançada em fim de semana | d-012 (sábado) | Tratada como qualquer outro dia; nenhuma regra especial | — (ver seção 10) |
| Hospedagem sem número de diárias identificável na descrição | hipotético, não presente no exemplo | Recusada integralmente por falta de dado | RN-003, AMB-010 |

## 8. Ordem de aplicação das regras

Cada despesa passa pelas regras na seguinte ordem. A primeira regra que
recusa a despesa integralmente interrompe a avaliação das regras
seguintes (a despesa não acumula múltiplos motivos de recusa):

1. **Valor negativo (RN-010):** se negativo, marca como `ignorado` e
   encerra — não participa de nenhuma soma.
2. **Categoria válida/mapeável (RN-009, RN-012):** normaliza a categoria;
   se não for uma das três oficiais nem mapeável por analogia, recusa.
3. **Período de competência (RN-007):** se a data está fora do período,
   recusa.
4. **Duplicata (RN-008):** se é duplicata de uma despesa de menor id já
   processada, recusa.
5. **Nota fiscal obrigatória (RN-005):** se o valor exige nota e ela não
   existe, recusa.
6. **Agregação por dia e aplicação do limite (RN-001, RN-002, RN-003,
   RN-004, RN-006):** só despesas que passaram pelos passos 1–5 entram na
   soma diária por categoria; o limite (ampliado em viagem quando
   aplicável) é aplicado sobre essa soma, com corte sequencial por ordem
   de lançamento.

Essa ordem importa porque garante que uma despesa recusada por motivo
estrutural (duplicata, fora do período, sem nota) nunca "ocupa" espaço do
limite diário de outra despesa legítima do mesmo dia.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] Processa `exemplos/despesas-exemplo.json` e produz saída conforme a
      seção 4, sem erros.
- [ ] Cada uma das 14 despesas do exemplo recebe o status e valor
      reembolsado previstos nas seções 5 e 7 desta spec.
- [ ] RN-001 a RN-012 têm, cada uma, ao menos um teste automatizado que
      verifica o caso de aceite descrito na seção 5.
- [ ] Todas as linhas da tabela de casos de borda (seção 7) têm teste
      correspondente.
- [ ] A soma de `resumo.total_reembolsado` + `resumo.total_recusado` é
      igual a `resumo.total_declarado` para qualquer entrada válida.
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
