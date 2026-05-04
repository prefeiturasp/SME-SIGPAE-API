import datetime

from celery import shared_task

from src.escola.models import ESCOLA_TIPO_GESTAO_NOME, Escola
from src.medicao_inicial.historico_acesso_ue.models import (
    HistoricoAcessoMedicaoInicialUE,
)

USUARIO_SISTEMA_ID = 1
BULK_BATCH_SIZE = 1000


def _obter_escolas_elegiveis_para_historico():
    """Retorna as escolas elegiveis para gerar historico de acesso.

    Returns:
        QuerySet: Escolas ativas, com lote, acesso ao modulo de medicao
            inicial habilitado e tipo de gestao TERC TOTAL.
    """
    return Escola.objects.filter(
        ativo=True,
        lote__isnull=False,
        acesso_modulo_medicao_inicial=True,
        tipo_gestao__nome=ESCOLA_TIPO_GESTAO_NOME,
    ).select_related("lote")


def _obter_ids_escolas_com_historico_ativo_desde(data_referencia):
    """Retorna os ids de escolas com historico aberto desde a data informada.

    Args:
        data_referencia: Data minima para o campo data_inicial do historico.

    Returns:
        set[int]: Conjunto com ids das escolas que ja possuem historico aberto.
    """
    return set(
        HistoricoAcessoMedicaoInicialUE.objects.filter(
            data_inicial__lte=data_referencia,
            data_final__isnull=True,
        ).values_list("escola_id", flat=True)
    )


def _obter_historicos_ativos_desde(data_referencia):
    """Retorna os historicos abertos desde a data informada.

    Args:
        data_referencia: Data minima para o campo data_inicial do historico.

    Returns:
        QuerySet: Historicos abertos com escola e lotes carregados.
    """
    return HistoricoAcessoMedicaoInicialUE.objects.filter(
        data_inicial__lte=data_referencia,
        data_final__isnull=True,
    ).select_related("escola", "lote", "escola__lote")


@shared_task
def cria_historico_acesso_ue():
    """Cria historicos de acesso para escolas elegiveis sem registro aberto.

    Returns:
        int: Quantidade de historicos criados.
    """
    hoje = datetime.date.today()
    escolas = _obter_escolas_elegiveis_para_historico()
    escolas_com_historico = _obter_ids_escolas_com_historico_ativo_desde(hoje)

    historicos_para_criar = [
        HistoricoAcessoMedicaoInicialUE(
            escola=escola,
            lote=escola.lote,
            data_inicial=hoje,
            criado_por_id=USUARIO_SISTEMA_ID,
        )
        for escola in escolas
        if escola.id not in escolas_com_historico
    ]

    if not historicos_para_criar:
        return 0

    HistoricoAcessoMedicaoInicialUE.objects.bulk_create(
        historicos_para_criar,
        batch_size=BULK_BATCH_SIZE,
    )
    return len(historicos_para_criar)


@shared_task
def finaliza_historico_acesso_ue():
    """Inativa historicos abertos quando o lote atual da escola mudou.

    Returns:
        int: Quantidade de historicos atualizados.
    """
    hoje = datetime.date.today()
    historicos = _obter_historicos_ativos_desde(hoje)

    historicos_para_atualizar = []
    for historico in historicos:
        if historico.escola.lote_id != historico.lote_id:
            historico.data_final = hoje
            historicos_para_atualizar.append(historico)

    if not historicos_para_atualizar:
        return 0

    HistoricoAcessoMedicaoInicialUE.objects.bulk_update(
        historicos_para_atualizar,
        ["data_final"],
        batch_size=BULK_BATCH_SIZE,
    )
    return len(historicos_para_atualizar)
