import datetime
from collections import defaultdict

from django.db.models import Prefetch
from rest_framework.pagination import PageNumberPagination

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.escola.models import Aluno
from src.kit_lanche.models import (
    KitLanche,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
)
from src.perfil.models import Usuario
from src.terceirizada.models import Contrato, VigenciaContrato


def date_to_string(date: datetime.date) -> str:
    assert isinstance(date, datetime.date), "date precisa ser `datetime.date`"  # nosec
    return date.strftime(FORMATO_DATA_BRASILEIRO)


def string_to_date(date_string: str) -> datetime.date:
    assert isinstance(date_string, str), "date_string precisa ser `string`"  # nosec
    return datetime.datetime.strptime(date_string, FORMATO_DATA_BRASILEIRO).date()


class KitLanchePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def cancela_solicitacao_kit_lanche_unificada(
    solicitacao_unificada, usuario, justificativa
):
    if not solicitacao_unificada.escolas_quantidades.filter(cancelado=False):
        solicitacao_unificada.cancelar_pedido(user=usuario, justificativa=justificativa)


SELECT_RELATED_SIMILAR_PASSEIO = (
    "solicitacao_kit_lanche",
    "escola",
    "escola__tipo_unidade",
    "escola__lote",
    "escola__lote__terceirizada",
    "escola__lote__tipo_gestao",
    "escola__tipo_gestao",
    "escola__diretoria_regional",
)

_PREFETCH_KITS = Prefetch(
    "solicitacao_kit_lanche__kits",
    queryset=KitLanche.objects.select_related("edital").prefetch_related(
        "tipos_unidades"
    ),
)


def _prefetch_contratos(prefixo):
    return [
        f"{prefixo}__contatos",
        Prefetch(
            f"{prefixo}__contratos",
            queryset=Contrato.objects.select_related(
                "edital", "modalidade"
            ).prefetch_related(
                Prefetch(
                    "vigencias",
                    queryset=VigenciaContrato.objects.select_related("contrato"),
                )
            ),
        ),
    ]


def _prefetch_lote_escola(prefixo="escola"):
    return [
        *_prefetch_contratos(f"{prefixo}__lote__terceirizada"),
        Prefetch(
            f"{prefixo}__lote__contratos_do_lote",
            queryset=Contrato.objects.select_related("edital"),
        ),
    ]


_PREFETCH_ALUNOS = Prefetch(
    "alunos_com_dieta_especial_participantes",
    queryset=Aluno.objects.select_related(
        "escola__tipo_unidade",
        "escola__lote__diretoria_regional",
        "escola__lote__terceirizada",
        "escola__lote__tipo_gestao",
        "escola__tipo_gestao",
        "escola__diretoria_regional",
        "periodo_escolar",
    ).prefetch_related("responsaveis", *_prefetch_lote_escola("escola")),
)


def anexa_logs_prefetched(objetos):
    """Busca os logs de todos os objetos em uma unica query e anexa em cada instancia."""
    objetos = list(objetos)
    uuids = [obj.uuid for obj in objetos]
    if not uuids:
        return objetos
    logs = list(
        LogSolicitacoesUsuario.objects.filter(uuid_original__in=uuids).order_by(
            "criado_em"
        )
    )
    usuarios = Usuario.objects.in_bulk({log.usuario_id for log in logs})
    for log in logs:
        log.usuario = usuarios.get(log.usuario_id, log.usuario)
    logs_por_uuid = defaultdict(list)
    for log in logs:
        logs_por_uuid[log.uuid_original].append(log)
    for obj in objetos:
        obj._prefetched_logs = logs_por_uuid.get(obj.uuid, [])
    return objetos


def prepara_solicitacoes_listagem_similares(solicitacoes, model):
    """Anexa solicitacoes similares em lote para listagens enxutas (avulsa/CEI)."""
    solicitacoes = list(solicitacoes)
    escolas_ids = {s.escola_id for s in solicitacoes}
    if not escolas_ids:
        return solicitacoes
    eh_cei = model is SolicitacaoKitLancheCEIAvulsa
    select = SELECT_RELATED_SIMILAR_PASSEIO if eh_cei else ("solicitacao_kit_lanche",)
    prefetch = [_PREFETCH_KITS]
    if eh_cei:
        prefetch += [
            _PREFETCH_ALUNOS,
            "faixas_etarias__faixa_etaria",
            *_prefetch_lote_escola("escola"),
        ]
    else:
        prefetch.append("alunos_com_dieta_especial_participantes")
    pool = (
        model.objects.filter(escola_id__in=escolas_ids)
        .exclude(status=model.workflow_class.RASCUNHO)
        .select_related(*select)
        .prefetch_related(*prefetch)
    )
    pool = anexa_logs_prefetched(pool)
    por_chave = defaultdict(list)
    for obj in pool:
        chave = (
            obj.escola_id,
            obj.solicitacao_kit_lanche.data,
            obj.solicitacao_kit_lanche.tempo_passeio,
        )
        por_chave[chave].append(obj)
    for solicitacao in solicitacoes:
        chave = (
            solicitacao.escola_id,
            solicitacao.solicitacao_kit_lanche.data,
            solicitacao.solicitacao_kit_lanche.tempo_passeio,
        )
        solicitacao._prefetched_solicitacoes_similares = [
            c for c in por_chave.get(chave, []) if c.uuid != solicitacao.uuid
        ]
    return solicitacoes


def _cemei_similares_correspondem(candidato, solicitacao):
    if (
        candidato.tem_solicitacao_cei
        and solicitacao.tem_solicitacao_cei
        and candidato.solicitacao_cei.tempo_passeio
        != solicitacao.solicitacao_cei.tempo_passeio
    ):
        return False
    if (
        candidato.tem_solicitacao_emei
        and solicitacao.tem_solicitacao_emei
        and candidato.solicitacao_emei.tempo_passeio
        != solicitacao.solicitacao_emei.tempo_passeio
    ):
        return False
    return True


def prepara_solicitacoes_listagem_similares_cemei(solicitacoes):
    """Anexa solicitacoes similares em lote para a listagem enxuta de CEMEI."""
    solicitacoes = list(solicitacoes)
    escolas_ids = {s.escola_id for s in solicitacoes}
    if not escolas_ids:
        return solicitacoes
    pool = (
        SolicitacaoKitLancheCEMEI.objects.filter(escola_id__in=escolas_ids)
        .exclude(status=SolicitacaoKitLancheCEMEI.workflow_class.RASCUNHO)
        .select_related("solicitacao_cei", "solicitacao_emei")
        .prefetch_related(
            Prefetch(
                "solicitacao_cei__kits",
                queryset=KitLanche.objects.select_related("edital").prefetch_related(
                    "tipos_unidades"
                ),
            ),
            Prefetch(
                "solicitacao_emei__kits",
                queryset=KitLanche.objects.select_related("edital").prefetch_related(
                    "tipos_unidades"
                ),
            ),
            "solicitacao_cei__alunos_com_dieta_especial_participantes",
            "solicitacao_emei__alunos_com_dieta_especial_participantes",
            "solicitacao_cei__faixas_quantidades__faixa_etaria",
        )
    )
    pool = anexa_logs_prefetched(pool)
    por_chave = defaultdict(list)
    for obj in pool:
        por_chave[(obj.escola_id, obj.data)].append(obj)
    for solicitacao in solicitacoes:
        solicitacao._prefetched_solicitacoes_similares = [
            candidato
            for candidato in por_chave.get(
                (solicitacao.escola_id, solicitacao.data), []
            )
            if candidato.uuid != solicitacao.uuid
            and _cemei_similares_correspondem(candidato, solicitacao)
        ]
    return solicitacoes
