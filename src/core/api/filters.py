from src.core.models import DiretoriaRegional
from src.dados_comuns.constants import PayloadVariaveis
from src.terceirizada.models import Terceirizada


def instituicao_da_requisicao(request):
    if not request or not getattr(request.user, "is_authenticated", False):
        return None
    vinculo = getattr(request.user, "vinculo_atual", None)
    if not vinculo:
        return None
    return vinculo.instituicao


def dres_da_terceirizada(terceirizada):
    """DREs dos lotes da empresa com contrato vigente."""
    return DiretoriaRegional.objects.filter(
        lotes__terceirizada=terceirizada,
        lotes__contratos_do_lote__encerrado=False,
        lotes__contratos_do_lote__edital__uuid__in=terceirizada.editais,
    ).distinct()


def dres_no_escopo(usuario):
    """
    QuerySet de DREs que o usuário pode consultar.

    Retorna None quando o perfil não tem restrição institucional (CODAE e equivalentes).
    """
    instituicao = instituicao_da_requisicao_usuario(usuario)
    if isinstance(instituicao, DiretoriaRegional):
        return DiretoriaRegional.objects.filter(pk=instituicao.pk)
    if isinstance(instituicao, Terceirizada):
        return dres_da_terceirizada(instituicao)
    return None


def instituicao_da_requisicao_usuario(usuario):
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return None
    vinculo = getattr(usuario, "vinculo_atual", None)
    if not vinculo:
        return None
    return vinculo.instituicao


def filtrar_lotes_por_escopo(queryset, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(terceirizada=instituicao)
    return queryset


def uuids_de_lista(data, chave_lista, chave_simples):
    if not hasattr(data, "getlist"):
        return []
    uuids = data.getlist(chave_lista)
    if not uuids:
        uuids = data.getlist(chave_simples)
    return [uuid for uuid in uuids if uuid]


def restringir_uuids_de_dre(uuids, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, DiretoriaRegional):
        permitidos = {str(instituicao.uuid)}
        return [uuid for uuid in uuids if str(uuid) in permitidos]
    if isinstance(instituicao, Terceirizada):
        dres = dres_da_terceirizada(instituicao).values_list("uuid", flat=True)
        permitidos = {str(uuid) for uuid in dres}
        return [uuid for uuid in uuids if str(uuid) in permitidos]
    return uuids


def aplicar_escopo_escola_para_filtros(queryset, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(lote__terceirizada=instituicao)
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    return queryset


def _filtrar_uuid_in(queryset, data, chave, lookup):
    valores = data.getlist(chave) if hasattr(data, "getlist") else []
    if valores:
        return queryset.filter(**{lookup: valores})
    return queryset


def _excluir_uuid_in(queryset, data, chave, lookup):
    valores = data.getlist(chave) if hasattr(data, "getlist") else []
    if valores:
        return queryset.exclude(**{lookup: valores})
    return queryset


def aplicar_filtros_lista_escola(queryset, data):
    queryset = _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        "tipo_unidade__uuid__in",
    )
    queryset = _filtrar_uuid_in(
        queryset, data, PayloadVariaveis.LOTE_UUID.value, "lote__uuid__in"
    )
    queryset = _excluir_uuid_in(
        queryset,
        data,
        PayloadVariaveis.EXCLUIR_TIPO_UNIDADE_UUID.value,
        "tipo_unidade__uuid__in",
    )
    queryset = _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        "diretoria_regional__uuid__in",
    )
    return _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.SUBPREFEITURA_UUID.value,
        "subprefeitura__uuid__in",
    )
