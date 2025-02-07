from collections import defaultdict

from django.db.models import CharField, F, Q, QuerySet
from django.db.models.functions import Cast, Substr
from rest_framework.request import Request

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.produto.models import HomologacaoProduto


def filtra_editais(
    request: Request, query_set: QuerySet[HomologacaoProduto]
) -> QuerySet[HomologacaoProduto]:
    if hasattr(request.user.vinculo_atual.instituicao, "editais"):
        query_set = query_set.filter(
            produto__vinculos__edital__uuid__in=request.user.vinculo_atual.instituicao.editais,
        )
    numero_edital = request.query_params.get("edital_produto")
    if numero_edital:
        query_set = query_set.filter(produto__vinculos__edital__numero=numero_edital)
    return query_set


def trata_parcialmente_homologados_ou_suspensos(
    request: Request, query_set: QuerySet[HomologacaoProduto], vinculo_suspenso: bool
) -> QuerySet[HomologacaoProduto]:
    numero_edital = request.query_params.get("edital_produto")
    if numero_edital:
        query_set = query_set.filter(
            produto__vinculos__suspenso=vinculo_suspenso,
            produto__vinculos__edital__numero=numero_edital,
        )
    if hasattr(request.user.vinculo_atual.instituicao, "editais"):
        query_set = query_set.filter(
            produto__vinculos__suspenso=vinculo_suspenso,
            produto__vinculos__edital__uuid__in=request.user.vinculo_atual.instituicao.editais,
        )
    return query_set


def filtrar_query_params(
    request: Request, query_set: QuerySet[HomologacaoProduto], filtra_por_edital=True
) -> QuerySet[HomologacaoProduto]:
    titulo = request.query_params.get("titulo_produto")
    marca = request.query_params.get("marca_produto")

    if titulo:
        query_set = query_set.annotate(
            id_amigavel=Substr(Cast(F("uuid"), output_field=CharField()), 1, 5)
        ).filter(Q(id_amigavel__icontains=titulo) | Q(produto__nome__icontains=titulo))
    if marca:
        query_set = query_set.filter(produto__marca__nome__icontains=marca)

    if filtra_por_edital:
        query_set = filtra_editais(request, query_set)
    return query_set


def retorna_produtos_homologados(
    query_set: QuerySet[HomologacaoProduto],
) -> QuerySet[HomologacaoProduto]:
    all_logs = LogSolicitacoesUsuario.objects.filter(
        uuid_original__in=query_set.values_list("uuid", flat=True)
    ).order_by("-criado_em")

    logs_by_uuid = defaultdict(list)
    for log in all_logs:
        logs_by_uuid[log.uuid_original].append(log)

    def produto_homologado(obj):
        for log in logs_by_uuid.get(obj.uuid, []):
            if log.status_evento == LogSolicitacoesUsuario.CODAE_HOMOLOGADO:
                return True
            elif log.status_evento in [
                LogSolicitacoesUsuario.CODAE_SUSPENDEU,
                LogSolicitacoesUsuario.CODAE_NAO_HOMOLOGADO,
            ]:
                continue
        return False

    filtered_objects = [obj for obj in query_set if produto_homologado(obj)]
    query_set = query_set.filter(id__in=[obj.id for obj in filtered_objects])
    return query_set


def filtra_reclamacoes_por_usuario(
    request: Request, query_set: QuerySet[HomologacaoProduto]
) -> QuerySet[HomologacaoProduto]:
    filtros = {
        constants.TIPO_USUARIO_ESCOLA: {
            "reclamacoes__escola": request.user.vinculo_atual.instituicao
        },
        constants.TIPO_USUARIO_TERCEIRIZADA: {
            "reclamacoes__escola__lote__terceirizada": request.user.vinculo_atual.instituicao
        },
        constants.TIPO_USUARIO_DIRETORIA_REGIONAL: {
            "reclamacoes__escola__lote__diretoria_regional_id": request.user.vinculo_atual.instituicao
        },
    }
    filtros_kwargs = filtros.get(request.user.tipo_usuario, {})
    if filtros_kwargs:
        query_set = query_set.filter(**filtros_kwargs)
    return query_set


def filtra_reclamacoes_questionamento_codae(
    request: Request, query_set: QuerySet[HomologacaoProduto]
) -> QuerySet[HomologacaoProduto]:
    filtros = {
        constants.TIPO_USUARIO_ESCOLA: {
            "reclamacoes__escola": request.user.vinculo_atual.instituicao,
            "status": HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_UE,
        },
        constants.TIPO_USUARIO_TERCEIRIZADA: {
            "reclamacoes__escola__lote__terceirizada": request.user.vinculo_atual.instituicao,
            "status": HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
        },
        constants.TIPO_USUARIO_DIRETORIA_REGIONAL: {
            "reclamacoes__escola__lote__diretoria_regional": request.user.vinculo_atual.instituicao
        },
        constants.TIPO_USUARIO_NUTRISUPERVISOR: {
            "status": HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_NUTRISUPERVISOR
        },
    }
    filtros_kwargs = filtros.get(request.user.tipo_usuario, {})
    if filtros_kwargs:
        query_set = query_set.filter(**filtros_kwargs)
    if request.user.tipo_usuario not in [
        constants.TIPO_USUARIO_ESCOLA,
        constants.TIPO_USUARIO_TERCEIRIZADA,
        constants.TIPO_USUARIO_DIRETORIA_REGIONAL,
        constants.TIPO_USUARIO_NUTRISUPERVISOR,
    ]:
        query_set = query_set.filter(
            status__in=[
                HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_UE,
                HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
                HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            ]
        )

    return query_set


def filtra_produtos_da_terceirizada(
    request: Request, query_set: QuerySet[HomologacaoProduto]
) -> QuerySet[HomologacaoProduto]:
    filtros = {
        constants.TIPO_USUARIO_TERCEIRIZADA: {
            "rastro_terceirizada": request.user.vinculo_atual.instituicao
        },
    }
    filtros_kwargs = filtros.get(request.user.tipo_usuario, {})
    if filtros_kwargs:
        query_set = query_set.filter(**filtros_kwargs)
    return query_set
