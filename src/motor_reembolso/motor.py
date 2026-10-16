"""Motor de regras de negocio do calculo de reembolso.

Funcao pura: recebe despesas normalizadas e periodo, devolve resultados.
Nao faz I/O. Ver specs/001-motor-reembolso/plan.md secoes 2 e 5 (DT-002, DT-003).

A ordem das regras implementadas aqui segue a secao 8 da spec (v2.0,
atualizada pelo envelope do Dia 2 — Politica de Reembolso v4).
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from motor_reembolso import cambio, politica
from motor_reembolso.modelos import Despesa, ResultadoDespesa


def _quantizar(valor: Decimal) -> Decimal:
    """RN-011: arredondamento half-even a 2 casas decimais."""
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


_POLITICA_CC_PADRAO: politica.PoliticaCentroCusto | None = None


def _politica_cc_padrao() -> politica.PoliticaCentroCusto:
    """Politica padrao (v3) resolvida para um centro de custo generico,
    usada como default pelos testes/chamadas que nao informam uma tabela
    de politica externa — mantem RN-001 a RN-012 funcionando sem mudanca
    de assinatura para quem so testa o comportamento v3."""
    global _POLITICA_CC_PADRAO
    if _POLITICA_CC_PADRAO is None:
        _POLITICA_CC_PADRAO = politica.resolver_politica_centro_custo(
            politica.politica_padrao_embutida(), ""
        )
    return _POLITICA_CC_PADRAO


def _regra_valor_negativo(despesa: Despesa) -> ResultadoDespesa | None:
    """RN-010: estornos (valor negativo) sao ignorados, nao recusados."""
    if despesa.valor < 0:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="ignorado",
            motivos=["RN-010"],
            justificativa="Valor negativo (estorno); despesa ignorada no calculo.",
        )
    return None


def _normalizar_categoria(despesa: Despesa, categorias_disponiveis: set[str]) -> str | None:
    """RN-012: normaliza para minusculas. RN-009/RN-014: mapeia por
    analogia ou valida contra as categorias disponiveis para o centro de
    custo da despesa (que pode incluir `representacao`, ver AMB-014).

    Devolve a categoria oficial aplicavel, ou None se nao reconhecida/mapeavel.
    """
    categoria = despesa.categoria_original.strip().lower()
    if categoria in categorias_disponiveis:
        return categoria
    mapeada = politica.MAPEAMENTO_ANALOGIA.get(categoria)
    if mapeada is not None and mapeada in categorias_disponiveis:
        return mapeada
    return None


def _regra_categoria(
    despesa: Despesa, categorias_disponiveis: set[str] | None = None
) -> tuple[ResultadoDespesa | None, str | None]:
    """RN-009/RN-014: recusa categoria fora da politica (ou nao
    disponivel para o centro de custo da despesa) e sem mapeamento de
    analogia.

    Devolve (resultado_de_recusa_ou_None, categoria_normalizada_ou_None).
    """
    if categorias_disponiveis is None:
        categorias_disponiveis = _politica_cc_padrao().categorias_disponiveis

    categoria = _normalizar_categoria(despesa, categorias_disponiveis)
    if categoria is None:
        resultado = ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-009"],
            justificativa=(
                f"Categoria '{despesa.categoria_original}' fora da politica "
                "(ou nao disponivel para o centro de custo) e sem mapeamento "
                "por analogia; nao reembolsavel."
            ),
        )
        return resultado, None
    return None, categoria


def _regra_conversao_moeda(
    despesa: Despesa, tabela_cambio: cambio.TabelaCambio | None
) -> tuple[ResultadoDespesa | None, Decimal]:
    """RN-015: converte o valor para BRL pela taxa da data da despesa.

    AMB-015: se a moeda nao existir na tabela de cambio em nenhuma data
    (ou nenhuma tabela foi informada), a despesa nao e processada
    (`status: "nao_processado"`), mas o processamento das demais despesas
    continua. Devolve (resultado_nao_processado_ou_None, valor_em_brl).
    """
    if despesa.moeda == cambio.MOEDA_BASE:
        return None, despesa.valor

    if tabela_cambio is None:
        return (
            ResultadoDespesa(
                despesa=despesa,
                valor_reembolsado=Decimal("0.00"),
                status="nao_processado",
                motivos=["RN-015"],
                justificativa=(
                    f"Moeda '{despesa.moeda}' informada, mas nenhuma tabela de "
                    "cambio foi fornecida; item nao processado, requer "
                    "verificacao manual do RH."
                ),
            ),
            despesa.valor,
        )

    try:
        valor_brl = _quantizar(
            cambio.converter_para_brl(despesa.valor, despesa.moeda, despesa.data, tabela_cambio)
        )
    except cambio.MoedaSemCotacaoError:
        return (
            ResultadoDespesa(
                despesa=despesa,
                valor_reembolsado=Decimal("0.00"),
                status="nao_processado",
                motivos=["RN-015"],
                justificativa=(
                    f"Moeda '{despesa.moeda}' sem cotacao disponivel em "
                    "cambio.json; item nao processado, requer verificacao "
                    "manual do RH."
                ),
            ),
            despesa.valor,
        )

    return None, valor_brl


def _regra_periodo(despesa: Despesa, inicio: date, fim: date) -> ResultadoDespesa | None:
    """RN-007: recusa despesa com data fora do periodo de competencia."""
    if not (inicio <= despesa.data <= fim):
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-007"],
            justificativa=(
                f"Data {despesa.data.isoformat()} fora do periodo de "
                f"competencia {inicio.isoformat()} a {fim.isoformat()}."
            ),
        )
    return None


def _chave_duplicata(despesa: Despesa, categoria: str) -> tuple:
    return (despesa.data, categoria, despesa.valor, despesa.fornecedor)


def _regra_duplicata(
    despesa: Despesa, categoria: str, chaves_vistas: set[tuple]
) -> ResultadoDespesa | None:
    """RN-008: recusa despesa duplicada (mesma data+categoria+valor+fornecedor).

    Muta `chaves_vistas` registrando a chave da primeira ocorrencia (menor id,
    assumindo chamadas na ordem de lancamento) como valida.
    """
    chave = _chave_duplicata(despesa, categoria)
    if chave in chaves_vistas:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-008"],
            justificativa=(
                "Duplicata de despesa com mesma data, categoria, valor e "
                "fornecedor ja processada."
            ),
        )
    chaves_vistas.add(chave)
    return None


def _regra_nota_fiscal(
    despesa: Despesa, politica_cc: politica.PoliticaCentroCusto | None = None
) -> ResultadoDespesa | None:
    """RN-005: nota fiscal obrigatoria para valor estritamente > gatilho.

    AMB-003: fronteira exclusiva (valor exato nao exige nota).
    AMB-004: ausencia da nota exigida recusa o item integralmente.
    RN-013: o gatilho vem da politica resolvida (ex-constante fixa na v3).
    """
    politica_cc = politica_cc or _politica_cc_padrao()
    gatilho = politica_cc.gatilho_nota_fiscal
    if despesa.valor > gatilho and not despesa.tem_nota_fiscal:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-005"],
            justificativa=(
                f"Valor R$ {despesa.valor} acima de R$ {gatilho} "
                "exige nota fiscal, que nao foi informada."
            ),
        )
    return None


def _regra_hospedagem_zerada_cc(
    despesa: Despesa, categoria: str, politica_cc: politica.PoliticaCentroCusto | None = None
) -> ResultadoDespesa | None:
    """RN-016: hospedagem recusada por politica do centro de custo
    (limite 0.00 explicito), motivo proprio e distinto de AMB-010b — a
    recusa ocorre mesmo quando o numero de diarias e identificavel."""
    if categoria != politica.CATEGORIA_HOSPEDAGEM:
        return None
    politica_cc = politica_cc or _politica_cc_padrao()
    if politica_cc.limites.get(politica.CATEGORIA_HOSPEDAGEM, Decimal("0.00")) <= 0:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-016"],
            justificativa=(
                "Centro de custo nao reembolsa hospedagem (limite de "
                "politica R$ 0,00)."
            ),
        )
    return None


_PADRAO_DIARIAS = re.compile(r"(\d+)\s*(?:di[aá]rias?|noites?)", re.IGNORECASE)


def _extrair_numero_diarias(descricao: str) -> int | None:
    """AMB-010: extrai o numero de diarias/noites de um texto livre."""
    correspondencia = _PADRAO_DIARIAS.search(descricao)
    if correspondencia is None:
        return None
    return int(correspondencia.group(1))


def _regra_hospedagem(
    despesa: Despesa, categoria: str, politica_cc: politica.PoliticaCentroCusto | None = None
) -> ResultadoDespesa | None:
    """RN-003: limite de hospedagem por diaria.

    AMB-010: numero de diarias extraido da descricao; fallback de recusa
    quando nao identificavel. AMB-002: excedente e cortado no limite, nao
    recusa o item inteiro. RN-013: o limite por diaria vem da politica
    resolvida para o centro de custo da despesa.
    """
    if categoria != politica.CATEGORIA_HOSPEDAGEM:
        return None

    politica_cc = politica_cc or _politica_cc_padrao()
    limite_diaria = politica_cc.limites[politica.CATEGORIA_HOSPEDAGEM]

    numero_diarias = _extrair_numero_diarias(despesa.descricao)
    if numero_diarias is None or numero_diarias <= 0:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=Decimal("0.00"),
            status="recusado",
            motivos=["RN-003"],
            justificativa=(
                "Numero de diarias/noites nao identificavel na descricao; "
                "impossivel aplicar o limite por diaria com seguranca."
            ),
        )

    valor_por_diaria = _quantizar(despesa.valor / numero_diarias)
    limite_total = _quantizar(limite_diaria * numero_diarias)

    if valor_por_diaria > limite_diaria:
        return ResultadoDespesa(
            despesa=despesa,
            valor_reembolsado=limite_total,
            status="aprovado_parcial",
            motivos=["RN-003"],
            justificativa=(
                f"Valor por diaria R$ {valor_por_diaria} excede o limite de "
                f"R$ {limite_diaria}; reembolso cortado em "
                f"R$ {limite_total} ({numero_diarias} diaria(s))."
            ),
        )

    return ResultadoDespesa(
        despesa=despesa,
        valor_reembolsado=despesa.valor,
        status="aprovado",
        motivos=["RN-003"],
        justificativa=(
            f"Dentro do limite de R$ {limite_diaria}/diaria "
            f"({numero_diarias} diaria(s))."
        ),
    )


def _calcular_dias_viagem(despesas_categorizadas: list[tuple[Despesa, str | None]]) -> set[date]:
    """RN-006/AMB-005: datas em que ha hospedagem lancada contam como viagem."""
    return {
        despesa.data
        for despesa, categoria in despesas_categorizadas
        if categoria == politica.CATEGORIA_HOSPEDAGEM
    }


def _limite_diario(
    categoria: str,
    data: date,
    dias_viagem: set[date],
    politica_cc: politica.PoliticaCentroCusto | None = None,
) -> Decimal:
    """RN-001/RN-002/RN-014 com ampliacao de RN-006 quando a data e dia
    de viagem (exceto para categorias em CATEGORIAS_SEM_AMPLIACAO_VIAGEM,
    ver AMB-018)."""
    politica_cc = politica_cc or _politica_cc_padrao()
    categorias_com_limite = politica.CATEGORIAS_COM_LIMITE_DIARIO | {
        politica.CATEGORIA_REPRESENTACAO
    }
    if categoria not in categorias_com_limite:
        raise ValueError(f"categoria sem limite diario: {categoria}")

    limite = politica_cc.limites[categoria]
    if data in dias_viagem and categoria not in politica.CATEGORIAS_SEM_AMPLIACAO_VIAGEM:
        limite = _quantizar(limite * politica_cc.ampliacao_viagem)
    return limite


def _motivo_limite(categoria: str) -> str:
    if categoria == politica.CATEGORIA_ALIMENTACAO:
        return "RN-001"
    if categoria == politica.CATEGORIA_TRANSPORTE_URBANO:
        return "RN-002"
    if categoria == politica.CATEGORIA_REPRESENTACAO:
        return "RN-014"
    raise ValueError(f"categoria sem limite diario: {categoria}")


def _aplicar_limites_diarios(
    despesas_validas: list[tuple[Despesa, str]],
    dias_viagem: set[date],
    resolver_politica_cc=None,
) -> list[ResultadoDespesa]:
    """RN-001/RN-002/RN-004/RN-014: agrega por dia+categoria e corta
    sequencialmente.

    Recebe apenas despesas de categorias com limite diario (alimentacao,
    transporte_urbano e representacao quando disponivel); hospedagem e
    tratada por `_regra_hospedagem`. Processa na ordem recebida (ordem de
    lancamento), que e o eixo do corte sequencial definido na RN-004.
    """
    if resolver_politica_cc is None:
        resolver_politica_cc = lambda _cc: _politica_cc_padrao()

    restante_por_grupo: dict[tuple[date, str], Decimal] = {}
    resultados: list[ResultadoDespesa] = []

    for despesa, categoria in despesas_validas:
        politica_cc = resolver_politica_cc(despesa.centro_custo)
        chave_grupo = (despesa.data, categoria)
        limite_do_dia = _limite_diario(categoria, despesa.data, dias_viagem, politica_cc)
        if chave_grupo not in restante_por_grupo:
            restante_por_grupo[chave_grupo] = limite_do_dia
        restante = restante_por_grupo[chave_grupo]
        reembolso = _quantizar(min(despesa.valor, max(restante, Decimal("0.00"))))
        restante_por_grupo[chave_grupo] = restante - reembolso
        motivo = _motivo_limite(categoria)

        if reembolso == despesa.valor:
            status = "aprovado"
            justificativa = (
                f"Dentro do limite diario de R$ {limite_do_dia} para "
                f"{categoria} em {despesa.data.isoformat()}."
            )
        elif reembolso > 0:
            status = "aprovado_parcial"
            justificativa = (
                f"Soma de {categoria} do dia {despesa.data.isoformat()} excede "
                f"o limite diario de R$ {limite_do_dia}; corte sequencial por "
                f"ordem de lancamento, este item absorveu R$ {reembolso}."
            )
        else:
            status = "recusado"
            justificativa = (
                f"Limite diario de R$ {limite_do_dia} para {categoria} em "
                f"{despesa.data.isoformat()} ja foi esgotado por despesas "
                "anteriores do mesmo dia."
            )

        resultados.append(
            ResultadoDespesa(
                despesa=despesa,
                valor_reembolsado=reembolso,
                status=status,
                motivos=[motivo, "RN-004"],
                justificativa=justificativa,
            )
        )

    return resultados


def _aplicar_fila_aprovacao_manual(
    resultados: list[ResultadoDespesa],
) -> list[ResultadoDespesa]:
    """RN-017/AMB-020/AMB-021: substitui aprovado/aprovado_parcial por
    pendente quando o valor_reembolsado final excede o limite de
    aprovacao automatica. Nunca se aplica a despesa recusada, ignorada
    ou nao processada."""
    ajustados: list[ResultadoDespesa] = []
    for resultado in resultados:
        if (
            resultado.status in ("aprovado", "aprovado_parcial")
            and resultado.valor_reembolsado > politica.LIMITE_APROVACAO_MANUAL
        ):
            ajustados.append(
                replace(
                    resultado,
                    status="pendente",
                    motivos=[*resultado.motivos, "RN-017"],
                    justificativa=(
                        f"{resultado.justificativa} Valor acima de "
                        f"R$ {politica.LIMITE_APROVACAO_MANUAL}; aguardando "
                        "aprovacao do gestor."
                    ),
                )
            )
        else:
            ajustados.append(resultado)
    return ajustados


def calcular(
    despesas: list[Despesa],
    inicio: date,
    fim: date,
    tabela_politica: politica.TabelaPolitica | None = None,
    tabela_cambio: cambio.TabelaCambio | None = None,
) -> list[ResultadoDespesa]:
    """Orquestra o pipeline de regras na ordem da secao 8 da spec.

    Recebe despesas ja carregadas (modelos.Despesa) e o periodo de
    competencia; devolve um ResultadoDespesa por despesa, na mesma ordem
    de entrada. A primeira regra que recusa/encerra uma despesa interrompe
    a avaliacao das seguintes para aquela despesa (secao 8 da spec); so
    despesas que passam pelos filtros estruturais entram na agregacao de
    limite diario, e a fila de aprovacao manual (RN-017) e o ultimo passo,
    aplicado sobre o resultado final de cada despesa.

    `tabela_politica`/`tabela_cambio` sao opcionais: quando omitidas, usa-se
    a politica padrao embutida (equivalente a v3) e nenhuma despesa em
    moeda estrangeira e convertida (ver spec.md secao 10).
    """
    if tabela_politica is None:
        tabela_politica = politica.politica_padrao_embutida()

    cache_politica_cc: dict[str, politica.PoliticaCentroCusto] = {}

    def resolver_politica_cc(centro_custo: str) -> politica.PoliticaCentroCusto:
        if centro_custo not in cache_politica_cc:
            cache_politica_cc[centro_custo] = politica.resolver_politica_centro_custo(
                tabela_politica, centro_custo
            )
        return cache_politica_cc[centro_custo]

    resultados_por_id: dict[str, ResultadoDespesa] = {}
    validas: list[tuple[Despesa, str]] = []
    chaves_duplicata: set[tuple] = set()

    for despesa in despesas:
        resultado = _regra_valor_negativo(despesa)
        if resultado is not None:
            resultados_por_id[despesa.id] = resultado
            continue

        politica_cc = resolver_politica_cc(despesa.centro_custo)
        resultado_categoria, categoria = _regra_categoria(
            despesa, politica_cc.categorias_disponiveis
        )
        if resultado_categoria is not None:
            resultados_por_id[despesa.id] = resultado_categoria
            continue

        resultado_cambio, valor_brl = _regra_conversao_moeda(
            replace(despesa, categoria_normalizada=categoria), tabela_cambio
        )
        if resultado_cambio is not None:
            resultados_por_id[despesa.id] = resultado_cambio
            continue

        despesa_normalizada = replace(
            despesa, categoria_normalizada=categoria, valor=valor_brl
        )

        resultado = _regra_periodo(despesa_normalizada, inicio, fim)
        if resultado is not None:
            resultados_por_id[despesa.id] = resultado
            continue

        resultado = _regra_duplicata(despesa_normalizada, categoria, chaves_duplicata)
        if resultado is not None:
            resultados_por_id[despesa.id] = resultado
            continue

        resultado = _regra_nota_fiscal(despesa_normalizada, politica_cc)
        if resultado is not None:
            resultados_por_id[despesa.id] = resultado
            continue

        resultado = _regra_hospedagem_zerada_cc(despesa_normalizada, categoria, politica_cc)
        if resultado is not None:
            resultados_por_id[despesa.id] = resultado
            continue

        validas.append((despesa_normalizada, categoria))

    dias_viagem = _calcular_dias_viagem(validas)

    for despesa, categoria in validas:
        if categoria == politica.CATEGORIA_HOSPEDAGEM:
            politica_cc = resolver_politica_cc(despesa.centro_custo)
            resultados_por_id[despesa.id] = _regra_hospedagem(despesa, categoria, politica_cc)

    categorias_com_limite_diario = politica.CATEGORIAS_COM_LIMITE_DIARIO | {
        politica.CATEGORIA_REPRESENTACAO
    }
    com_limite_diario = [
        (d, c) for d, c in validas if c in categorias_com_limite_diario
    ]
    for resultado in _aplicar_limites_diarios(com_limite_diario, dias_viagem, resolver_politica_cc):
        resultados_por_id[resultado.despesa.id] = resultado

    resultados_ordenados = [resultados_por_id[despesa.id] for despesa in despesas]
    return _aplicar_fila_aprovacao_manual(resultados_ordenados)
