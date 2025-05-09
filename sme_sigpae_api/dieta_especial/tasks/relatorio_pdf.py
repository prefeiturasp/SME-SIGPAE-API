import logging

from celery import shared_task
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.dieta_especial.forms import RelatorioDietaForm
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.relatorios.relatorios import relatorio_geral_dieta_especial_pdf

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_dieta_especial_async(user, nome_arquivo, ids_dietas, data):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        form = RelatorioDietaForm(data)
        if not form.is_valid():
            raise ValidationError(form.errors)
        queryset = SolicitacaoDietaEspecial.objects.filter(id__in=ids_dietas)
        usuario = Usuario.objects.get(username=user)
        arquivo = relatorio_geral_dieta_especial_pdf(form, queryset, usuario)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
