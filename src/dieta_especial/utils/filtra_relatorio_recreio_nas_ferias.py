from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import QueryDict

from src.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)


def filtra_relatorio_recreio_nas_ferias(query_params: QueryDict) -> QuerySet:
    """
    Retorna um queryset unificado com alunos matriculados e não matriculados que atendem aos critérios do Recreio nas Férias.

    Args:
        query_params (QueryDict): Parâmetros de filtro da requisição.
    Returns:
        QuerySet: Conjunto de solicitações filtradas e ordenadas por escola de destino.
    """
    filtros = gera_filtros_relatorio_recreio_nas_ferias(query_params)
    padrao = filtros.get("padrao", {})
    matriculado = filtros.get("matriculado", {})
    nao_matriculado = filtros.get("nao_matriculado", {})

    status_permitidos = [
        SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        SolicitacaoDietaEspecial.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    ]

    filtro_matriculados = Q(
        status__in=status_permitidos,
        tipo_solicitacao="ALTERACAO_UE",
        motivo_alteracao_ue__nome__icontains="recreio",
        **padrao,
        **matriculado,
    )

    filtro_nao_matriculados = Q(
        status__in=status_permitidos,
        tipo_solicitacao__in=[
            SolicitacaoDietaEspecial.COMUM,
            SolicitacaoDietaEspecial.ALUNO_NAO_MATRICULADO,
        ],
        dieta_para_recreio_ferias=True,
        **padrao,
        **nao_matriculado,
    )

    queryset = SolicitacaoDietaEspecial.objects.filter(
        filtro_matriculados | filtro_nao_matriculados
    ).order_by("escola_destino__nome")

    return queryset


def gera_filtros_relatorio_recreio_nas_ferias(query_params: QueryDict) -> dict:
    """
    Gera os dicionários de filtros com base nos parâmetros da requisição.

    Args:
        query_params (QueryDict): Parâmetros enviados na requisição HTTP.
    Returns:
        dict:  Dicionário com filtros para padrao, matriculado e nao_matriculado.
    """
    filtros = {
        "padrao": {
            "escola_destino__lote__uuid": query_params.get("lote", None),
            "escola_destino__uuid__in": query_params.getlist(
                "unidades_educacionais_selecionadas", None
            ),
            "classificacao__id__in": query_params.getlist(
                "classificacoes_selecionadas", None
            ),
            "alergias_intolerancias__id__in": query_params.getlist(
                "alergias_intolerancias_selecionadas", None
            ),
        },
        "matriculado": {},
        "nao_matriculado": {},
    }

    data_inicio = query_params.get("data_inicio")
    data_fim = query_params.get("data_fim")

    if data_inicio:
        data_ini = _parse_data(data_inicio, "data_inicio")
        filtros["padrao"]["data_termino__gte"] = data_ini
    if data_fim:
        data_fim = _parse_data(data_fim, "data_fim")
        filtros["padrao"]["data_inicio__lte"] = data_fim

    filtros["padrao"] = {
        key: value
        for key, value in filtros["padrao"].items()
        if value not in [None, []]
    }
    return filtros


def _parse_data(valor: str, campo: str) -> datetime:
    """
    Converte string de data no formato 'dd/mm/yyyy' para objeto date
    Args:
        valor (str): string contendo a data.
        campo (str): nome do campo para mensagens de erro.
    Raises:
        ValidationError: se o formato da data for inválido.
    Returns:
        datetime:  objeto date convertido.
    """
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(
            f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
        )
