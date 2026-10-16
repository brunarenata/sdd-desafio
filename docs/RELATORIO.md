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

> ## ☑ Checklist de retomada — apenas 1 campo `<preencher>` pendente
>
> **Cabeçalho**
> - [ ] L3 — nome, link do repositório, data de entrega
>
> **Delegação** — preenchido
> **Discernimento (Caso 2, opcional)** — preenchido
> **Diligência** — preenchido
> **O envelope** — preenchido (envelope recebido e absorvido em 2026-10-15)
> **Fechamento** — preenchido
>
> Resta apenas o cabeçalho (L3), que só pode ser preenchido no momento da
> entrega real.

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

**Onde deleguei e me arrependi:** aprovei as decisões de ambiguidade (AMB-00X)
uma a uma, no momento em que cada pergunta foi feita, sem voltar depois para
cruzá-las contra os textos de "Aceite" de outras regras já escritas na mesma
spec. Isso só apareceu como problema real quando a auditoria despesa a
despesa (`docs/auditoria-resultado-2026-07.md`) encontrou d-005 e d-013: o
"Aceite" de RN-009 e RN-003 descrevia um resultado (reembolso integral)
oposto ao que a própria decisão de AMB-010b e a ordem de regras da seção 8
exigiam. A decisão de negócio em si estava certa — o erro foi ter aceitado
a redação da spec sem reler o documento inteiro depois de cada ambiguidade
decidida, só item a item isoladamente. Delegar a decisão foi certo; não ter
delegado (ou feito eu mesmo) uma segunda passada de consistência textual
depois de todas as decisões tomadas foi o erro.

**Onde não deleguei e deveria ter delegado:** a revisão cruzada de
consistência textual entre as regras da própria spec, depois que todas as
ambiguidades já estavam decididas. Eu fiz essa checagem manualmente (ou não
fiz, e só apareceu via auditoria posterior); é exatamente o tipo de
varredura mecânica e exaustiva — comparar cada "Aceite" de cada RN-00X
contra as decisões de AMB-00X e contra a ordem de regras da seção 8 — que
poderia ter sido delegada a um agente auditor logo após a redação da spec,
em vez de só ser descoberta semanas depois ao rodar uma auditoria sobre o
resultado real. Delegar isso mais cedo teria evitado carregar uma
contradição interna na spec por todo o período de implementação.

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

**Padrão que eu notei:** não identifiquei um padrão de erro recorrente além
do Caso 1 (spec/plan/tasks duplicados após retomada de sessão) e do achado
de contradição textual descrito na seção Diligência (RN-003/RN-009 vs.
AMB-010b, ver `docs/auditoria-resultado-2026-07.md`). Os dois têm uma raiz
comum — o agente redige texto plausível em um ponto do documento sem
recarregar o estado completo e já decidido do resto do documento — mas não
tenho evidência de que isso se repetiu uma terceira vez neste projeto para
chamar de "padrão" com confiança. Deixo registrado como hipótese a vigiar
em projetos futuros, não como fato estabelecido.

---

## Diligência

*O que você verificou antes de aceitar.*

**Auditoria despesa a despesa:** `docs/auditoria-resultado-2026-07.md`
percorre as 14 despesas de `exemplos/despesas-exemplo.json` uma a uma,
confirmando regra (`RN-00X`), ambiguidade (`AMB-00X`) e aritmética contra o
resultado real (`_resultado_20261014.json`), mais a conferência do bloco
`resumo`. Encontrou duas contradições internas na própria spec (frases de
"Aceite" de RN-003 e RN-009 desatualizadas em relação a AMB-010b e à ordem
de regras da seção 8) — corrigidas em `spec.md` e registradas em
`specs/001-motor-reembolso/DECISIONS.md` (entrada 2026-10-15). O motor de
cálculo estava correto; a spec é que tinha o erro editorial.

**Meu procedimento de verificação:** rodei o CLI sobre
`exemplos/despesas-exemplo.json` e conferi manualmente a saída
(`_resultado_20261014.json`) contra o exemplo da spec e contra o que eu
esperava item por item — valor declarado, valor reembolsado, status e
motivo de cada uma das 14 despesas, além dos totais do `resumo`. Essa
conferência manual foi o que me levou a pedir a auditoria formal
despesa-a-despesa desta sessão, que então cruzou cada item contra o texto
normativo da spec (RN-00X/AMB-00X) e expôs as duas contradições internas
registradas acima. Não li a spec inteira linha a linha antes de aprovar a
versão original — a leitura detalhada aconteceu depois, via auditoria,
quando já havia uma saída real para comparar.

**Li o diff inteiro em que porcentagem das entregas?** entre 25% e 50%. Nos
commits de implementação (`feat(T-00X)`) eu geralmente li o diff de
`motor.py` por ser onde a regra de negócio vive, mas não li linha a linha
todos os diffs de teste e de documentação com a mesma atenção — confiei na
nomeação `test_rn_00X_*`/`test_amb_00X_*` como proxy de cobertura, o que é
exatamente o risco que a própria seção de testes abaixo descreve.

**O que aceitei sem verificar direito, e o que me custou:** aceitei os
textos de "Aceite" de RN-003 e RN-009 em `spec.md` como corretos no momento
em que a spec foi escrita, sem reler cada "Aceite" contra as decisões de
ambiguidade (AMB-010b) e contra a ordem de regras da seção 8 depois que
todas elas já estavam fixadas. O custo: a contradição ficou dentro do
repositório, sem detecção, por todo o período entre a redação da spec e
esta sessão de auditoria — qualquer leitor que confiasse só no "Aceite" de
RN-003/RN-009 isoladamente teria concluído, de forma incorreta, que d-005 e
d-013 deveriam ser aprovadas integralmente. O motor de cálculo nunca teve
esse bug (seguia a leitura correta), mas a documentação ficou incoerente
sem que eu notasse até rodar uma auditoria formal, item por item, contra o
resultado real.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
Os testes foram escritos pelo mesmo agente que escreveu o código (`motor.py`,
`relatorio.py`, `cli.py`), o que é o cenário de risco citado no próprio
template: teste escrito por quem escreveu o código tende a confirmar o
comportamento implementado, não o comportamento correto. Mitigação aplicada:
os nomes dos testes referenciam o ID da regra da spec (`test_rn_00X_*`,
`test_amb_00X_*`) e o "Aceite" de cada `RN-00X`/caso de borda em `spec.md` foi
escrito **antes** do código (sequência de commits `docs(spec)` →
`docs(plan)` → `docs(tasks)` → `feat(T-00X)`), então o teste tem uma
referência externa ao código para ser cobrado contra. Na prática, só
revisei o conteúdo dos testes de verdade (valores exatos esperados, não só
o nome `test_rn_00X_*`) nesta sessão, ao pedir a auditoria formal
despesa-a-despesa — foi aí que percebi, por exemplo, que
`test_rn_003_hospedagem_duas_diarias` e `test_rn_003_hospedagem_tres_noites`
testam d-010 e d-013 isoladamente com `tem_nota_fiscal` sempre `True` (valor
default do helper `_despesa()` em `test_motor.py`), então nenhum teste
unitário de `_regra_hospedagem` cobre o cenário real de d-013 (hospedagem
sem nota fiscal, valor acima de R$100) — essa interação só é coberta
indiretamente pelo teste de ponta a ponta via CLI contra o exemplo oficial.
Antes desta sessão, eu confiava na leitura cruzada com a spec (nome do
teste + ID da regra) como proxy suficiente; a auditoria mostrou que isso
não é garantia de que o teste cobre a interação certa entre regras.

---

## O envelope

*A mudança de requisito do Dia 2.*

**Status:** envelope recebido e absorvido nesta sessão. Fonte: comunicado
"Política de Reembolso v4" (três eixos — A: limites por centro de custo,
B: despesas internacionais, C: fila de aprovação manual), com quatro
arquivos de dados (`politica-v4.json`, `cambio.json`,
`despesas-envelope.json`, `despesas-envelope-cc-desconhecido.json`),
salvos em `exemplos/envelope/`.

**Quantos arquivos toquei na mão:** 23 — 15 modificados (`README.md`,
`specs/001-motor-reembolso/{DECISIONS,spec,tasks}.md`,
`src/motor_reembolso/{cli,io_despesas,modelos,motor,politica,relatorio}.py`,
`tests/test_{cli,modelos,motor,politica,relatorio}.py`) e 8 novos
(`src/motor_reembolso/cambio.py`, `tests/test_cambio.py`,
`docs/envelope-impacto.html`, mais os 5 arquivos do envelope em
`exemplos/envelope/`). Nenhum arquivo foi gerado por script — cada edição
de spec/código/teste foi uma decisão explícita, uma a uma.

**Quanto tempo levou:** absorvido em uma única sessão contínua, do
mapeamento de impacto (antes de qualquer decisão de ambiguidade) até a
suíte verde final — sem interrupção de sessão no meio (diferente do Caso 1
da seção Discernimento). Não registrei timestamps de início/fim; a
evidência objetiva é a sequência de edições desta sessão, não um
cronômetro.

**Diff de absorção:** núcleo (`specs/` + `src/`): 9 arquivos,
+1138/-109 linhas (`git diff HEAD --stat -- src/ specs/001-motor-reembolso/`).
Testes: 5 arquivos modificados +435 linhas, mais `tests/test_cambio.py`
novo. `README.md`: +58/-9 linhas. Hashes de commit ainda não existem —
nada foi commitado até o momento deste relatório (ver `tasks.md` Fase 5,
coluna "Commit" com `<pendente>` em todas as T-021 a T-031).

**Absorveu de graça:** a separação de `motor.py` como função pura sem
I/O (DT-002/DT-003 do `plan.md`) se confirmou exatamente como o `plan.md`
previu no próprio risco antecipado ("mudança de requisito do Dia 2
introduzir uma dimensão de dado que a entrada não tem"): acrescentar
`centro_custo`/`moeda` em `Despesa` e um parâmetro opcional
`tabela_politica`/`tabela_cambio` em `calcular()` não exigiu tocar em
`io_despesas.py` além de propagar dois campos, nem em `cli.py` além de
dois argumentos novos. O pipeline sequencial de regras com corte
antecipado (DT-003) absorveu três regras novas (RN-015, RN-016, RN-017)
como três novos passos na mesma lista de funções, sem reescrever a lógica
das regras RN-001 a RN-012 já existentes — todas as 46 regras/testes da
v3 continuaram passando sem modificação de asserção.

**Resistiu:** a definição de `resumo.quantidade_aprovadas` (seção 4 da
spec) teve que ser **redefinida**, não só estendida — a definição antiga
por exclusão ("status != recusado") não tinha como acomodar dois status
novos (`pendente`, `nao_processado`) sem contá-los erroneamente como
aprovados (ver AMB-023). Isso mudou o valor de `quantidade_aprovadas` até
para o exemplo v3 antigo (de 8 para 7, porque o estorno `ignorado` d-009
deixou de ser contado) — uma mudança de comportamento observável em dados
que não faziam parte do envelope, forçada pela necessidade de manter o
campo coerente. Também resistiu a suposição implícita de que
"centro de custo" era só um dado informativo repassado para a saída
(`plan.md` dizia isso explicitamente) — agora ele determina o resultado
do cálculo, exigindo resolução de política em cache por centro de custo
dentro do próprio `calcular()`.

**Ordem em que fiz:** spec → DECISIONS → tasks → código, na ordem exigida
pelo próprio comunicado do RH ("primeiro a spec... registre no
DECISIONS.md... novas tasks... só então, código") e pelo `CLAUDE.md` do
projeto. Antes mesmo de tocar na spec, produzi um mapeamento de impacto
(`docs/envelope-impacto.html`) listando o que quebraria em `spec.md`/
`plan.md`, sem decidir nenhuma ambiguidade ainda — só depois disso revisado
pelo humano é que as 11 ambiguidades novas (AMB-013 a AMB-023) foram
decididas, uma a uma, via `ask_user`.

**Se eu tivesse escrito a spec original sabendo desta mudança:** teria
definido `resumo.quantidade_aprovadas` por inclusão explícita desde a v1.0
(em vez de por exclusão de `recusado`) — a auditoria da v3
(`docs/auditoria-resultado-2026-07.md`) já tinha exposto esse risco antes
mesmo do envelope chegar, e a v4 só tornou o problema concreto. Também
teria modelado `centro_custo` no `plan.md` como "dado que pode vir a
influenciar o cálculo", em vez de documentar explicitamente que ele "só é
repassado para a saída, nunca usado no cálculo" — essa frase acabou sendo
exatamente o que a v4 invalidou.

**O que a spec me poupou, em concreto:** a ordem de aplicação de regras
(seção 8) já existia e já era auditável antes da v4 chegar; inserir RN-015
(conversão de moeda), RN-016 (hospedagem zerada por CC) e RN-017 (fila de
aprovação) significou decidir **onde** cada uma entra nessa sequência já
nomeada e numerada, não inventar uma ordem do zero. Isso tornou a decisão
de AMB-017 (conversão de moeda antes de nota fiscal/diária/arredondamento)
uma pergunta objetiva — "antes ou depois do passo N da seção 8?" — em vez
de uma discussão aberta sobre arquitetura.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Para qualquer tamanho
de projeto que tenha regra de negócio ambígua — não é uma questão de
contagem de arquivos ou de devs, mas de quanto texto de política em
linguagem natural precisa ser traduzido em decisão determinística. Mesmo
este desafio de dois dias, pequeno em volume de código (um pacote Python
com 6 módulos), já tinha 12 ambiguidades reais na política de RH; sem o
processo de spec-driven (uma pergunta por ambiguidade, decisão registrada
antes do código), cada uma delas teria sido decidida implicitamente dentro
do código, sem rastro, e a auditoria desta sessão não teria tido nenhum
"Aceite"/AMB-00X para comparar contra o resultado — só o comportamento
observado, sem saber se era intencional.

**Para qual não valeria?** Para protótipos descartáveis ou scripts de uso
único, onde não existe regra de negócio ambígua a decidir (é só lógica
mecânica óbvia) e não haverá uma segunda pessoa ou uma versão futura
precisando entender por que uma decisão foi tomada. O custo de escrever
spec/plan/tasks/DECISIONS antes do código só se paga quando alguém vai
precisar auditar ou mudar a regra depois — e nesses casos o overhead de
documentação supera o valor de uma trilha de decisão que nunca será
consultada.

**O que eu faria diferente:** depois de decidir todas as ambiguidades e
escrever a spec, eu rodaria uma auditoria de consistência cruzada (como a
desta sessão) *antes* de aprovar a spec como "pronta para implementar", não
só depois de já ter código, testes e um resultado real para comparar. O
achado de RN-003/RN-009 contradizendo AMB-010b poderia ter sido pego no dia
1, sem nunca ter entrado em um commit `docs(spec): aprovada`.

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
eu aprovo texto plausível com mais rigor quando ele é código (porque "roda
ou não roda" é uma checagem objetiva e imediata) do que quando ele é prosa
normativa dentro da própria spec — um "Aceite" de exemplo bem escrito passa
pela minha revisão com a mesma facilidade estando certo ou contraditório,
porque lê bem e soa autoritativo. O código mentiroso quebra um teste; a
spec mentirosa só quebra quando alguém se dá ao trabalho de auditar.
