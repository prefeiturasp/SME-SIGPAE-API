import logging
from celery import shared_task
from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.dieta_especial.tasks.utils.relatorio_recreio_nas_ferias import (
    gera_pdf_relatorio_recreio_nas_ferias,
    gera_dicionario_relatorio_recreio,
    conveter_dict_to_querydict,
)
from sme_sigpae_api.dieta_especial.utils import (
    filtra_relatorio_recreio_nas_ferias,
)

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_recreio_nas_ferias_async(user, nome_arquivo, params):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        query_dict_params = conveter_dict_to_querydict(params)
        solicitacoes = filtra_relatorio_recreio_nas_ferias(query_dict_params)
        dados = gera_dicionario_relatorio_recreio(solicitacoes)
        arquivo = gera_pdf_relatorio_recreio_nas_ferias(dados, user, query_dict_params.get("lote", None))
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
