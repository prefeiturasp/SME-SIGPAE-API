from typing import List

from django.http import QueryDict

from sme_sigpae_api.medicao_inicial.models import Medicao, ValorMedicao


def _obtem_medicoes(mes: str, ano: str, filtros: dict):
    return (
        Medicao.objects.select_related("periodo_escolar", "grupo")
        .filter(
            solicitacao_medicao_inicial__mes=mes,
            solicitacao_medicao_inicial__ano=ano,
            solicitacao_medicao_inicial__status="MEDICAO_APROVADA_PELA_CODAE",
            **filtros,
        )
        .exclude(
            solicitacao_medicao_inicial__escola__tipo_unidade__iniciais__in=[
                "CEI",
                "CEI DIRET",
                "CEI INDIR",
                "CEI CEU",
                "CCI",
                "CCI/CIPS",
                "CEU CEI",
                "CEU CEMEI",
                "CEMEI",
            ]
        )
    )


def _obtem_valores_medicao(
    medicao: Medicao,
    tipos_alimentacao: List[str],
):
    queryset = ValorMedicao.objects.select_related("tipo_alimentacao").filter(
        medicao=medicao
    )

    if tipos_alimentacao:
        queryset = queryset.filter(
            tipo_alimentacao__uuid__in=tipos_alimentacao
        ) | queryset.filter(nome_campo="frequencia")

    return queryset.exclude(categoria_medicao__nome__icontains="DIETA")


def _soma_total_servido_do_tipo_de_alimentacao(
    resultados, medicao_nome: str, valor_medicao: ValorMedicao
):
    tipo_alimentacao = valor_medicao.tipo_alimentacao

    if tipo_alimentacao is not None:
        tipo_alimentacao_nome = tipo_alimentacao.nome.upper()
        if resultados[medicao_nome].get(tipo_alimentacao_nome) is None:
            resultados[medicao_nome][tipo_alimentacao_nome] = {
                "total_servido": 0,
                "total_frequencia": 0,
                "total_adesao": 0,
            }

        resultados[medicao_nome][tipo_alimentacao_nome]["total_servido"] += int(
            valor_medicao.valor
        )

    return resultados


def _atualiza_total_frequencia_e_adesao_para_cada_tipo_de_alimentacao(
    resultados, medicao_nome: str, total_frequencia: int
):
    for tipo_alimentacao in resultados[medicao_nome].keys():
        tipo_alimentacao_totais = resultados[medicao_nome][tipo_alimentacao]
        tipo_alimentacao_totais["total_frequencia"] = total_frequencia
        try:
            tipo_alimentacao_totais["total_adesao"] = round(
                tipo_alimentacao_totais["total_servido"] / total_frequencia,
                4,
            )
        except ZeroDivisionError:
            tipo_alimentacao_totais["total_adesao"] = 0

    return resultados


def _soma_totais_por_medicao(
    resultados,
    total_frequencia_por_medicao,
    medicao: Medicao,
    tipos_alimentacao: List[str],
):
    medicao_nome = medicao.nome_periodo_grupo.upper()

    if resultados.get(medicao_nome) is None:
        resultados[medicao_nome] = {}
        total_frequencia_por_medicao[medicao_nome] = 0

    valores_medicao = _obtem_valores_medicao(medicao, tipos_alimentacao)
    for valor_medicao in valores_medicao:
        if valor_medicao.nome_campo == "frequencia":
            total_frequencia_por_medicao[medicao_nome] += int(valor_medicao.valor)
        else:
            resultados = _soma_total_servido_do_tipo_de_alimentacao(
                resultados, medicao_nome, valor_medicao
            )

    if not resultados[medicao_nome]:
        del resultados[medicao_nome]
    else:
        resultados = _atualiza_total_frequencia_e_adesao_para_cada_tipo_de_alimentacao(
            resultados, medicao_nome, total_frequencia_por_medicao[medicao_nome]
        )

    return resultados


def _cria_filtros(query_params: QueryDict):
    filtros = {}

    dre = query_params.get("diretoria_regional")
    if dre:
        filtros["solicitacao_medicao_inicial__escola__diretoria_regional__uuid"] = dre

    lotes = query_params.getlist("lotes[]")
    if lotes:
        filtros["solicitacao_medicao_inicial__escola__lote__uuid__in"] = lotes

    escola = query_params.get("escola")
    if escola:
        filtros["solicitacao_medicao_inicial__escola__uuid"] = escola

    periodos_escolares = query_params.getlist("periodos_escolares[]")
    if periodos_escolares:
        filtros["periodo_escolar__uuid__in"] = periodos_escolares

    return filtros


def obtem_resultados(mes: str, ano: str, query_params: QueryDict):
    tipos_alimentacao = query_params.getlist("tipos_alimentacao[]")

    filtros = _cria_filtros(query_params)
    resultados = {}
    total_frequencia_por_medicao = {}

    medicoes = _obtem_medicoes(mes, ano, filtros)
    for medicao in medicoes:
        resultados = _soma_totais_por_medicao(
            resultados, total_frequencia_por_medicao, medicao, tipos_alimentacao
        )

    return resultados
