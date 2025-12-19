import datetime
import logging

from django.db.models import Q
from celery import shared_task

from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    SolicitacaoDietaEspecial,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
)
from sme_sigpae_api.dieta_especial.tasks.utils.logs import (
    cria_logs_totais_cei_por_faixa_etaria,
    gera_logs_dietas_escolas_cei,
    gera_logs_dietas_escolas_comuns,
    gera_logs_dietas_recreio_ferias_escolas_comuns,
    gera_logs_dietas_recreio_ferias_escolas_cei,
    gera_logs_dietas_recreio_ferias_parte_sem_faixa_cemei,
)
from sme_sigpae_api.escola.models import Escola

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def gera_logs_dietas_especiais_diariamente():
    logger.info(
        "x-x-x-x Iniciando a geração de logs de dietas especiais autorizadas diaria x-x-x-x"
    )
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    dietas_autorizadas = SolicitacaoDietaEspecial.objects.filter(
        tipo_solicitacao__in=["COMUM", "ALTERACAO_UE", "ALUNO_NAO_MATRICULADO"],
        status__in=[
            SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            SolicitacaoDietaEspecial.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
        ],
        ativo=True,
    )
    logs_a_criar_escolas_comuns = []
    logs_a_criar_escolas_cei = []
    escolas = Escola.objects.filter(tipo_gestao__nome="TERC TOTAL")
    for index, escola in enumerate(escolas):
        msg = "x-x-x-x Logs de quantidade de dietas autorizadas para a escola"
        msg += f" {escola.nome} ({index + 1}/{(escolas).count()}) x-x-x-x"
        logger.info(msg)
        if escola.eh_cei:
            logs_escola = gera_logs_dietas_escolas_cei(
                escola, dietas_autorizadas, ontem
            )
            logs_escola = cria_logs_totais_cei_por_faixa_etaria(
                logs_escola, ontem, escola
            )
            logs_a_criar_escolas_cei += logs_escola
        elif escola.eh_cemei:
            logs_a_criar_escolas_comuns += gera_logs_dietas_escolas_comuns(
                escola, dietas_autorizadas, ontem
            )

            logs_escola = gera_logs_dietas_escolas_cei(
                escola, dietas_autorizadas, ontem
            )
            logs_escola = cria_logs_totais_cei_por_faixa_etaria(
                logs_escola, ontem, escola
            )
            logs_a_criar_escolas_cei += logs_escola
        else:
            logs_a_criar_escolas_comuns += gera_logs_dietas_escolas_comuns(
                escola, dietas_autorizadas, ontem
            )
    LogQuantidadeDietasAutorizadas.objects.bulk_create(logs_a_criar_escolas_comuns)
    LogQuantidadeDietasAutorizadasCEI.objects.bulk_create(logs_a_criar_escolas_cei)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def gera_logs_dietas_recreio_ferias_diariamente():
    logger.info(
        "x-x-x-x Iniciando a geração de logs de dietas autorizadas - Recreio nas Férias x-x-x-x"
    )

    hoje = datetime.date.today()

    # 1) Verifica se está em Janeiro ou Julho
    if hoje.month not in (1, 7):
        logger.info("Fora dos meses de janeiro/julho. Task não será executada.")
        return

    ontem = hoje - datetime.timedelta(days=1)

    # 2) Filtra dietas de Recreio nas Férias autorizadas
    dietas_recreio_ferias = SolicitacaoDietaEspecial.objects.filter(
        Q(
            tipo_solicitacao__in=["COMUM", "ALTERACAO_UE"],
            motivo_alteracao_ue__nome="Dieta Especial - Recreio nas Férias",
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )
        | Q(
            tipo_solicitacao="ALUNO_NAO_MATRICULADO",
            ativo=True,
            dieta_para_recreio_ferias=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )
    )

    # 3) Verifica se ontem está contido em alguma solicitação de Recreio nas Férias
    solicitacoes_validas_para_ontem = dietas_recreio_ferias.filter(
        data_inicio__lte=ontem,
        data_termino__gte=ontem,
    )

    if not solicitacoes_validas_para_ontem.exists():
        logger.info(
            f"Nenhuma solicitação de Recreio nas Férias válida para o dia {ontem}. "
            "Nenhum log será gerado."
        )
        return

    # 4) Busca escolas participantes (que têm solicitações válidas para ontem)
    escolas_participantes = (
        Escola.objects.filter(tipo_gestao__nome="TERC TOTAL")
        .filter(
            id__in=solicitacoes_validas_para_ontem.values_list(
                "escola_destino_id", flat=True
            ).distinct()
        )
        .distinct()
    )

    logs_a_criar_comuns = []
    logs_a_criar_cei = []

    for index, escola in enumerate(escolas_participantes):
        msg = (
            f"x-x-x-x Logs Recreio nas Férias para {escola.nome} "
            f"({index + 1}/{escolas_participantes.count()}) x-x-x-x"
        )
        logger.info(msg)

        dietas_escola = solicitacoes_validas_para_ontem.filter(escola_destino=escola)

        if escola.eh_cei:
            logs_cei = gera_logs_dietas_recreio_ferias_escolas_cei(
                escola, dietas_escola, ontem
            )
            logs_a_criar_cei += logs_cei

        elif escola.eh_cemei:
            logs_cei = gera_logs_dietas_recreio_ferias_escolas_cei(
                escola, dietas_escola, ontem
            )
            logs_a_criar_cei += logs_cei

            logs_comuns = gera_logs_dietas_recreio_ferias_parte_sem_faixa_cemei(
                escola, dietas_escola, ontem
            )
            logs_a_criar_comuns += logs_comuns

        else:
            logs_comuns = gera_logs_dietas_recreio_ferias_escolas_comuns(
                escola, dietas_escola, ontem
            )
            logs_a_criar_comuns += logs_comuns

    LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.bulk_create(
        logs_a_criar_comuns
    )
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI.objects.bulk_create(
        logs_a_criar_cei
    )

    logger.info(
        f"x-x-x-x Logs de Recreio nas Férias gerados com sucesso: "
        f"{len(logs_a_criar_comuns)} logs sem faixa etária, "
        f"{len(logs_a_criar_cei)} logs com faixa etária x-x-x-x"
    )
