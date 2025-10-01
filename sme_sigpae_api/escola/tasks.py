import datetime
import io
import logging
import environ

from celery import shared_task
from django.core import management
from django.template.loader import render_to_string
from requests.exceptions import ConnectionError, Timeout

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.escola.utils_escola import (
    atualiza_codigo_codae_das_escolas,
    atualiza_tipo_gestao_das_escolas,
)

from ..cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ..cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ..cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from ..cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ..dados_comuns.fluxo_status import (
    PedidoAPartirDaDiretoriaRegionalWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ..dados_comuns.models import LogSolicitacoesUsuario
from ..escola.models import AlunosMatriculadosPeriodoEscola, FaixaEtaria, TipoTurma
from ..inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ..kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheUnificada,
)
from ..paineis_consolidados.models import SolicitacoesDRE
from ..perfil.models import Usuario
from ..relatorios.utils import html_to_pdf_file
from .utils import (
    calendario_sgp,
    ordenar_alunos_matriculados,
    registro_quantidade_alunos_matriculados_por_escola_periodo,
)
from .utils_montar_planilha_matriculados import build_xlsx_alunos_matriculados
from sme_sigpae_api.dados_comuns.utils import envia_email_unico

# https://docs.celeryproject.org/en/latest/userguide/tasks.html
logger = logging.getLogger("sigpae.taskEscola")
env = environ.Env()


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def atualiza_total_alunos_escolas():
    logger.debug(
        f"Iniciando task atualiza_total_alunos_escolas às {datetime.datetime.now()}"
    )
    management.call_command("atualiza_total_alunos_escolas", verbosity=0)


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def atualiza_dados_escolas():
    logger.debug(f"Iniciando task atualiza_dados_escolas às {datetime.datetime.now()}")
    management.call_command("atualiza_dados_escolas", verbosity=0)


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, Timeout),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=60 * 60,  # 1 hora
)
def atualiza_alunos_escolas(self):
    logger.debug(f"Iniciando task às {datetime.datetime.now()}")
    management.call_command("atualiza_alunos_escolas", verbosity=0)


def task_on_failure(self, exc, task_id, args, kwargs, einfo):
    assunto = "[CRÍTICO] Falha na task de atualização de alunos"

    html_message = render_to_string(
        "email_task_atualiza_alunos_escolas_falha.html",
        {
            "titulo": "Falha na atualização de alunos 🚨",
            "erro": str(exc),
            "task_id": task_id,
            "horario": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "hidden_email": False,
        },
    )

    # corpo texto puro para fallback
    corpo = f"""
    A task `atualiza_alunos_escolas` falhou definitivamente.

    Erro: {str(exc)}
    Task ID: {task_id}
    Horário: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    """

    envia_email_unico(
        assunto,
        corpo,
        env("EMAIL_NOTIFICACAO_FALHA_TASK"),
        template="",
        dados_template=None,
        html=html_message,
    )


atualiza_alunos_escolas.on_failure = task_on_failure.__get__(atualiza_alunos_escolas, type(atualiza_alunos_escolas))


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 3},
)
def atualiza_codigo_codae_das_escolas_task(path_planilha, id_planilha):
    logger.debug(
        f"Iniciando task atualiza_codigo_codae_das_escolas às {datetime.datetime.now()}"
    )
    atualiza_codigo_codae_das_escolas(path_planilha, id_planilha)


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 3},
)
def atualiza_tipo_gestao_das_escolas_task(path_planilha, id_planilha):
    logger.debug(
        f"Iniciando task atualiza_tipo_gestao_das_escolas às {datetime.datetime.now()}"
    )
    atualiza_tipo_gestao_das_escolas(path_planilha, id_planilha)


@shared_task(
    autoretry_for=(ConnectionError,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)
def nega_solicitacoes_vencidas():
    """Gestão de Alimentação.

    Nega solicitações não validadas pela DRE, ou seja, que possuam
    status igual a DRE_A_VALIDAR e que tenham o dia do evento
    menor que o dia de execução dessa task.
    """
    justificativa = "A solicitação não foi validada em tempo hábil"

    # Buscando solicitações da DRE não validadas que expiraram
    uuids_solicitacoes_dre_a_validar = (
        SolicitacoesDRE.objects.filter(
            status_atual=PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            data_evento__lt=datetime.date.today(),
        )
        .exclude(tipo_doc=SolicitacoesDRE.TP_SOL_DIETA_ESPECIAL)
        .values_list("uuid", flat=True)
        .distinct()
        .order_by("-data_log")
    )

    classes_solicitacoes = [
        SolicitacaoKitLancheAvulsa,
        SolicitacaoKitLancheCEIAvulsa,
        SolicitacaoKitLancheUnificada,
        SolicitacaoKitLancheCEMEI,
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoContinua,
        InclusaoAlimentacaoDaCEI,
        InclusaoDeAlimentacaoCEMEI,
        AlteracaoCardapio,
        AlteracaoCardapioCEI,
        AlteracaoCardapioCEMEI,
        InversaoCardapio,
    ]

    for classe_solicitacao in classes_solicitacoes:
        solicitacoes = classe_solicitacao.objects.filter(
            uuid__in=uuids_solicitacoes_dre_a_validar
        )
        if classe_solicitacao == AlteracaoCardapio:
            solicitacoes = solicitacoes.exclude(motivo__nome="Lanche Emergencial")
        for solicitacao in solicitacoes.all():
            usuario = Usuario.objects.filter(email="system@admin.com").first()
            solicitacao.dre_nao_valida(
                user=usuario if usuario else None, justificativa=justificativa
            )


@shared_task(
    autoretry_for=(ConnectionError,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)
def nega_solicitacoes_pendentes_autorizacao_vencidas():
    """Gestão de Alimentação.

    Nega solicitações validadas pela DRE (DRE_VALIDADO)
    e não validadas pela CODAE (CODAE_A_AUTORIZAR)
    que tenham o dia do evento menor que o dia de execução dessa task.
    """
    justificativa = "A solicitação não foi validada em tempo hábil"

    # Buscando solicitações da DRE validadas e não validadas pela CODAE que expiraram
    uuids_solicitacoes_dre_a_validar = (
        SolicitacoesDRE.objects.filter(
            status_atual__in=[
                PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
                PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
            ],
            data_evento__lt=datetime.date.today(),
        )
        .exclude(tipo_doc=SolicitacoesDRE.TP_SOL_DIETA_ESPECIAL)
        .values_list("uuid", flat=True)
        .distinct()
        .order_by("-data_log")
    )

    classes_solicitacoes = [
        SolicitacaoKitLancheAvulsa,
        SolicitacaoKitLancheCEIAvulsa,
        SolicitacaoKitLancheUnificada,
        GrupoInclusaoAlimentacaoNormal,
        InclusaoAlimentacaoContinua,
        InclusaoAlimentacaoDaCEI,
        AlteracaoCardapio,
        AlteracaoCardapioCEI,
        InversaoCardapio,
    ]

    for classe_solicitacao in classes_solicitacoes:
        solicitacoes = classe_solicitacao.objects.filter(
            uuid__in=uuids_solicitacoes_dre_a_validar
        )
        if classe_solicitacao == AlteracaoCardapio:
            solicitacoes = solicitacoes.exclude(motivo__nome="Lanche Emergencial")
        for solicitacao in solicitacoes.all():
            usuario = Usuario.objects.filter(email="system@admin.com").first()
            if solicitacao.status in [
                PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
                PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
            ]:
                solicitacao.codae_nega(
                    user=usuario if usuario else None, justificativa=justificativa
                )
            else:
                solicitacao.codae_nega_questionamento(
                    user=usuario if usuario else None, justificativa=justificativa
                )


@shared_task(
    autoretry_for=(ConnectionError,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)
def matriculados_por_escola_e_periodo_regulares():  # noqa C901
    """Medição Inicial.

    Consulta todos os dias a API do eol do SGP, para cada escola e turmas regulares,
    a quantidade de alunos matriculados por período no dia e armazena essa informação.
    """

    registro_quantidade_alunos_matriculados_por_escola_periodo(TipoTurma.REGULAR)


@shared_task(
    autoretry_for=(ConnectionError,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)
def matriculados_por_escola_e_periodo_programas():  # noqa C901
    """Medição Inicial.

    Consulta todos os dias a API do eol do SGP, para cada escola e turmas programas,
    a quantidade de alunos matriculados por período no dia e armazena essa informação.
    """

    registro_quantidade_alunos_matriculados_por_escola_periodo(TipoTurma.PROGRAMAS)


@shared_task(
    autoretry_for=(ConnectionError,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)
def calendario_escolas():  # noqa C901
    """Medição Inicial.

    Consulta o calendário de uma escola para o mês corrente.
    """

    calendario_sgp()


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def atualiza_cache_matriculados_por_faixa():
    logger.debug(
        f"Iniciando task atualiza_cache_matriculados_por_faixa às {datetime.datetime.now()}"
    )
    management.call_command("atualiza_cache_matriculados_por_faixa", verbosity=0)


def build_pdf_alunos_matriculados(dados, nome_arquivo):
    html_string = render_to_string("relatorio_alunos_matriculados.html", dados)
    return html_to_pdf_file(html_string, nome_arquivo, True)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=15000,
    soft_time_limit=15000,
)
def gera_pdf_relatorio_alunos_matriculados_async(user, nome_arquivo, uuids):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        queryset = []
        alunos_matriculados = AlunosMatriculadosPeriodoEscola.objects.filter(
            uuid__in=uuids
        )
        alunos_matriculados_ordenados = ordenar_alunos_matriculados(alunos_matriculados)
        fxs = [
            {"nome": faixa.__str__(), "uuid": str(faixa.uuid)}
            for faixa in FaixaEtaria.objects.filter(ativo=True)
        ]
        for matriculados in alunos_matriculados_ordenados:
            queryset.append(matriculados.formata_para_relatorio())
        dados = {
            "faixas_etarias": fxs,
            "queryset": queryset,
            "usuario": Usuario.objects.get(username=user).nome,
        }
        arquivo = build_pdf_alunos_matriculados(dados, nome_arquivo)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))
    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=15000,
    soft_time_limit=15000,
)
def gera_xlsx_relatorio_alunos_matriculados_async(user, nome_arquivo, uuids):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        queryset = []
        alunos_matriculados = AlunosMatriculadosPeriodoEscola.objects.filter(
            uuid__in=uuids
        )
        alunos_matriculados_ordenados = ordenar_alunos_matriculados(alunos_matriculados)
        fxs = [
            {"nome": faixa.__str__(), "uuid": str(faixa.uuid)}
            for faixa in FaixaEtaria.objects.filter(ativo=True)
        ]
        for matriculados in alunos_matriculados_ordenados:
            queryset.append(matriculados.formata_para_relatorio())
        dados = {
            "faixas_etarias": fxs,
            "queryset": queryset,
            "usuario": Usuario.objects.get(username=user).nome,
        }
        output = io.BytesIO()
        build_xlsx_alunos_matriculados(dados, nome_arquivo, output)
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))
    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def registra_historico_matriculas_alunos(*args, **kwargs):
    logger.debug(
        f"Iniciando task registra_historico_matriculas_alunos às {datetime.datetime.now()}"
    )
    ano = kwargs.get("ano")
    if ano is not None:
        management.call_command(
            "registra_historico_matriculas_alunos", f"--ano={ano}", verbosity=0
        )
    else:
        management.call_command("registra_historico_matriculas_alunos", verbosity=0)


@shared_task(
    autoretry_for=(ConnectionError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def cria_logs_alunos_por_dia_escolas_cei(*args, **kwargs):
    management.call_command("cria_logs_alunos_por_dia_escolas_cei", verbosity=0)
