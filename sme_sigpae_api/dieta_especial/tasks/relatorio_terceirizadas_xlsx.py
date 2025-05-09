import io
import logging

from celery import shared_task

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.dieta_especial.api.serializers import (
    SolicitacaoDietaEspecialExportXLSXSerializer,
    SolicitacaoDietaEspecialNutriSupervisaoExportXLSXSerializer,
)
from sme_sigpae_api.dieta_especial.tasks.utils.relatorio_terceirizadas_xlsx import (
    build_xlsx_relatorio_terceirizadas,
)
from sme_sigpae_api.perfil.models import Usuario

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xlsx_relatorio_dietas_especiais_terceirizadas_async(
    user, nome_arquivo, ids_dietas, data, lotes, classificacoes, protocolos_padrao
):
    from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial

    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        query_set = SolicitacaoDietaEspecial.objects.filter(id__in=ids_dietas)
        usuario = Usuario.objects.get(username=user)
        solicitacoes = []
        for solicitacao in query_set:
            classificacao = (
                solicitacao.classificacao.nome if solicitacao.classificacao else "--"
            )
            dados_solicitacoes = {
                "codigo_eol_aluno": solicitacao.aluno.codigo_eol,
                "nome_aluno": solicitacao.aluno.nome,
                "nome_escola": solicitacao.escola.nome,
                "classificacao": classificacao,
                "protocolo_padrao": solicitacao.nome_protocolo,
                "alergias_intolerancias": solicitacao.alergias_intolerancias,
            }
            if data.get("status_selecionado") == "CANCELADAS":
                dados_solicitacoes["data_cancelamento"] = solicitacao.data_ultimo_log
            solicitacoes.append(dados_solicitacoes)
        exibir_diagnostico = usuario.tipo_usuario != "terceirizada"
        if exibir_diagnostico:
            serializer = SolicitacaoDietaEspecialNutriSupervisaoExportXLSXSerializer(
                query_set, context={"status": data.get("status_selecionado")}, many=True
            )
        else:
            serializer = SolicitacaoDietaEspecialExportXLSXSerializer(
                query_set, context={"status": data.get("status_selecionado")}, many=True
            )
        data_inicial = data.get("data_inicial", None)
        data_final = data.get("data_final", None)

        output = io.BytesIO()
        build_xlsx_relatorio_terceirizadas(
            output,
            serializer,
            query_set,
            data.get("status_selecionado"),
            lotes,
            classificacoes,
            protocolos_padrao,
            data_inicial,
            data_final,
            exibir_diagnostico,
        )
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
