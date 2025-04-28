from django.db.models import QuerySet
from rest_framework.request import Request

from sme_sigpae_api.dados_comuns.utils import (
    ordena_queryset_por_ultimo_log,
    remove_duplicados_do_query_set,
)
from sme_sigpae_api.produto.api.dashboard.utils import (
    filtra_produtos_da_terceirizada,
    filtra_reclamacoes_por_usuario,
    filtra_reclamacoes_questionamento_codae,
    filtrar_query_params,
    retorna_produtos_homologados,
    trata_parcialmente_homologados_ou_suspensos,
)
from sme_sigpae_api.produto.models import HomologacaoProduto


def produtos_homologados(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(eh_copia=False)
    query_set = filtrar_query_params(request, query_set)
    query_set = trata_parcialmente_homologados_ou_suspensos(
        request, query_set, vinculo_suspenso=False
    )
    query_set = retorna_produtos_homologados(query_set)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_nao_homologados(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(
        status__in=[
            HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO,
            HomologacaoProduto.workflow_class.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
            HomologacaoProduto.workflow_class.CODAE_AUTORIZOU_RECLAMACAO,
            HomologacaoProduto.workflow_class.CODAE_CANCELOU_ANALISE_SENSORIAL,
        ]
    )
    query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_suspensos(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.exclude(
        status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO
    )
    query_set = filtrar_query_params(request, query_set, filtra_por_edital=True)
    query_set = trata_parcialmente_homologados_ou_suspensos(
        request, query_set, vinculo_suspenso=True
    )
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_aguardando_analise_reclamacao(
    request: Request, query_set: QuerySet = None
) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(
        status__in=[
            HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
            HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_UE,
            HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            HomologacaoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
            HomologacaoProduto.workflow_class.UE_RESPONDEU_QUESTIONAMENTO,
            HomologacaoProduto.workflow_class.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        ]
    )
    query_set = filtrar_query_params(request, query_set)
    query_set = filtra_reclamacoes_por_usuario(request, query_set)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_pendente_homologacao(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(
        status=HomologacaoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO
    )
    query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_correcao_de_produto(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(
        status=HomologacaoProduto.workflow_class.CODAE_QUESTIONADO
    )
    query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
    query_set = filtra_produtos_da_terceirizada(request, query_set)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_aguardando_amostra_analise_sensorial(
    request: Request, query_set: QuerySet = None
) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(
        status=HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_SENSORIAL
    )
    query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
    query_set = filtra_produtos_da_terceirizada(request, query_set)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_questionamento_da_codae(
    request: Request, query_set: QuerySet = None
) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = filtrar_query_params(request, query_set)
    query_set = filtra_reclamacoes_questionamento_codae(request, query_set)
    lista = ordena_queryset_por_ultimo_log(query_set)
    lista = remove_duplicados_do_query_set(lista)
    return lista


def produtos_por_status(
    status: str, query_set: QuerySet[HomologacaoProduto] = None
) -> QuerySet:
    if not query_set:
        query_set = HomologacaoProduto.objects.all()
    query_set = query_set.filter(status=status.upper())
    return query_set
