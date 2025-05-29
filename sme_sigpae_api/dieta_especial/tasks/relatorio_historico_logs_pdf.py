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
    build_titulo,
    formata_logs_para_titulo,
    gera_pdf_relatorio_historico_dieta_especial,
)
from sme_sigpae_api.dieta_especial.utils import (
    gera_dicionario_historico_dietas,
    gerar_filtros_relatorio_historico,
    get_logs_historico_dietas,
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

        logs_dietas_auxiliar = get_logs_historico_dietas(filtros, eh_exportacao=True)
        logs_dietas_formatados = formata_logs_para_titulo(logs_dietas_auxiliar)
        subtitulo_relatorio = build_titulo(
            logs_dietas_formatados, querydict_params, for_pdf=True
        )

        logs_dietas = gera_dicionario_historico_dietas(filtros)
        arquivo = gera_pdf_relatorio_historico_dieta_especial(
            logs_dietas, user, subtitulo_relatorio
        )
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
