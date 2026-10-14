---
name: calcular-reembolso
description: Use quando o usuario pedir para calcular, processar, rodar ou auditar o motor de reembolso sobre um arquivo JSON de despesas.
argument-hint: [caminho-do-json]
---

# Calcular e auditar reembolso

## Quando usar esta skill

Sempre que o usuario pedir para calcular reembolso de um arquivo de
despesas, ou quiser verificar/auditar se um calculo esta de acordo com a
spec e as ambiguidades decididas em
`specs/001-motor-reembolso/spec.md`.

## Como usar esta skill

1. Se o usuario informou um caminho de JSON (via `$ARGUMENTS` ou no texto da
   mensagem), use-o. Caso contrario, pergunte qual arquivo processar antes
   de continuar — nao assuma `exemplos/despesas-exemplo.json` por padrao.

2. Delegue para o subagente **`calculo-reembolso`** (tool `agent`), passando
   o caminho do arquivo de entrada. Peca explicitamente:
   - o caminho do arquivo de resultado gerado,
   - o JSON de resultado (ou resumo, se grande),
   - o resumo em linguagem natural (aprovadas/recusadas, totais, motivo por
     despesa nao integralmente aprovada).

3. Com a resposta do passo 2 em maos, delegue para o subagente
   **`auditor-ambiguidades`** (tool `agent`), repassando no prompt:
   - o caminho do arquivo de entrada original,
   - o caminho (ou conteudo) do arquivo de resultado gerado no passo 2,
   - pedindo o veredito estruturado completo (testes, cobertura spec->teste,
     cobertura ambiguidade->codigo, coerencia do resultado especifico).

4. Apresente ao usuario, nesta ordem:
   - O resumo do calculo (passo 2).
   - O veredito da auditoria (passo 3).
   - Se o veredito for `ATENCAO`, liste os pontos encontrados antes de
     qualquer outra coisa — isso e mais importante que o resultado numerico.

5. Nunca edite spec.md, codigo ou testes dentro desta skill sem o usuario
   pedir explicitamente depois de ver o veredito da auditoria.
