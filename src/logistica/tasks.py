import datetime
import logging

from celery import shared_task
from django.template.loader import render_to_string

from config import celery  # noqa: I001
from src.dados_comuns.fluxo_status import GuiaRemessaWorkFlow
from src.dados_comuns.models import Notificacao
from src.dados_comuns.tasks import envia_email_em_massa_task
from src.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from src.logistica.api.helpers import (
    retorna_dados_normalizados_excel_entregas_distribuidor,
    retorna_dados_normalizados_excel_visao_dilog,
    retorna_dados_normalizados_excel_visao_distribuidor,
)
from src.logistica.models.guia import Guia
from src.relatorios.relatorios import relatorio_guia_de_remessa

from .api.services.exporta_para_excel import RequisicoesExcelService
from .models import SolicitacaoRemessa

logger = logging.getLogger(__name__)


@celery.app.task(soft_time_limit=1000, time_limit=1200)  # noqa C901
def avisa_a_escola_que_hoje_tem_entrega_de_alimentos():
    hoje = datetime.date.today()

    guias = Guia.objects.filter(
        status=GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA, data_entrega=hoje
    )

    for guia in guias.all():
        if guia.escola:
            vinculos = guia.escola.vinculos.filter(
                ativo=True, data_inicial__isnull=False, data_final__isnull=True
            )

            users = [vinculo.usuario for vinculo in vinculos]
        else:
            users = []

        if users:
            texto_notificacao = render_to_string(
                template_name="logistica_notificacao_avisa_ue_para_conferir_no_prazo.html",
            )
            for user in users:
                Notificacao.notificar(
                    tipo=Notificacao.TIPO_NOTIFICACAO_AVISO,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
                    titulo=f"Hoje tem entrega de alimentos | Guia: {guia.numero_guia}",
                    descricao=texto_notificacao,
                    usuario=user,
                    link=f"/logistica/conferir-entrega?numero_guia={guia.numero_guia}",
                    guia=guia,
                )


@celery.app.task(soft_time_limit=1000, time_limit=1200)  # noqa C901
def avisa_a_escola_que_tem_guias_pendestes_de_conferencia():
    ontem = datetime.date.today() - datetime.timedelta(days=1)

    guias = Guia.objects.filter(
        status=GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA, data_entrega=ontem
    )

    for guia in guias.all():
        if guia.escola:
            vinculos = guia.escola.vinculos.filter(
                ativo=True, data_inicial__isnull=False, data_final__isnull=True
            )
            partes_interessadas = (
                [guia.escola.contato.email] if guia.escola.contato else []
            )
            users = [vinculo.usuario for vinculo in vinculos]

        else:
            partes_interessadas = []
            users = []

        if partes_interessadas:
            html = render_to_string(
                template_name="logistica_avisa_ue_que_prazo_para_conferencia_foi_ultrapassado.html",
                context={
                    "titulo": "Registro da Conferência da Guia de Remessa",
                    "numero_guia": guia.numero_guia,
                    "data_entrega": guia.data_entrega,
                },
            )

            envia_email_em_massa_task.delay(
                assunto="[SIGPAE] Registre a conferência da Guia de Remessa de alimentos!",
                emails=partes_interessadas,
                corpo="",
                html=html,
            )

        if users:
            texto_notificacao = render_to_string(
                template_name="logistica_notificacao_avisa_ue_que_prazo_para_conferencia_foi_ultrapassado.html",
                context={
                    "numero_guia": guia.numero_guia,
                    "data_entrega": guia.data_entrega,
                },
            )
            for user in users:
                Notificacao.notificar(
                    tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
                    titulo=(
                        f"A Guia de Remessa Nº {guia.numero_guia}, "
                        + f'com data de entrega prevista para {guia.data_entrega.strftime("%d/%m/%Y")}, '
                        + "está Pendente de Conferência"
                    ),
                    descricao=texto_notificacao,
                    usuario=user,
                    link=f"/logistica/conferir-entrega?numero_guia={guia.numero_guia}",
                    guia=guia,
                    renotificar=False,
                )


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limet=600,
    soft_time_limit=300,
)
def gera_pdf_async(user, nome_arquivo, list_guias):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        guias = Guia.objects.filter(id__in=list_guias)
        arquivo = relatorio_guia_de_remessa(guias=guias, is_async=True)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limet=600,
    soft_time_limit=300,
)
def gera_xlsx_async(username, nome_arquivo, ids_requisicoes, eh_distribuidor=False):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")

    obj_central_download = gera_objeto_na_central_download(
        user=username, identificador=nome_arquivo
    )
    try:
        queryset = SolicitacaoRemessa.objects.filter(id__in=ids_requisicoes)
        if eh_distribuidor:
            requisicoes = retorna_dados_normalizados_excel_visao_distribuidor(queryset)
            arquivo = RequisicoesExcelService.exportar_visao_distribuidor(
                requisicoes=requisicoes, is_async=True
            )
        else:
            requisicoes = retorna_dados_normalizados_excel_visao_dilog(queryset)
            arquivo = RequisicoesExcelService.exportar_visao_dilog(
                requisicoes=requisicoes, is_async=True
            )
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limet=600,
    soft_time_limit=300,
)
def gera_xlsx_entregas_async(
    uuid,
    username,
    tem_conferencia,
    tem_insucesso,
    eh_distribuidor=False,
    eh_dre=False,
    status_guia=None,
):
    queryset = SolicitacaoRemessa.objects.filter(uuid=uuid)

    if status_guia:
        queryset = queryset.filter(guias__status__in=status_guia)
    numero_solicitacao = (
        queryset.first().numero_solicitacao if queryset.first() else "vazio"
    )
    nome_arquivo = f"entregas_requisicao_{numero_solicitacao}.xlsx"

    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=username, identificador=nome_arquivo
    )

    queryset_insucesso = SolicitacaoRemessa.objects.filter(
        uuid=uuid, guias__status=GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO
    )

    requisicoes_insucesso = (
        retorna_dados_normalizados_excel_entregas_distribuidor(queryset_insucesso)
        if tem_insucesso
        else None
    )
    requisicoes = retorna_dados_normalizados_excel_entregas_distribuidor(queryset)

    try:
        if not eh_distribuidor and not eh_dre:
            perfil = "DILOG"
        else:
            perfil = "DISTRIBUIDOR" if eh_distribuidor else "DRE"

        arquivo = RequisicoesExcelService.exportar_entregas(
            requisicoes,
            requisicoes_insucesso,
            perfil,
            tem_conferencia,
            tem_insucesso,
            is_async=True,
        )

        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
