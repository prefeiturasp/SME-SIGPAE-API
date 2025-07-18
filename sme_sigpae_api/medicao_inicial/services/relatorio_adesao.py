from datetime import datetime
from typing import List

from django.core.exceptions import ValidationError
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
    medicao: Medicao, tipos_alimentacao: List[str], data_inicio, data_fim
):
    queryset = ValorMedicao.objects.select_related("tipo_alimentacao").filter(
        medicao=medicao
    )

    if data_inicio and data_fim:
        queryset = queryset.filter(dia__gte=data_inicio, dia__lte=data_fim)

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
    data_inicio,
    data_fim,
):
    medicao_nome = medicao.nome_periodo_grupo.upper()

    if resultados.get(medicao_nome) is None:
        resultados[medicao_nome] = {}
        total_frequencia_por_medicao[medicao_nome] = 0

    valores_medicao = _obtem_valores_medicao(
        medicao, tipos_alimentacao, data_inicio, data_fim
    )
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
        escola = escola.split("-")[0].strip()
        filtros["solicitacao_medicao_inicial__escola__codigo_eol"] = escola

    periodos_escolares = query_params.getlist("periodos_escolares[]")
    if periodos_escolares:
        filtros["periodo_escolar__uuid__in"] = periodos_escolares

    return filtros


def obtem_resultados(query_params: QueryDict):
    mes_ano = query_params.get("mes_ano")
    mes, ano = mes_ano.split("_")
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")

    data_inicio = None
    data_fim = None
    if periodo_lancamento_de and periodo_lancamento_ate:
        data_inicio = periodo_lancamento_de.split("/")[0]
        data_fim = periodo_lancamento_ate.split("/")[0]

    tipos_alimentacao = query_params.getlist("tipos_alimentacao[]")

    filtros = _cria_filtros(query_params)
    resultados = {}
    total_frequencia_por_medicao = {}

    medicoes = _obtem_medicoes(mes, ano, filtros)
    for medicao in medicoes:
        resultados = _soma_totais_por_medicao(
            resultados,
            total_frequencia_por_medicao,
            medicao,
            tipos_alimentacao,
            data_inicio,
            data_fim,
        )

    return resultados


def _valida_ano_mes(mes_ano):
    if not mes_ano:
        raise ValidationError("É necessário informar o mês/ano de referência")
    try:
        mes_referencia, ano_referencia = map(int, mes_ano.split("_"))
    except ValueError:
        raise ValidationError("mes_ano deve estar no formato MM_AAAA")

    return mes_referencia, ano_referencia


def valida_parametros_periodo_lancamento(query_params):

    mes_ano = query_params.get("mes_ano")
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")

    mes_referencia, ano_referencia = _valida_ano_mes(mes_ano)

    if (periodo_lancamento_de and not periodo_lancamento_ate) or (
        periodo_lancamento_ate and not periodo_lancamento_de
    ):
        raise ValidationError(
            "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos"
        )

    if periodo_lancamento_de and periodo_lancamento_ate:

        data_de = _parse_data(periodo_lancamento_de, "periodo_lancamento_de")
        data_ate = _parse_data(periodo_lancamento_ate, "periodo_lancamento_ate")

        if data_de > data_ate:
            raise ValidationError(
                "'periodo_lancamento_de' deve ser anterior a 'periodo_lancamento_ate'"
            )

        _validar_mes_ano_data(
            data_de, mes_referencia, ano_referencia, "periodo_lancamento_de"
        )
        _validar_mes_ano_data(
            data_ate, mes_referencia, ano_referencia, "periodo_lancamento_ate"
        )


def _parse_data(valor, campo):
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(
            f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
        )


def _validar_mes_ano_data(data, mes, ano, campo):
    if (data.month, data.year) != (mes, ano):
        raise ValidationError(
            f"O mês/ano de '{campo}' ({data.month:02}/{data.year}) não coincide com 'mes_ano' ({mes:02}_{ano})."
        )
