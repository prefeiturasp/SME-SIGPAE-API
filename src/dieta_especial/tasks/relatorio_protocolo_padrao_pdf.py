import logging

from celery import shared_task
from django.template.loader import render_to_string

from src.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from src.dieta_especial.protocolo_padrao.models import ProtocoloPadraoDietaEspecial
from src.dieta_especial.protocolo_padrao.services.dados_protocolo_padrao import (
    preparar_dados_protocolo_padrao,
)
from src.relatorios.utils import html_to_pdf_file

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gerar_pdf_protocolo_padrao_async(user, nome_arquivo, params):
    logger.info("Iniciando a geração do arquivo %s.", nome_arquivo)
    registro_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        protocolo = ProtocoloPadraoDietaEspecial.objects.get(
            uuid=params["protocolo_uuid"],
            ativo=True,
        )
        dados = preparar_dados_protocolo_padrao(protocolo)
        html = render_to_string(
            "protocolo_padrao_dieta_especial.html",
            dados,
        )
        arquivo_pdf = html_to_pdf_file(
            html,
            nome_arquivo,
            is_async=True,
        )
        atualiza_central_download(registro_download, nome_arquivo, arquivo_pdf)
    except Exception as erro:
        logger.exception("Erro ao gerar o arquivo %s.", nome_arquivo)
        atualiza_central_download_com_erro(registro_download, str(erro))
    finally:
        logger.info("Encerrada a geração do arquivo %s.", nome_arquivo)
