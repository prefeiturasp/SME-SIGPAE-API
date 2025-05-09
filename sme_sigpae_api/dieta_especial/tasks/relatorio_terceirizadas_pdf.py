import datetime
import logging

from celery import shared_task

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    converte_numero_em_mes,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.relatorios.relatorios import relatorio_dietas_especiais_terceirizada

logger = logging.getLogger(__name__)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_dietas_especiais_terceirizadas_async(
    user, nome_arquivo, ids_dietas, data, filtros
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
        now = datetime.datetime.now()
        data_pt = f"{now.day} de {converte_numero_em_mes(now.month)} de {now.year}"
        dados = {
            "usuario_nome": usuario.nome,
            "status": data.get("status_selecionado").lower(),
            "filtros": filtros,
            "solicitacoes": solicitacoes,
            "quantidade_solicitacoes": query_set.count(),
            "diagnostico": exibir_diagnostico,
            "data_extracao": data_pt,
        }
        arquivo = relatorio_dietas_especiais_terceirizada(dados=dados)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
