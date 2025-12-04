import datetime
import logging
from io import BytesIO
from uuid import UUID

from celery import shared_task
from dateutil.relativedelta import relativedelta
from pypdf import PdfWriter

from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.medicao_inicial.services.ordenacao_unidades import ordenar_unidades
from sme_sigpae_api.medicao_inicial.services.relatorio_adesao_excel import (
    gera_relatorio_adesao_xlsx,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_adesao_pdf import (
    gera_relatorio_adesao_pdf,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    gera_relatorio_consolidado_xlsx,
)
from sme_sigpae_api.medicao_inicial.services.relatorio_controle_frequencia_pdf import (
    gera_relatorio_controle_frequencia_pdf,
)
from sme_sigpae_api.perfil.models.usuario import Usuario

from ..dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from ..escola.models import AlunoPeriodoParcial, Escola
from ..relatorios.relatorios import (
    obter_relatorio_da_unidade,
    relatorio_solicitacao_medicao_por_escola,
    relatorio_solicitacao_medicao_por_escola_cei,
    relatorio_solicitacao_medicao_por_escola_cemei,
    relatorio_solicitacao_medicao_por_escola_emebs,
)
from .models import Responsavel, SolicitacaoMedicaoInicial
from .utils import cria_relatorios_financeiros_por_grupo_unidade_escolar

logger = logging.getLogger(__name__)


# https://docs.celeryproject.org/en/latest/userguide/tasks.html
@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def cria_solicitacao_medicao_inicial_mes_atual():
    data_hoje = datetime.date.today()
    data_mes_anterior = data_hoje + relativedelta(months=-1)

    for escola in Escola.objects.all():
        if not solicitacao_medicao_atual_existe(escola, data_hoje):
            try:
                solicitacao_mes_anterior = buscar_solicitacao_mes_anterior(
                    escola, data_mes_anterior
                )
                solicitacao_atual = criar_nova_solicitacao(
                    solicitacao_mes_anterior, escola, data_hoje
                )
                copiar_responsaveis(solicitacao_mes_anterior, solicitacao_atual)

                if solicitacao_atual.ue_possui_alunos_periodo_parcial:
                    copiar_alunos_periodo_parcial(
                        solicitacao_mes_anterior, solicitacao_atual
                    )
                usuario_admin = Usuario.objects.get(email="system@admin.com")
                solicitacao_atual.inicia_fluxo(
                    user=usuario_admin
                )

            except SolicitacaoMedicaoInicial.DoesNotExist:
                message = (
                    "x-x-x-x Não existe Solicitação de Medição Inicial para a escola "
                    f"{escola.nome} no mês anterior ({data_mes_anterior.month:02d}/"
                    f"{data_mes_anterior.year}) x-x-x-x"
                )
                logger.info(message)


def solicitacao_medicao_atual_existe(escola, data):
    return SolicitacaoMedicaoInicial.objects.filter(
        escola=escola, ano=data.year, mes=f"{data.month:02d}"
    ).exists()


def buscar_solicitacao_mes_anterior(escola, data):
    return SolicitacaoMedicaoInicial.objects.get(
        escola=escola, ano=data.year, mes=f"{data.month:02d}"
    )


def criar_nova_solicitacao(solicitacao_anterior, escola, data_hoje):
    attrs = {
        "escola": escola,
        "ano": data_hoje.year,
        "mes": f"{data_hoje.month:02d}",
        "criado_por": solicitacao_anterior.criado_por,
        "ue_possui_alunos_periodo_parcial": solicitacao_anterior.ue_possui_alunos_periodo_parcial,
    }

    solicitacao_mes_atual = SolicitacaoMedicaoInicial.objects.create(**attrs)
    solicitacao_mes_atual.tipos_contagem_alimentacao.set(
        solicitacao_anterior.tipos_contagem_alimentacao.all()
    )
    solicitacao_mes_atual.save()
    return solicitacao_mes_atual


def copiar_responsaveis(solicitacao_origem, solicitacao_destino):
    for responsavel in solicitacao_origem.responsaveis.all():
        Responsavel.objects.create(
            solicitacao_medicao_inicial=solicitacao_destino,
            nome=responsavel.nome,
            rf=responsavel.rf,
        )


def copiar_alunos_periodo_parcial(solicitacao_origem, solicitacao_destino):
    alunos_em_periodo_parcial = solicitacao_origem.alunos_periodo_parcial.filter(
        data_removido__isnull=True
    )
    for aluno in alunos_em_periodo_parcial:
        AlunoPeriodoParcial.objects.create(
            solicitacao_medicao_inicial=solicitacao_destino,
            aluno=aluno.aluno,
            escola=solicitacao_destino.escola,
            data=datetime.date(
                int(solicitacao_destino.ano), int(solicitacao_destino.mes), 1
            ),
        )


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
    user, nome_arquivo, uuid_sol_medicao
):
    solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid=uuid_sol_medicao)
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        if solicitacao.escola.eh_cei:
            arquivo = relatorio_solicitacao_medicao_por_escola_cei(solicitacao)
        elif solicitacao.escola.eh_cemei:
            arquivo = relatorio_solicitacao_medicao_por_escola_cemei(solicitacao)
        elif solicitacao.escola.eh_emebs:
            arquivo = relatorio_solicitacao_medicao_por_escola_emebs(solicitacao)
        else:
            arquivo = relatorio_solicitacao_medicao_por_escola(solicitacao)
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
def gera_pdf_relatorio_unificado_async(
    user: str,
    nome_arquivo: str,
    ids_solicitacoes: list[UUID],
    tipos_de_unidade: list[str],
) -> None:
    """
    Gera um PDF unificado contendo os relatórios das solicitações informadas.

    A função cria um registro na Central de Download, processa cada solicitação
    gerando seus respectivos PDFs e, ao final, unifica todos os arquivos em um
    único PDF final.

    Args:
        user (str): Usuário responsável pela solicitação de geração.
        nome_arquivo (str): Nome do arquivo final a ser gerado.
        ids_solicitacoes (list[UUID]): Lista de UUIDs das solicitações.
        tipos_de_unidade (list[str]): Tipos de unidade utilizados para selecionar
            o módulo gerador do relatório.

    Raises:
        Exception: Qualquer erro interno durante o processo de merge ou geração
            é capturado e registrado na Central de Download.
    """
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        merger_lancamentos = PdfWriter()
        merger_arquivo_final = PdfWriter()

        processa_relatorio_lançamentos(
            ids_solicitacoes, tipos_de_unidade, merger_lancamentos, obj_central_download
        )

        output_final = cria_merge_pdfs(merger_lancamentos, merger_arquivo_final)

        atualiza_central_download(obj_central_download, nome_arquivo, output_final)

    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))
        logger.error(f"Erro ao gerar relatório unificado: {e}")

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


def processa_relatorio_lançamentos(
    ids_solicitacoes: list[UUID],
    tipos_de_unidade: list[str],
    merger_lancamentos: PdfWriter,
    obj_central_download: CentralDeDownload,
) -> None:
    """
    Processa cada solicitação gerando seu PDF individual e adicionando ao merger.

    Args:
        ids_solicitacoes (list[UUID]): Lista de UUIDs das solicitações.
        tipos_de_unidade (list[str]): Tipos de unidade para definir o módulo
            gerador de relatórios.
        merger_lancamentos (PdfWriter): Instância usada para acumular os PDFs.
        obj_central_download (CentralDeDownload): Objeto de controle na Central
            de Download para registrar erros e status.

    Raises:
        Exception: Erros individuais de processamento são capturados e
            registrados, sem interromper o processamento das demais solicitações.
    """

    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(uuid__in=ids_solicitacoes)
    modulo_da_unidade = obter_relatorio_da_unidade(tipos_de_unidade)
    for solicitacao in ordenar_unidades(solicitacoes):
        try:
            arquivo_lancamentos = modulo_da_unidade(solicitacao)
            arquivo_lancamentos_io = BytesIO(arquivo_lancamentos)
            merger_lancamentos.append(arquivo_lancamentos_io)
        except Exception as e:
            atualiza_central_download_com_erro(obj_central_download, str(e))
            logger.error(
                f"Erro ao mesclar arquivo para a solicitação {solicitacao.id}: {e}"
            )


def cria_merge_pdfs(
    merger_lancamentos: PdfWriter, merger_arquivo_final: PdfWriter
) -> bytes:
    """
    Realiza o merge dos PDFs individuais em um único arquivo final.

    Args:
        merger_lancamentos (PdfWriter): Writer contendo os PDFs das solicitações.
        merger_arquivo_final (PdfWriter): Writer responsável por gerar o PDF final.

    Returns:
        bytes: Conteúdo final do PDF unificado.

    Raises:
        Exception: Caso ocorra falha ao gerar ou escrever os arquivos PDF.
    """

    output_lancamentos = BytesIO()
    merger_lancamentos.write(output_lancamentos)
    output_lancamentos.seek(0)
    merger_arquivo_final.append(output_lancamentos)

    output_final = BytesIO()
    merger_arquivo_final.write(output_final)
    output_final.seek(0)

    merger_lancamentos.close()
    merger_arquivo_final.close()

    return output_final.getvalue()


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def exporta_relatorio_adesao_para_xlsx(user, nome_arquivo, resultados, query_params):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        arquivo = gera_relatorio_adesao_xlsx(resultados, query_params)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def exporta_relatorio_adesao_para_pdf(user, nome_arquivo, resultados, query_params):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        arquivo = gera_relatorio_adesao_pdf(resultados, query_params)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def exporta_relatorio_controle_frequencia_para_pdf(
    user, nome_arquivo, query_params, escola_uuid
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        arquivo = gera_relatorio_controle_frequencia_pdf(query_params, escola_uuid)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def exporta_relatorio_consolidado_xlsx(
    user, nome_arquivo, solicitacoes, tipos_de_unidade, query_params
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        arquivo = gera_relatorio_consolidado_xlsx(
            solicitacoes, tipos_de_unidade, query_params
        )
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)

    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))
        logger.error(f"Erro ao gerar relatório consolidado: {e}")

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def cria_relatorios_financeiros():
    logger.info(
        "x-x-x-x Iniciando criação de Relatórios Financeiros da Medição Inicial x-x-x-x"
    )

    data_hoje = datetime.date.today()
    quantidade_meses = 1
    while quantidade_meses <= 6:
        data = datetime.date(data_hoje.year, data_hoje.month, 1) + relativedelta(
            months=-quantidade_meses
        )
        cria_relatorios_financeiros_por_grupo_unidade_escolar(data)
        quantidade_meses += 1

    logger.info(
        "x-x-x-x Finaliza criação de Relatórios Financeiros da Medição Inicial x-x-x-x"
    )
