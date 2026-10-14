# Relatório — Desafio SDD

**Aluno:** `<nome>` · **Repositório:** `<link>` · **Data:** `<preencher ao entregar>`

> Isto não é redação. São **evidências**. Toda afirmação deve vir acompanhada de
> arquivo, hash de commit ou trecho de sessão exportada. Um parágrafo bonito sem
> evidência vale menos que uma frase curta com um hash.
>
> Vale 20 dos 100 pontos, e é a seção que mais separa notas.

> **Nota de rascunho:** este arquivo foi pré-preenchido com evidências objetivas
> (hashes, arquivos, cronologia) que já existem no repositório. Os campos de
> reflexão pessoal (`<...>`) são seus — preencha com sua própria avaliação antes
> de entregar. Os blocos "O envelope" e partes de "Diligência"/sessões ficam
> pendentes até o envelope do Dia 2 chegar e as sessões serem exportadas.

---

## Delegação

*O que você fez, o que o Claude fez, e por que dividiu assim.*

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades candidatas | Claude (levantamento inicial cruzando a política com `despesas-exemplo.json`, item por item) | Varredura mecânica e exaustiva é tarefa de busca, não de julgamento de negócio |
| Decidir cada ambiguidade | Humano, uma a uma, via perguntas estruturadas | Cada decisão é um critério de negócio sem resposta "certa" — exige quem responde pelo resultado |
| Escrever `spec.md`/`plan.md`/`tasks.md` | Claude (redação), a partir das decisões já tomadas pelo humano | Redação mecânica após decisão já tomada; risco de "spec aceita sem revisão" mitigado por decisão prévia explícita |
| Desenhar a arquitetura (`plan.md`) | Claude, com justificativa de alternativas descartadas | Escolha técnica sem impacto de regra de negócio |
| Implementar (T-001 a T-020) | Claude | Implementação mecânica a partir de tasks já definidas |
| Escrever testes | Claude | Mesmo risco de "teste complacente" descrito na seção Diligência abaixo |
| Absorver o envelope (Dia 2) | `<pendente>` | `<pendente>` |

**Onde deleguei e me arrependi:** `<preencher>`

**Onde não deleguei e deveria ter delegado:** `<preencher>`

**Usei subagentes / skills / MCP / hooks?** Não neste projeto — o fluxo foi
conduzido inteiramente na sessão principal do agente, com decisões de
ambiguidade coletadas via prompts estruturados de escolha (uma pergunta por
ambiguidade, com opções e justificativa). `<complementar se usou algo além
disso>`

---

## Descrição

*Como você transformou requisito ambíguo em requisito verificável.*

**Exemplo: AMB-008 — categorias fora da lista oficial (`coworking`).**

**Primeira proposta (minha, como agente):** comparar a categoria pelo rótulo
literal, normalizado só por caixa — qualquer rótulo que não fosse
`alimentacao`, `transporte_urbano` ou `hospedagem` seria recusado, sem
nenhuma inferência de significado. `coworking` ficaria recusado por não
constar na lista.

**Pergunta que forçou a revisão:** o humano perguntou explicitamente se duas
situações diferentes (uma corrida de transporte urbano reconhecida
literalmente vs. uma categoria nova como "coworking") deveriam ser tratadas
da mesma forma. Isso expôs que "match literal" escondia uma decisão de
negócio real: tratar toda categoria fora da lista como irrecuperável, mesmo
quando ela representa claramente a mesma natureza de gasto que uma categoria
oficial.

**Decisão final (`spec.md`, AMB-008/AMB-008b):** mapear por analogia quando a
natureza do gasto é equivalente; `coworking` é tratado como `hospedagem`
(espaço de trabalho temporário, mesma lógica de diária) e segue o limite de
R$250,00/diária. Qualquer categoria sem analogia razoável continua recusada.

**O que estava ambíguo:** se "categoria fora da política" deveria ser lida
estritamente pelo texto do rótulo ou pela natureza econômica do gasto.

**Como percebi:** não fui eu (o agente) que percebi — foi uma pergunta do
humano que expôs a lacuna antes da decisão ser fixada na spec. Isso é
evidência de que a primeira proposta do agente era defensável mas
incompleta, e só não entrou na spec porque houve revisão antes da escrita.

**Commit onde a decisão final foi registrada:** `18415e5`
(`docs(spec): define regras de negocio e resolve ambiguidades da politica de
reembolso`), seção `AMB-008`/`AMB-008b` de `specs/001-motor-reembolso/spec.md`.

---

## Discernimento

*Onde o Claude errou e você pegou.*

> **Sem um caso concreto e verificável, esta seção vale zero.** Não existe projeto
> de dois dias em que o modelo acertou tudo. A ausência do caso não prova que o
> modelo foi perfeito — prova que ninguém estava conferindo.

### Caso 1 — spec/plan/tasks duplicados e conflitantes após retomada de sessão

**O que ele propôs:** depois de uma interrupção de sessão (duas chamadas de
ferramenta encerradas sem confirmação, visíveis no histórico como "Tool
execution was interrupted before producing a result"), o agente **reescreveu
do zero** `spec.md`, `plan.md` e `tasks.md` (commits `3258d3c`, `7795273`,
`2452759`), com uma estrutura de regras diferente da já escrita e já
implementada em commits anteriores (`18415e5`, `7c72dc7`, `a259fdb` — por
exemplo, a versão nova fundia em `RN-001`/`RN-002` o que a versão antiga
corretamente separava em `RN-009`/`RN-011`/`RN-012`), sem perceber que já
existia uma spec aprovada e uma implementação completa (T-001 a T-013, 37
testes passando) alinhada à versão antiga.

**Por que estava errado:** criar uma segunda spec com numeração de regra
incompatível, sobre uma base de código que seguia a numeração antiga, teria
deixado o repositório com `spec.md` e `src/motor_reembolso/` descrevendo duas
realidades diferentes — exatamente o tipo de inconsistência que a rubrica do
desafio pune (`spec.md` que "descreve o código que já existia" ou, neste
caso, o inverso: código que não corresponde mais à spec vigente).

**Como eu detectei:** ao retomar a tarefa de implementação, um `git log` e
`git status` de rotina (antes de criar os módulos Python) mostrou "ahead of
origin by 20 commits" — número incompatível com os 4 commits que eu esperava
ter feito até aquele ponto. Isso disparou uma investigação com `git show` nos
dois commits de spec (`18415e5` vs `3258d3c`) para comparar o conteúdo linha
a linha.

**O que eu fiz:** confirmei que as decisões de ambiguidade eram, no mérito,
as mesmas (ambas refletiam a conversa real com o usuário), mas a estrutura
textual e a numeração de regras eram incompatíveis entre si e com o código já
implementado e testado. Descartei os três commits duplicados e sem
implementação correspondente (`git reset --hard` até o último commit
consistente, `fbad5f1`), preservando a spec que já tinha código e testes
construídos sobre ela, e segui a implementação a partir daí.

**Onde está a evidência:** `git log --oneline` deste repositório mostra a
sequência completa de commits, incluindo os três descartados (ainda
recuperáveis via `git reflog` se necessário) e o ponto de reconciliação em
`fbad5f1`. `docs/sessions/<arquivo-desta-sessão>` — `<completar após exportar
a sessão: o trecho onde o `git status` revelou "ahead by 20 commits">`.

### Caso 2 *(opcional)*

**Padrão que eu notei:** `<preencher — ex.: o agente tende a redigir
justificativas de spec plausíveis mesmo quando a decisão de negócio não foi
de fato tomada por um humano; vale conferir se isso se repetiu em algum outro
ponto>`

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação:** `<preencher — o que você, humano, de
fato fez: leu a spec gerada antes de aprovar? conferiu a saída do CLI contra
o JSON de exemplo manualmente?>`

**Li o diff inteiro em que porcentagem das entregas?** `<preencher
honestamente>`

**O que aceitei sem verificar direito, e o que me custou:** `<preencher>`

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
Os testes foram escritos pelo mesmo agente que escreveu o código (`motor.py`,
`relatorio.py`, `cli.py`), o que é o cenário de risco citado no próprio
template: teste escrito por quem escreveu o código tende a confirmar o
comportamento implementado, não o comportamento correto. Mitigação aplicada:
os nomes dos testes referenciam o ID da regra da spec (`test_rn_00X_*`,
`test_amb_00X_*`) e o "Aceite" de cada `RN-00X`/caso de borda em `spec.md` foi
escrito **antes** do código (sequência de commits `docs(spec)` →
`docs(plan)` → `docs(tasks)` → `feat(T-00X)`), então o teste tem uma
referência externa ao código para ser cobrado contra. `<preencher: você
revisou pessoalmente se os testes verificam valores corretos, ou confiou na
leitura cruzada com a spec?>`

---

## O envelope

*A mudança de requisito do Dia 2.*

**Status:** envelope ainda não recebido. Esta seção fica pendente até a
mudança de requisito chegar (ver `specs/001-motor-reembolso/tasks.md` Fase 5
e `DECISIONS.md`, que já estão preparados para receber as novas entradas).

**Quantos arquivos toquei na mão:** `<preencher>`
**Quanto tempo levou:** `<preencher>`
**Diff de absorção:** `<n> arquivos, +<n>/-<n> linhas` (`git diff <hash-antes> HEAD --stat`)

**Absorveu de graça:** `<preencher — a arquitetura em pipeline sequencial de
funções puras (plan.md, DT-002/DT-003) foi desenhada justamente para isolar
regra de negócio de I/O; avaliar aqui se isso se confirmou na prática>`

**Resistiu:** `<preencher>`

**Ordem em que fiz:** `<preencher — spec → DECISIONS → tasks → código é a
ordem esperada pelo CLAUDE.md deste projeto; a correção vê os timestamps dos
commits de qualquer forma>`

**Se eu tivesse escrito a spec original sabendo desta mudança:** `<preencher>`

**O que a spec me poupou, em concreto:** `<preencher>`

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** `<preencher>`

**Para qual não valeria?** `<preencher>`

**O que eu faria diferente:** `<preencher>`

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
`<preencher>`
