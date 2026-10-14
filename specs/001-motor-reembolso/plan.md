# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.0

> Aqui mora o COMO. Este arquivo pode e deve falar de linguagem, biblioteca e
> arquitetura. O que ele **não** pode é introduzir regra de negócio nova — se
> apareceu uma, ela pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.11+ | Stdlib cobre tudo que o projeto precisa (JSON, decimal, datas, argparse); produtividade alta para 2 dias | Node/TypeScript: exigiria dependência externa para decimal preciso; Go: tipagem forte ajudaria, mas o overhead de boilerplate não compensa no prazo |
| Testes | `pytest` | Padrão de fato no ecossistema Python, fixtures simples, saída legível para rastreabilidade | `unittest` da stdlib: mais verboso, sem ganho real |
| Parsing/validação | `json` da stdlib + validação manual em funções puras | Entrada é pequena e fixa (ver `exemplos/despesas-exemplo.json`); schema completo (`pydantic`) seria peso desnecessário para 7 campos por despesa | `pydantic`/`jsonschema`: dependência extra sem benefício proporcional ao tamanho do projeto |
| Aritmética monetária | `decimal.Decimal` da stdlib | Elimina erro de ponto flutuante (ponto crítico, ver RN-011); suporta `ROUND_HALF_EVEN` nativamente via `quantize` | `float`: fonte de bug mais previsível em dinheiro, descartado por definição; `int` em centavos: funcionaria, mas exigiria conversão manual em toda entrada/saída sem ganho sobre `Decimal` |
| CLI | `argparse` da stdlib | Único comando (`calcular --input --output`), não justifica `click`/`typer` | `click`/`typer`: dependência externa para uma CLI de um comando só |

A linha de aritmética monetária não é decoração. Ponto flutuante em dinheiro é
a fonte de bug mais previsível deste projeto — todo valor monetário entra e
sai do núcleo de regras como `Decimal`, nunca como `float`.

## 2. Arquitetura

```
entrada JSON → loader/validador → normalização → motor de regras (puro) → serializador → saída JSON
                                                         ↑
                                                  política (constantes)
```

Módulos:

- **`io_despesas.py`** — lê o JSON de entrada, valida estrutura mínima (campos
  obrigatórios, tipos), converte valores para `Decimal`. Erros de entrada
  levantam exceção e interrompem a execução antes de qualquer cálculo.
- **`modelos.py`** — estruturas de dados internas (ver seção 3).
- **`politica.py`** — constantes da política (limites, percentuais) em um só
  lugar.
- **`motor.py`** — núcleo de regras de negócio puro: recebe a lista de
  despesas já normalizadas, aplica RN-001 a RN-012 na ordem da seção 8 da
  spec, devolve o resultado por despesa. Não faz I/O, não conhece JSON.
- **`relatorio.py`** — monta a estrutura de saída (resumo + lista de despesas)
  a partir do resultado do motor, serializa para JSON.
- **`cli.py`** — ponto de entrada: lê argumentos, orquestra
  `io_despesas → motor → relatorio`, escreve o arquivo de saída.

**Fronteiras:** o `motor.py` é o único módulo que decide reembolso — é
puramente funcional (entrada: lista de despesas normalizadas + período de
competência; saída: lista de resultados), sem tocar em arquivo, argumento de
linha de comando ou formato de JSON. Essa separação é o que permite trocar a
interface (CLI → API, por exemplo) ou absorver uma mudança de regra de
negócio sem tocar em parsing/serialização, e vice-versa.

## 3. Modelo de dados

```
Despesa (interna, pós-normalização):
  id: str
  data: date
  categoria_original: str
  categoria_normalizada: str | None   # None se não reconhecida/mapeável
  descricao: str
  fornecedor: str
  valor: Decimal                      # já quantizado a 2 casas
  tem_nota_fiscal: bool

ResultadoDespesa:
  despesa: Despesa
  valor_reembolsado: Decimal
  status: Literal["aprovado", "aprovado_parcial", "recusado", "ignorado"]
  motivos: list[str]                  # códigos RN-00X
  justificativa: str

ResultadoCalculo:
  colaborador: dict                   # repassado da entrada
  periodo: dict                       # repassado da entrada
  resultados: list[ResultadoDespesa]
  resumo: Resumo                      # totais agregados
```

`categoria_normalizada` carrega o resultado da RN-009/RN-012 (minúsculas +
mapeamento de analogia); quando `None`, a despesa é recusada antes de chegar
às regras de limite.

## 4. Como a política é representada

Os limites e percentuais vivem como constantes nomeadas em `politica.py`
(um único arquivo, sem configuração externa):

```python
LIMITE_ALIMENTACAO_DIA = Decimal("60.00")
LIMITE_TRANSPORTE_URBANO_DIA = Decimal("80.00")
LIMITE_HOSPEDAGEM_DIARIA = Decimal("250.00")
GATILHO_NOTA_FISCAL = Decimal("100.00")
AMPLIACAO_VIAGEM = Decimal("1.5")
CATEGORIAS_OFICIAIS = {"alimentacao", "transporte_urbano", "hospedagem"}
MAPEAMENTO_ANALOGIA = {"coworking": "hospedagem"}
```

Decisão deliberada: constantes em código, não arquivo de configuração externo
(YAML/JSON de política). Para duas categorias de política (limites e
mapeamento) em um projeto de 2 dias, um arquivo de config externo adicionaria
uma camada de parsing e validação sem usuário real para editá-lo sem
recompilar/redistribuir o projeto. Se a política mudar com frequência no
mundo real, esse é o primeiro ponto a extrair para configuração — e é por
isso que fica isolado em um único módulo, não espalhado pelo `motor.py`.

## 5. Decisões técnicas

### DT-001 — `Decimal` em vez de `float` para todo valor monetário

**Contexto:** a entrada tem um valor com 3 casas decimais (`33.333`); somas
repetidas em `float` acumulam erro de representação binária.
**Decisão:** todo valor monetário é convertido para `Decimal` no momento da
leitura (`io_despesas.py`) e permanece `Decimal` até a serialização final.
**Alternativa descartada:** `float` com `round()` ad-hoc em cada operação —
descartado porque o erro de arredondamento se manifestaria de forma
diferente dependendo da ordem das operações, quebrando o determinismo exigido
pelos critérios de aceite (seção 9 da spec).
**Consequência:** torna fácil garantir soma exata entre
`total_reembolsado + total_recusado = total_declarado`; torna um pouco mais
verboso o código de serialização (precisa converter `Decimal` → `str`/`float`
na saída JSON, já que `json` nativo não serializa `Decimal`).

### DT-002 — Motor de regras como função pura sem estado

**Contexto:** a mudança de requisito do Dia 2 é desconhecida; a arquitetura
precisa absorver regra nova sem reescrever I/O.
**Decisão:** `motor.py` expõe uma função `calcular(despesas: list[Despesa],
periodo: Periodo) -> list[ResultadoDespesa]` sem efeitos colaterais, sem
acesso a arquivo, sem estado global.
**Alternativa descartada:** uma classe `MotorReembolso` com estado
acumulado (ex.: um dicionário interno de "despesas já vistas por dia")
mutável entre chamadas — descartada porque criaria dependência de ordem de
chamada externa à função, dificultando testes isolados por regra.
**Consequência:** cada regra de negócio (RN-00X) é testável isoladamente
chamando `calcular` com uma lista pequena construída à mão; o custo é que
regras que dependem de agregação (RN-001, RN-002, RN-004, RN-006) precisam
primeiro agrupar despesas por data/categoria dentro da própria função, em
vez de usar estado incremental.

### DT-003 — Pipeline de regras sequencial com corte antecipado

**Contexto:** a seção 8 da spec define uma ordem fixa de regras, onde a
primeira recusa interrompe a avaliação das seguintes.
**Decisão:** cada despesa passa por uma sequência de funções de regra
(`_regra_valor_negativo`, `_regra_categoria`, `_regra_periodo`,
`_regra_duplicata`, `_regra_nota_fiscal`), cada uma retornando `None` (passa)
ou um `ResultadoDespesa` de recusa (interrompe); só o que sobra entra na
etapa de agregação por limite diário.
**Alternativa descartada:** avaliar todas as regras sempre e escolher o
"motivo mais relevante" depois — descartada porque a spec exige que a
despesa recusada por motivo estrutural (ex.: fora do período) nunca ocupe
espaço no limite diário de outra despesa (seção 8 da spec); avaliar tudo e
decidir depois tornaria essa garantia difícil de verificar por leitura.
**Consequência:** fácil de testar regra a regra isoladamente; fácil de
inserir uma nova regra na cadeia (relevante para o envelope do Dia 2) desde
que se decida sua posição na ordem — exige decisão explícita de onde a nova
regra entra, o que é desejável (força registrar em `DECISIONS.md`).

## 6. Estratégia de testes

- **Nível:** majoritariamente unitário, um arquivo de teste por módulo
  (`test_motor.py`, `test_io_despesas.py`, `test_relatorio.py`), mais um
  teste de integração (`test_cli.py`) que roda a CLI de ponta a ponta contra
  `exemplos/despesas-exemplo.json` e verifica o JSON de saída completo.
- **Cada `RN-NNN` da spec tem teste?** Sim — um teste nomeado
  `test_rn_00X_<resumo>` por regra, construindo o caso mínimo descrito no
  "Aceite" da própria regra na spec. A tabela de cobertura em `tasks.md`
  rastreia essa correspondência.
- **Casos de borda da seção 7 da spec:** cada linha da tabela de casos de
  borda tem um teste próprio nomeado `test_borda_<descricao>`, usando os
  mesmos ids de despesa do exemplo (`d-001`...`d-014`) sempre que possível,
  para que o teste funcione como documentação executável do exemplo oficial.
- **Nomenclatura:** `test_<rn|borda>_<id-ou-resumo>` — isso é o que fecha a
  rastreabilidade na correção: ao ler o nome do teste já se sabe qual
  requisito da spec ele verifica, sem abrir o corpo da função.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Mudança de requisito do Dia 2 introduzir uma dimensão de dado que a entrada não tem (ex.: campo de aprovação de gestor) | Média | Documentar em `DECISIONS.md`, estender `Despesa`/`modelos.py` com o campo opcional, adicionar regra nova ao final do pipeline da DT-003, nunca remover regra existente sem registrar o porquê |
| Padrão de texto de "N diárias/noites" na descrição não cobrir todos os casos reais do conjunto oculto do instrutor | Média | Fallback já é recusa documentada (RN-003, AMB-010); se o conjunto oculto expuser um padrão novo e razoável, é mudança de spec, não ajuste silencioso de regex |
| `Decimal` mal serializado no JSON de saída (ex.: aparecer como string em vez de número) | Baixa | Teste de integração (`test_cli.py`) valida o tipo de cada campo monetário na saída antes de considerar a task de serialização concluída |
