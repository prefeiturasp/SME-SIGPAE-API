import logging

from celery import shared_task

from src.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from src.imr.api.services import RelatorioNotificacaoService
from src.imr.models import FormularioSupervisao
from src.relatorios.relatorios import (
    exportar_relatorio_notificacao,
    relatorio_formulario_supervisao,
)
from src.relatorios.utils import PDFMergeService

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_formulario_supervisao_async(user, nome_arquivo, uuid):
    solicitacao = FormularioSupervisao.objects.get(uuid=uuid)
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        arquivo = relatorio_formulario_supervisao(solicitacao)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))
        logger.error(f"Erro: {e}")

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gerar_relatorio_notificacao_pdf_async(
    user, formulario_supervisao_uuid, nome_arquivo
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    formulario_supervisao = FormularioSupervisao.by_uuid(
        uuid=formulario_supervisao_uuid
    )

    central_download = gera_objeto_na_central_download(
        user=user,
        identificador=nome_arquivo,
    )

    try:
        merge_service = PDFMergeService()

        service = RelatorioNotificacaoService(formulario_supervisao)
        for categoria, template in service.categoria_template_map.items():
            dados_formatados = service.retornar_dados_formatados(categoria)
            if len(dados_formatados["respostas"]) > 0:
                relatorio = exportar_relatorio_notificacao(
                    data=dados_formatados,
                    filename=f"Relatório de Notificação - {categoria} - {formulario_supervisao.escola.nome}.pdf",
                    template_name=template,
                )

                merge_service.append_pdf(relatorio)
            else:
                logger.info(
                    f"x-x-x-x Não há respostas para a categoria {categoria}. Portanto, o relatório não será gerado. x-x-x-x"
                )

        relatorio_final = merge_service.merge_pdfs()

        atualiza_central_download(
            central_download,
            nome_arquivo,
            relatorio_final,
        )
        logger.info(
            f"x-x-x-x Finaliza com sucesso a geração do relatório {nome_arquivo} x-x-x-x"
        )
    except Exception as e:
        atualiza_central_download_com_erro(central_download, str(e))
        logger.info(
            f"x-x-x-x Exceção ao gerar relatório {nome_arquivo}. Consulte o erro na central de download. x-x-x-x"
        )
