from django.db.models import QuerySet
from rest_framework.request import Request

from sme_sigpae_api.dados_comuns.utils import (
    ordena_queryset_por_ultimo_log,
    remove_duplicados_do_query_set,
)
from sme_sigpae_api.produto.api.dashboard.utils import (
    filtrar_query_params,
    retorna_produtos_homologados,
    trata_parcialmente_homologados_ou_suspensos,
)
from sme_sigpae_api.produto.models import HomologacaoProduto


def produtos_homologados(request: Request, query_set: QuerySet = None) -> list:
    if not query_set:
        query_set = HomologacaoProduto.objects.filter(eh_copia=False)
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
