import datetime
import logging

from celery import shared_task

from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.dieta_especial.tasks.utils.logs import (
    cria_logs_totais_cei_por_faixa_etaria,
    gera_logs_dietas_escolas_cei,
    gera_logs_dietas_escolas_comuns,
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
