import json
import logging

from celery import shared_task

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    convert_dict_to_querydict,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.dieta_especial.tasks.utils.relatorio_historico_logs import (
    gera_pdf_relatorio_historico_dieta_especial,
)
from sme_sigpae_api.dieta_especial.utils import (
    gera_dicionario_historico_dietas,
    gerar_filtros_relatorio_historico,
)

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_historico_dietas_especiais_async(user, nome_arquivo, data):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        data_json = json.loads(data)
        querydict_params = convert_dict_to_querydict(data_json)
        filtros, data_dieta = gerar_filtros_relatorio_historico(querydict_params)
        logs_dietas = gera_dicionario_historico_dietas(filtros)
        arquivo = gera_pdf_relatorio_historico_dieta_especial(
            logs_dietas, user, filtros
        )
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
