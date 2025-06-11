"""Classes de apoio devem ser usadas em conjunto com as classes abstratas de fluxo.

Na pasta docs tem os BMPNs dos fluxos
"""

import datetime

import environ
import xworkflows
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.loader import render_to_string
from django_xworkflows import models as xwf_models
from rest_framework.exceptions import PermissionDenied

from sme_sigpae_api.dados_comuns import constants

from ..escola import models as m
from ..perfil.models import Usuario
from ..relatorios.utils import html_to_pdf_email_anexo
from .constants import (
    ADMINISTRADOR_MEDICAO,
    COGESTOR_DRE,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DIRETOR_UE,
)
from .models import AnexoLogSolicitacoesUsuario, LogSolicitacoesUsuario, Notificacao
from .services import EmailENotificacaoService, PartesInteressadasService
from .tasks import envia_email_em_massa_task, envia_email_unico_task
from .utils import (
    convert_base64_to_contentfile,
    envia_email_unico_com_anexo_inmemory,
    obter_dias_uteis_apos,
    preencher_template_e_notificar,
)

env = environ.Env()
base_url = f'{env("REACT_APP_URL")}'


class PedidoAPartirDaEscolaWorkflow(xwf_models.Workflow):
    # leia com atenção:
    # https://django-xworkflows.readthedocs.io/en/latest/index.html
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"  # INICIO
    DRE_A_VALIDAR = "DRE_A_VALIDAR"
    DRE_VALIDADO = "DRE_VALIDADO"
    # PODE HAVER LOOP AQUI...
    DRE_PEDIU_ESCOLA_REVISAR = "DRE_PEDIU_ESCOLA_REVISAR"
    DRE_NAO_VALIDOU_PEDIDO_ESCOLA = "DRE_NAO_VALIDOU_PEDIDO_ESCOLA"  # FIM DE FLUXO
    CODAE_AUTORIZADO = "CODAE_AUTORIZADO"
    CODAE_QUESTIONADO = "CODAE_QUESTIONADO"
    CODAE_NEGOU_PEDIDO = "CODAE_NEGOU_PEDIDO"  # FIM, NOTIFICA ESCOLA E DRE
    TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO = "TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO"
    # FIM, NOTIFICA ESCOLA, DRE E CODAE
    TERCEIRIZADA_TOMOU_CIENCIA = "TERCEIRIZADA_TOMOU_CIENCIA"

    # UM STATUS POSSIVEL, QUE PODE SER ATIVADO PELA ESCOLA EM ATE X HORAS ANTES
    # AS TRANSIÇÕES NÃO ENXERGAM ESSE STATUS
    ESCOLA_CANCELOU = "ESCOLA_CANCELOU"

    # TEM UMA ROTINA QUE CANCELA CASO O PEDIDO TENHA PASSADO DO DIA E NÃO TENHA TERMINADO O FLUXO
    # AS TRANSIÇÕES NÃO ENXERGAM ESSE STATUS
    CANCELADO_AUTOMATICAMENTE = "CANCELADO_AUTOMATICAMENTE"

    states = (
        (RASCUNHO, "Rascunho"),
        (DRE_A_VALIDAR, "DRE a validar"),
        (DRE_VALIDADO, "DRE validado"),
        (DRE_PEDIU_ESCOLA_REVISAR, "Escola tem que revisar o pedido"),
        (DRE_NAO_VALIDOU_PEDIDO_ESCOLA, "DRE não validou pedido da escola"),
        (CODAE_AUTORIZADO, "CODAE autorizou pedido"),
        (
            CODAE_QUESTIONADO,
            "CODAE questionou terceirizada se é possível atender a solicitação",
        ),
        (CODAE_NEGOU_PEDIDO, "CODAE negou pedido"),
        (
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            "Terceirizada respondeu se é possível atender a solicitação",
        ),
        (TERCEIRIZADA_TOMOU_CIENCIA, "Terceirizada tomou"),
        (ESCOLA_CANCELOU, "Escola cancelou"),
        (CANCELADO_AUTOMATICAMENTE, "Cancelamento automático"),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, DRE_A_VALIDAR),
        ("dre_valida", DRE_A_VALIDAR, DRE_VALIDADO),
        ("dre_pede_revisao", DRE_A_VALIDAR, DRE_PEDIU_ESCOLA_REVISAR),
        ("dre_nao_valida", DRE_A_VALIDAR, DRE_NAO_VALIDOU_PEDIDO_ESCOLA),
        ("escola_revisa", DRE_PEDIU_ESCOLA_REVISAR, DRE_A_VALIDAR),
        ("codae_autoriza", DRE_VALIDADO, CODAE_AUTORIZADO),
        ("codae_questiona", DRE_VALIDADO, CODAE_QUESTIONADO),
        (
            "codae_autoriza_questionamento",
            [DRE_VALIDADO, TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO],
            CODAE_AUTORIZADO,
        ),
        (
            "codae_nega_questionamento",
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            CODAE_NEGOU_PEDIDO,
        ),
        ("codae_nega", [DRE_VALIDADO, CODAE_QUESTIONADO], CODAE_NEGOU_PEDIDO),
        (
            "terceirizada_responde_questionamento",
            CODAE_QUESTIONADO,
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        ),
        ("terceirizada_toma_ciencia", CODAE_AUTORIZADO, TERCEIRIZADA_TOMOU_CIENCIA),
    )

    initial_state = RASCUNHO


class PedidoAPartirDaDiretoriaRegionalWorkflow(xwf_models.Workflow):
    # leia com atenção:
    # https://django-xworkflows.readthedocs.io/en/latest/index.html

    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"  # INICIO
    CODAE_A_AUTORIZAR = "CODAE_A_AUTORIZAR"
    # PODE HAVER LOOP AQUI...
    CODAE_PEDIU_DRE_REVISAR = "DRE_PEDE_ESCOLA_REVISAR"
    CODAE_NEGOU_PEDIDO = "CODAE_NEGOU_PEDIDO"  # FIM DE FLUXO
    CODAE_AUTORIZADO = "CODAE_AUTORIZADO"
    CODAE_QUESTIONADO = "CODAE_QUESTIONADO"
    # FIM, NOTIFICA ESCOLA, DRE E CODAE
    TERCEIRIZADA_TOMOU_CIENCIA = "TERCEIRIZADA_TOMOU_CIENCIA"
    TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO = "TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO"

    # UM STATUS POSSIVEL, QUE PODE SER ATIVADO PELA DRE EM ATE X HORAS ANTES
    # AS TRANSIÇÕES NÃO ENXERGAM ESSE STATUS
    DRE_CANCELOU = "DRE_CANCELOU"

    # TEM UMA ROTINA QUE CANCELA CASO O PEDIDO TENHA PASSADO DO DIA E NÃO TENHA TERMINADO O FLUXO
    # AS TRANSIÇÕES NÃO ENXERGAM ESSE STATUS
    CANCELAMENTO_AUTOMATICO = "CANCELAMENTO_AUTOMATICO"

    states = (
        (RASCUNHO, "Rascunho"),
        (CODAE_A_AUTORIZAR, "CODAE a autorizar"),
        (CODAE_PEDIU_DRE_REVISAR, "DRE tem que revisar o pedido"),
        (CODAE_NEGOU_PEDIDO, "CODAE negou o pedido da DRE"),
        (CODAE_AUTORIZADO, "CODAE autorizou"),
        (
            CODAE_QUESTIONADO,
            "CODAE questionou terceirizada se é possível atender a solicitação",
        ),
        (TERCEIRIZADA_TOMOU_CIENCIA, "Terceirizada tomou ciencia"),
        (
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            "Terceirizada respondeu se é possível atender a solicitação",
        ),
        (CANCELAMENTO_AUTOMATICO, "Cancelamento automático"),
        (DRE_CANCELOU, "DRE cancelou"),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, CODAE_A_AUTORIZAR),
        ("codae_pede_revisao", CODAE_A_AUTORIZAR, CODAE_PEDIU_DRE_REVISAR),
        ("codae_nega", [CODAE_A_AUTORIZAR, CODAE_QUESTIONADO], CODAE_NEGOU_PEDIDO),
        ("dre_revisa", CODAE_PEDIU_DRE_REVISAR, CODAE_A_AUTORIZAR),
        ("codae_autoriza", CODAE_A_AUTORIZAR, CODAE_AUTORIZADO),
        ("codae_questiona", CODAE_A_AUTORIZAR, CODAE_QUESTIONADO),
        (
            "codae_autoriza_questionamento",
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            CODAE_AUTORIZADO,
        ),
        (
            "codae_nega_questionamento",
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            CODAE_NEGOU_PEDIDO,
        ),
        ("terceirizada_toma_ciencia", CODAE_AUTORIZADO, TERCEIRIZADA_TOMOU_CIENCIA),
        (
            "terceirizada_responde_questionamento",
            CODAE_QUESTIONADO,
            TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        ),
    )

    initial_state = RASCUNHO


class InformativoPartindoDaEscolaWorkflow(xwf_models.Workflow):
    # leia com atenção:
    # https://django-xworkflows.readthedocs.io/en/latest/index.html
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"  # INICIO
    INFORMADO = "INFORMADO"
    TERCEIRIZADA_TOMOU_CIENCIA = "TERCEIRIZADA_TOMOU_CIENCIA"
    ESCOLA_CANCELOU = "ESCOLA_CANCELOU"

    states = (
        (RASCUNHO, "Rascunho"),
        (INFORMADO, "Informado"),
        (TERCEIRIZADA_TOMOU_CIENCIA, "Terceirizada toma ciencia"),
        (ESCOLA_CANCELOU, "Escola cancelou"),
    )

    transitions = (
        ("informa", RASCUNHO, INFORMADO),
        ("terceirizada_toma_ciencia", INFORMADO, TERCEIRIZADA_TOMOU_CIENCIA),
        ("escola_cancela", [INFORMADO, TERCEIRIZADA_TOMOU_CIENCIA], ESCOLA_CANCELOU),
    )

    initial_state = RASCUNHO


class SolicitacaoRemessaWorkFlow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    AGUARDANDO_ENVIO = "AGUARDANDO_ENVIO"
    DILOG_ENVIA = "DILOG_ENVIA"
    AGUARDANDO_CANCELAMENTO = "AGUARDANDO_CANCELAMENTO"
    PAPA_CANCELA = "CANCELADA"
    DISTRIBUIDOR_CONFIRMA = "DISTRIBUIDOR_CONFIRMA"
    DISTRIBUIDOR_SOLICITA_ALTERACAO = "DISTRIBUIDOR_SOLICITA_ALTERACAO"
    DILOG_ACEITA_ALTERACAO = "DILOG_ACEITA_ALTERACAO"

    states = (
        (AGUARDANDO_ENVIO, "Aguardando envio"),
        (DILOG_ENVIA, "Enviada"),
        (AGUARDANDO_CANCELAMENTO, "Aguardando cancelamento"),
        (PAPA_CANCELA, "Cancelada"),
        (DISTRIBUIDOR_CONFIRMA, "Confirmada"),
        (DISTRIBUIDOR_SOLICITA_ALTERACAO, "Em análise"),
        (DILOG_ACEITA_ALTERACAO, "Alterada"),
    )

    transitions = (
        ("inicia_fluxo", AGUARDANDO_ENVIO, DILOG_ENVIA),
        ("empresa_atende", DILOG_ENVIA, DISTRIBUIDOR_CONFIRMA),
        ("solicita_alteracao", DILOG_ENVIA, DISTRIBUIDOR_SOLICITA_ALTERACAO),
        (
            "cancela_solicitacao",
            [
                AGUARDANDO_ENVIO,
                DILOG_ENVIA,
                DISTRIBUIDOR_CONFIRMA,
                DISTRIBUIDOR_SOLICITA_ALTERACAO,
                PAPA_CANCELA,
                DILOG_ACEITA_ALTERACAO,
            ],
            PAPA_CANCELA,
        ),
        (
            "dilog_aceita_alteracao",
            DISTRIBUIDOR_SOLICITA_ALTERACAO,
            DILOG_ACEITA_ALTERACAO,
        ),
        ("dilog_nega_alteracao", DISTRIBUIDOR_SOLICITA_ALTERACAO, DILOG_ENVIA),
        (
            "aguarda_confirmacao_de_cancelamento",
            [DISTRIBUIDOR_CONFIRMA, DISTRIBUIDOR_SOLICITA_ALTERACAO],
            AGUARDANDO_CANCELAMENTO,
        ),
        ("distribuidor_confirma_cancelamento", AGUARDANDO_CANCELAMENTO, PAPA_CANCELA),
        (
            "distribuidor_confirma_cancelamento_envia_email_notificacao",
            PAPA_CANCELA,
            PAPA_CANCELA,
        ),
    )

    initial_state = AGUARDANDO_ENVIO


class SolicitacaoDeAlteracaoWorkFlow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    EM_ANALISE = "EM_ANALISE"
    ACEITA = "ACEITA"
    NEGADA = "NEGADA"

    states = (
        (EM_ANALISE, "Em análise"),
        (ACEITA, "Aceita"),
        (NEGADA, "Negada"),
    )

    transitions = (
        ("dilog_aceita", EM_ANALISE, ACEITA),
        ("dilog_nega", EM_ANALISE, NEGADA),
        ("inicia_fluxo", EM_ANALISE, EM_ANALISE),
    )

    initial_state = EM_ANALISE


class GuiaRemessaWorkFlow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    AGUARDANDO_ENVIO = "AGUARDANDO_ENVIO"
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    PENDENTE_DE_CONFERENCIA = "PENDENTE_DE_CONFERENCIA"
    DISTRIBUIDOR_REGISTRA_INSUCESSO = "DISTRIBUIDOR_REGISTRA_INSUCESSO"
    RECEBIDA = "RECEBIDA"
    NAO_RECEBIDA = "NAO_RECEBIDA"
    RECEBIMENTO_PARCIAL = "RECEBIMENTO_PARCIAL"
    REPOSICAO_TOTAL = "REPOSICAO_TOTAL"
    REPOSICAO_PARCIAL = "REPOSICAO_PARCIAL"
    CANCELADA = "CANCELADA"
    AGUARDANDO_CANCELAMENTO = "AGUARDANDO_CANCELAMENTO"

    states = (
        (AGUARDANDO_ENVIO, "Aguardando envio"),
        (AGUARDANDO_CONFIRMACAO, "Aguardando confirmação"),
        (PENDENTE_DE_CONFERENCIA, "Pendente de conferência"),
        (DISTRIBUIDOR_REGISTRA_INSUCESSO, "Insucesso de entrega"),
        (RECEBIDA, "Recebida"),
        (NAO_RECEBIDA, "Não recebida"),
        (RECEBIMENTO_PARCIAL, "Recebimento parcial"),
        (REPOSICAO_TOTAL, "Reposição total"),
        (REPOSICAO_PARCIAL, "Reposição parcial"),
        (CANCELADA, "Cancelada"),
        (AGUARDANDO_CANCELAMENTO, "Aguardando cancelamento"),
    )

    transitions = (
        ("distribuidor_confirma_guia", AGUARDANDO_CONFIRMACAO, PENDENTE_DE_CONFERENCIA),
        (
            "distribuidor_confirma_guia_envia_email_e_notificacao",
            PENDENTE_DE_CONFERENCIA,
            PENDENTE_DE_CONFERENCIA,
        ),
        (
            "distribuidor_registra_insucesso",
            PENDENTE_DE_CONFERENCIA,
            DISTRIBUIDOR_REGISTRA_INSUCESSO,
        ),
        (
            "escola_recebe",
            [
                PENDENTE_DE_CONFERENCIA,
                DISTRIBUIDOR_REGISTRA_INSUCESSO,
                NAO_RECEBIDA,
                RECEBIMENTO_PARCIAL,
                RECEBIDA,
                REPOSICAO_PARCIAL,
                REPOSICAO_TOTAL,
            ],
            RECEBIDA,
        ),
        (
            "escola_nao_recebe",
            [
                PENDENTE_DE_CONFERENCIA,
                DISTRIBUIDOR_REGISTRA_INSUCESSO,
                NAO_RECEBIDA,
                RECEBIMENTO_PARCIAL,
                RECEBIDA,
                REPOSICAO_PARCIAL,
                REPOSICAO_TOTAL,
            ],
            NAO_RECEBIDA,
        ),
        (
            "escola_recebe_parcial",
            [
                PENDENTE_DE_CONFERENCIA,
                DISTRIBUIDOR_REGISTRA_INSUCESSO,
                NAO_RECEBIDA,
                RECEBIMENTO_PARCIAL,
                RECEBIDA,
                REPOSICAO_PARCIAL,
                REPOSICAO_TOTAL,
            ],
            RECEBIMENTO_PARCIAL,
        ),
        (
            "escola_recebe_parcial_atraso",
            [
                PENDENTE_DE_CONFERENCIA,
                DISTRIBUIDOR_REGISTRA_INSUCESSO,
                NAO_RECEBIDA,
                RECEBIMENTO_PARCIAL,
                RECEBIDA,
                REPOSICAO_PARCIAL,
                REPOSICAO_TOTAL,
            ],
            RECEBIMENTO_PARCIAL,
        ),
        (
            "reposicao_parcial",
            [NAO_RECEBIDA, RECEBIMENTO_PARCIAL, REPOSICAO_PARCIAL, REPOSICAO_TOTAL],
            REPOSICAO_PARCIAL,
        ),
        (
            "reposicao_total",
            [NAO_RECEBIDA, RECEBIMENTO_PARCIAL, REPOSICAO_PARCIAL, REPOSICAO_TOTAL],
            REPOSICAO_TOTAL,
        ),
    )

    initial_state = AGUARDANDO_ENVIO


class DietaEspecialWorkflow(xwf_models.Workflow):
    # leia com atenção:
    # https://django-xworkflows.readthedocs.io/en/latest/index.html
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"
    CODAE_A_AUTORIZAR = "CODAE_A_AUTORIZAR"  # INICIO
    CODAE_NEGOU_PEDIDO = "CODAE_NEGOU_PEDIDO"
    CODAE_AUTORIZADO = "CODAE_AUTORIZADO"
    TERCEIRIZADA_TOMOU_CIENCIA = "TERCEIRIZADA_TOMOU_CIENCIA"
    ESCOLA_SOLICITOU_INATIVACAO = "ESCOLA_SOLICITOU_INATIVACAO"
    CODAE_NEGOU_INATIVACAO = "CODAE_NEGOU_INATIVACAO"
    CODAE_AUTORIZOU_INATIVACAO = "CODAE_AUTORIZOU_INATIVACAO"
    TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO = "TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO"
    TERMINADA_AUTOMATICAMENTE_SISTEMA = "TERMINADA_AUTOMATICAMENTE_SISTEMA"
    CANCELADO_ALUNO_MUDOU_ESCOLA = "CANCELADO_ALUNO_MUDOU_ESCOLA"
    CANCELADO_ALUNO_NAO_PERTENCE_REDE = "CANCELADO_ALUNO_NAO_PERTENCE_REDE"

    ESCOLA_CANCELOU = "ESCOLA_CANCELOU"
    CODAE_NEGOU_CANCELAMENTO = "CODAE_NEGOU_CANCELAMENTO"

    states = (
        (RASCUNHO, "Rascunho"),
        (CODAE_A_AUTORIZAR, "CODAE a autorizar"),
        (CODAE_NEGOU_PEDIDO, "CODAE negou a solicitação"),
        (CODAE_AUTORIZADO, "CODAE autorizou"),
        (TERCEIRIZADA_TOMOU_CIENCIA, "Terceirizada toma ciencia"),
        (ESCOLA_CANCELOU, "Escola cancelou"),
        (CODAE_NEGOU_CANCELAMENTO, "CODAE negou o cancelamento"),
        (ESCOLA_SOLICITOU_INATIVACAO, "Escola solicitou cancelamento"),
        (CODAE_NEGOU_INATIVACAO, "CODAE negou o cancelamento"),
        (CODAE_AUTORIZOU_INATIVACAO, "CODAE autorizou o cancelamento"),
        (
            TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
            "Terceirizada tomou ciência do cancelamento",
        ),
        (TERMINADA_AUTOMATICAMENTE_SISTEMA, "Data de término atingida"),
        (
            CANCELADO_ALUNO_MUDOU_ESCOLA,
            "Cancelamento por alteração de unidade educacional",
        ),
        (
            CANCELADO_ALUNO_NAO_PERTENCE_REDE,
            "Cancelamento para aluno não matriculado na rede municipal",
        ),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, CODAE_A_AUTORIZAR),
        ("codae_nega", [CODAE_A_AUTORIZAR], CODAE_NEGOU_PEDIDO),
        ("codae_autoriza", [RASCUNHO, CODAE_A_AUTORIZAR], CODAE_AUTORIZADO),
        ("terceirizada_toma_ciencia", CODAE_AUTORIZADO, TERCEIRIZADA_TOMOU_CIENCIA),
        (
            "cancelar_pedido",
            [CODAE_A_AUTORIZAR, ESCOLA_SOLICITOU_INATIVACAO, CODAE_AUTORIZADO],
            ESCOLA_CANCELOU,
        ),
        (
            "negar_cancelamento_pedido",
            [CODAE_A_AUTORIZAR, ESCOLA_SOLICITOU_INATIVACAO],
            CODAE_NEGOU_CANCELAMENTO,
        ),
        (
            "inicia_fluxo_inativacao",
            [RASCUNHO, CODAE_AUTORIZADO, TERCEIRIZADA_TOMOU_CIENCIA],
            ESCOLA_SOLICITOU_INATIVACAO,
        ),
        ("codae_nega_inativacao", ESCOLA_SOLICITOU_INATIVACAO, CODAE_NEGOU_INATIVACAO),
        (
            "codae_autoriza_inativacao",
            ESCOLA_SOLICITOU_INATIVACAO,
            CODAE_AUTORIZOU_INATIVACAO,
        ),
        (
            "terceirizada_toma_ciencia_inativacao",
            CODAE_AUTORIZOU_INATIVACAO,
            TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        ),
        ("cancelar_aluno_mudou_escola", CODAE_AUTORIZADO, CANCELADO_ALUNO_MUDOU_ESCOLA),
        (
            "cancelar_aluno_nao_pertence_rede",
            CODAE_AUTORIZADO,
            CANCELADO_ALUNO_NAO_PERTENCE_REDE,
        ),
    )

    initial_state = RASCUNHO


class HomologacaoProdutoWorkflow(xwf_models.Workflow):
    # leia com atenção:
    # https://django-xworkflows.readthedocs.io/en/latest/index.html
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"
    CODAE_PENDENTE_HOMOLOGACAO = "CODAE_PENDENTE_HOMOLOGACAO"  # INICIO
    CODAE_HOMOLOGADO = "CODAE_HOMOLOGADO"
    CODAE_NAO_HOMOLOGADO = "CODAE_NAO_HOMOLOGADO"
    CODAE_QUESTIONADO = "CODAE_QUESTIONADO"
    CODAE_PEDIU_ANALISE_SENSORIAL = "CODAE_PEDIU_ANALISE_SENSORIAL"
    CODAE_CANCELOU_ANALISE_SENSORIAL = "CODAE_CANCELOU_ANALISE_SENSORIAL"
    TERCEIRIZADA_CANCELOU = "TERCEIRIZADA_CANCELOU"
    INATIVA = "HOMOLOGACAO_INATIVA"
    CODAE_SUSPENDEU = "CODAE_SUSPENDEU"
    ESCOLA_OU_NUTRICIONISTA_RECLAMOU = "ESCOLA_OU_NUTRICIONISTA_RECLAMOU"
    CODAE_QUESTIONOU_UE = "CODAE_QUESTIONOU_UE"
    UE_RESPONDEU_QUESTIONAMENTO = "UE_RESPONDEU_QUESTIONAMENTO"
    CODAE_QUESTIONOU_NUTRISUPERVISOR = "CODAE_QUESTIONOU_NUTRISUPERVISOR"
    NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO = (
        "NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO"
    )
    CODAE_PEDIU_ANALISE_RECLAMACAO = "CODAE_PEDIU_ANALISE_RECLAMACAO"
    TERCEIRIZADA_RESPONDEU_RECLAMACAO = "TERCEIRIZADA_RESPONDEU_RECLAMACAO"
    CODAE_AUTORIZOU_RECLAMACAO = "CODAE_AUTORIZOU_RECLAMACAO"
    TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO = (
        "TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO"
    )

    states = (
        (RASCUNHO, "Rascunho"),
        (CODAE_PENDENTE_HOMOLOGACAO, "Pendente homologação da CODAE"),
        (CODAE_HOMOLOGADO, "CODAE homologou"),
        (CODAE_NAO_HOMOLOGADO, "CODAE não homologou"),
        (CODAE_QUESTIONADO, "CODAE pediu correção"),
        (CODAE_PEDIU_ANALISE_SENSORIAL, "CODAE pediu análise sensorial"),
        (CODAE_CANCELOU_ANALISE_SENSORIAL, "CODAE cancelou análise sensorial"),
        (TERCEIRIZADA_CANCELOU, "Terceirizada cancelou homologação"),
        (INATIVA, "Homologação inativada"),
        (CODAE_SUSPENDEU, "CODAE suspendeu o produto"),
        (ESCOLA_OU_NUTRICIONISTA_RECLAMOU, "Escola/Nutricionista reclamou do produto"),
        (CODAE_QUESTIONOU_UE, "CODAE questionou U.E."),
        (UE_RESPONDEU_QUESTIONAMENTO, "U.E respondeu questionamento"),
        (CODAE_QUESTIONOU_NUTRISUPERVISOR, "CODAE questionou Nutrisupervisor"),
        (
            NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
            "Nutrisupervisor respondeu questionamento",
        ),
        (CODAE_PEDIU_ANALISE_RECLAMACAO, "CODAE pediu análise da reclamação"),
        (TERCEIRIZADA_RESPONDEU_RECLAMACAO, "Terceirizada respondeu a reclamação"),
        (CODAE_AUTORIZOU_RECLAMACAO, "CODAE autorizou reclamação"),
        (
            TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
            "Terceirizada cancelou solicitação de homologação de produto",
        ),
    )

    transitions = (
        (
            "inicia_fluxo",
            [
                RASCUNHO,
                CODAE_NAO_HOMOLOGADO,
                CODAE_HOMOLOGADO,
                CODAE_SUSPENDEU,
                TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
                CODAE_QUESTIONADO,
                CODAE_AUTORIZOU_RECLAMACAO,
                CODAE_CANCELOU_ANALISE_SENSORIAL,
            ],
            CODAE_PENDENTE_HOMOLOGACAO,
        ),
        (
            "codae_homologa",
            [
                CODAE_PENDENTE_HOMOLOGACAO,
                CODAE_PEDIU_ANALISE_SENSORIAL,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                CODAE_SUSPENDEU,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                CODAE_CANCELOU_ANALISE_SENSORIAL,
            ],
            CODAE_HOMOLOGADO,
        ),
        (
            "codae_nao_homologa",
            [CODAE_PENDENTE_HOMOLOGACAO, CODAE_PEDIU_ANALISE_SENSORIAL],
            CODAE_NAO_HOMOLOGADO,
        ),
        ("codae_questiona", CODAE_PENDENTE_HOMOLOGACAO, CODAE_QUESTIONADO),
        (
            "terceirizada_responde_questionamento",
            CODAE_QUESTIONADO,
            CODAE_PENDENTE_HOMOLOGACAO,
        ),
        (
            "codae_pede_analise_sensorial",
            [
                CODAE_PEDIU_ANALISE_RECLAMACAO,
                UE_RESPONDEU_QUESTIONAMENTO,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                CODAE_PENDENTE_HOMOLOGACAO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                CODAE_HOMOLOGADO,
            ],
            CODAE_PEDIU_ANALISE_SENSORIAL,
        ),
        (
            "codae_cancela_analise_sensorial",
            CODAE_PEDIU_ANALISE_SENSORIAL,
            CODAE_CANCELOU_ANALISE_SENSORIAL,
        ),
        (
            "terceirizada_responde_analise_sensorial",
            CODAE_PEDIU_ANALISE_SENSORIAL,
            CODAE_PENDENTE_HOMOLOGACAO,
        ),
        (
            "codae_suspende",
            [CODAE_PENDENTE_HOMOLOGACAO, CODAE_HOMOLOGADO],
            CODAE_SUSPENDEU,
        ),
        (
            "codae_ativa",
            [CODAE_SUSPENDEU, CODAE_HOMOLOGADO, CODAE_AUTORIZOU_RECLAMACAO],
            CODAE_HOMOLOGADO,
        ),
        (
            "escola_ou_nutricionista_reclamou",
            [CODAE_HOMOLOGADO, CODAE_CANCELOU_ANALISE_SENSORIAL],
            ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
        ),
        (
            "codae_questiona_ue",
            [
                CODAE_PEDIU_ANALISE_RECLAMACAO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                UE_RESPONDEU_QUESTIONAMENTO,
                CODAE_QUESTIONOU_UE,
                CODAE_QUESTIONOU_NUTRISUPERVISOR,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                CODAE_PEDIU_ANALISE_SENSORIAL,
            ],
            CODAE_QUESTIONOU_UE,
        ),
        (
            "codae_questiona_nutrisupervisor",
            [
                UE_RESPONDEU_QUESTIONAMENTO,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            ],
            CODAE_QUESTIONOU_NUTRISUPERVISOR,
        ),
        (
            "nutrisupervisor_respondeu_questionamento",
            CODAE_QUESTIONOU_NUTRISUPERVISOR,
            NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        ),
        (
            "ue_respondeu_questionamento",
            CODAE_QUESTIONOU_UE,
            UE_RESPONDEU_QUESTIONAMENTO,
        ),
        (
            "codae_pediu_analise_reclamacao",
            [
                CODAE_PEDIU_ANALISE_RECLAMACAO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                UE_RESPONDEU_QUESTIONAMENTO,
                CODAE_QUESTIONOU_UE,
                CODAE_QUESTIONOU_NUTRISUPERVISOR,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                CODAE_PEDIU_ANALISE_SENSORIAL,
            ],
            CODAE_PEDIU_ANALISE_RECLAMACAO,
        ),
        (
            "terceirizada_responde_reclamacao",
            CODAE_PEDIU_ANALISE_RECLAMACAO,
            TERCEIRIZADA_RESPONDEU_RECLAMACAO,
        ),
        (
            "codae_autorizou_reclamacao",
            [
                CODAE_PEDIU_ANALISE_RECLAMACAO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                UE_RESPONDEU_QUESTIONAMENTO,
                CODAE_QUESTIONOU_UE,
                CODAE_QUESTIONOU_NUTRISUPERVISOR,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                CODAE_PEDIU_ANALISE_SENSORIAL,
            ],
            CODAE_AUTORIZOU_RECLAMACAO,
        ),
        (
            "codae_recusou_reclamacao",
            [
                CODAE_PEDIU_ANALISE_RECLAMACAO,
                CODAE_HOMOLOGADO,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                UE_RESPONDEU_QUESTIONAMENTO,
                NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
                TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                CODAE_QUESTIONOU_UE,
                CODAE_QUESTIONOU_NUTRISUPERVISOR,
                CODAE_PEDIU_ANALISE_SENSORIAL,
            ],
            CODAE_HOMOLOGADO,
        ),
        (
            "inativa_homologacao",
            [
                CODAE_SUSPENDEU,
                ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                CODAE_QUESTIONADO,
                CODAE_HOMOLOGADO,
                CODAE_NAO_HOMOLOGADO,
                CODAE_AUTORIZOU_RECLAMACAO,
                TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
            ],
            INATIVA,
        ),
        (
            "terceirizada_cancelou_solicitacao_homologacao",
            CODAE_PENDENTE_HOMOLOGACAO,
            TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
        ),
        (
            "terceirizada_responde_analise_sensorial_da_reclamacao",
            CODAE_PEDIU_ANALISE_SENSORIAL,
            ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
        ),
        (
            "terceirizada_responde_analise_sensorial_homologado",
            CODAE_PEDIU_ANALISE_SENSORIAL,
            CODAE_HOMOLOGADO,
        ),
        (
            "codae_cancela_solicitacao_correcao",
            CODAE_QUESTIONADO,
            CODAE_PENDENTE_HOMOLOGACAO,
        ),
        (
            "terceirizada_cancela_solicitacao_correcao",
            CODAE_QUESTIONADO,
            CODAE_PENDENTE_HOMOLOGACAO,
        ),
    )

    initial_state = RASCUNHO


class FluxoSolicitacaoRemessa(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = SolicitacaoRemessaWorkFlow
    status = xwf_models.StateField(workflow_class)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    def _preenche_template_e_envia_email(
        self, assunto, titulo, user, partes_interessadas
    ):
        raise NotImplementedError(
            "Deve criar um método de envio de email as partes interessadas"
        )

    def _titulo_notificacao_confirma_cancelamento(self):
        return f"Cancelamento de Guias de Remessa da Requisição N° {self.numero_solicitacao}"

    def _titulo_notificacao_cancelamento_confirmado(self):
        return f"Cancelamento Confirmado - Guias de Remessa da Requisição N° {self.numero_solicitacao}"

    def _envia_email_dilog_envia_solicitacao_para_distibuidor(self, log_transicao):
        url = f'{env("REACT_APP_URL")}/logistica/gestao-requisicao-entrega?numero_requisicao={self.numero_solicitacao}'
        html = render_to_string(
            template_name="logistica_dilog_envia_solicitacao.html",
            context={
                "titulo": "Nova Requisição de Entrega",
                "solicitacao": self.numero_solicitacao,
                "log_transicao": log_transicao,
                "url": url,
            },
        )
        envia_email_unico_task.delay(
            assunto=f"[SIGPAE] Nova Requisição de Entrega N° {self.numero_solicitacao}",
            corpo="",
            email=self.distribuidor.responsavel_email,
            html=html,
        )

    def _envia_email_aguarda_cancelamento_para_distibuidor(self, log_transicao):
        url = f'{env("REACT_APP_URL")}/logistica/gestao-requisicao-entrega?numero_requisicao={self.numero_solicitacao}'
        html = render_to_string(
            template_name="logistica_aguardando_cancelamento_distribuidor.html",
            context={
                "titulo": "Cancelamento de Guia(s) de Remessa",
                "solicitacao": self.numero_solicitacao,
                "log_transicao": log_transicao,
                "url": url,
            },
        )
        envia_email_unico_task.delay(
            assunto=f"[SIGPAE] Cancelamento de Guia(s) de Remessa da Requisição N° {self.numero_solicitacao}",
            corpo="",
            email=self.distribuidor.responsavel_email,
            html=html,
        )

    def _envia_email_distribuidor_confirma_cancelamento(
        self, log_transicao, partes_interessadas
    ):
        url = f"{base_url}/logistica/envio-requisicoes-entrega-completo?numero_requisicao={self.numero_solicitacao}"
        html = render_to_string(
            template_name="logistica_distribuidor_confirma_cancelamento.html",
            context={
                "titulo": "Cancelamento de Guia(s) Confirmado",
                "objeto": self,
                "log_transicao": log_transicao,
                "url": url,
            },
        )

        envia_email_em_massa_task.delay(
            assunto=f"Cancelamento Confirmado - Guias de Remessa da Requisição N° {self.numero_solicitacao}",
            emails=partes_interessadas,
            corpo="",
            html=html,
        )

    def _preenche_template_e_cria_notificacao(
        self, template_notif, titulo_notif, usuarios, link, tipo, log_transicao=None
    ):
        if usuarios:
            texto_notificacao = render_to_string(
                template_name=template_notif,
                context={
                    "solicitacao": self.numero_solicitacao,
                    "log_transicao": log_transicao,
                    "objeto": self,
                },
            )
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_REQUISICAO_DE_ENTREGA,
                    titulo=titulo_notif,
                    descricao=texto_notificacao,
                    usuario=usuario,
                    link=link,
                    requisicao=self,
                )

    def _usuarios_partes_interessadas_distribuidor(self):
        # retornar objeto de usuários ativos, vinculados ao distribuidor da requisicao
        if self.distribuidor:
            vinculos = self.distribuidor.vinculos.filter(ativo=True)

            return [vinculo.usuario for vinculo in vinculos]
        else:
            return []

    def _partes_interessadas_codae_dilog(self):
        # Envia email somente para COORDENADOR_LOGISTICA.
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=(
                "COORDENADOR_LOGISTICA",
                "COORDENADOR_CODAE_DILOG_LOGISTICA",
            ),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario.email for usuario in queryset]

    def _partes_interessadas_codae_dilog_logistica(self):
        # Envia email somente para COORDENADOR_CODAE_DILOG_LOGISTICA.
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=("COORDENADOR_CODAE_DILOG_LOGISTICA",),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario.email for usuario in queryset]

    def _usuarios_partes_interessadas_codae_dilog(self):
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=(
                "COORDENADOR_LOGISTICA",
                "COORDENADOR_CODAE_DILOG_LOGISTICA",
            ),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario for usuario in queryset]

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DILOG_ENVIA_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        self.guias.filter(status=GuiaRemessaWorkFlow.AGUARDANDO_ENVIO).update(
            status=GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO
        )
        self._envia_email_dilog_envia_solicitacao_para_distibuidor(
            log_transicao=log_transicao
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_distribuidor()
        template_notif = "logistica_notificacao_dilog_envia_solicitacao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_PENDENCIA
        titulo_notif = f"Nova Requisição de Entrega N° {self.numero_solicitacao}"
        link = f"/logistica/gestao-requisicao-entrega?numero_requisicao={self.numero_solicitacao}"
        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif, usuarios, link, tipo, log_transicao
        )

    @xworkflows.after_transition("empresa_atende")
    def _empresa_atende_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DISTRIBUIDOR_CONFIRMA_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("aguarda_confirmacao_de_cancelamento")
    def _aguarda_confirmacao_de_cancelamento_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.PAPA_AGUARDA_CONFIRMACAO_CANCELAMENTO_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )
        self._envia_email_aguarda_cancelamento_para_distibuidor(
            log_transicao=log_transicao
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_distribuidor()
        template_notif = (
            "logistica_notificacao_aguardando_cancelamento_distribuidor.html"
        )
        tipo = Notificacao.TIPO_NOTIFICACAO_PENDENCIA
        titulo_notif = self._titulo_notificacao_confirma_cancelamento()
        link = f"/logistica/gestao-requisicao-entrega?numero_requisicao={self.numero_solicitacao}"

        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif, usuarios, link, tipo, log_transicao
        )

    @xworkflows.after_transition("cancela_solicitacao")
    def _cancela_solicitacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.PAPA_CANCELA_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("distribuidor_confirma_cancelamento")
    def _distribuidor_confirma_cancelamento_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DISTRIBUIDOR_CONFIRMA_CANCELAMENTO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition(
        "distribuidor_confirma_cancelamento_envia_email_notificacao"
    )
    def _distribuidor_confirma_cancelamento_envia_email_notificacao_hook(
        self, *args, **kwargs
    ):
        log_transicao = self.log_mais_recente
        partes_interessadas = self._partes_interessadas_codae_dilog()
        self._envia_email_distribuidor_confirma_cancelamento(
            log_transicao=log_transicao, partes_interessadas=partes_interessadas
        )
        titulo_notif = self._titulo_notificacao_confirma_cancelamento()
        Notificacao.resolver_pendencia(titulo=titulo_notif, requisicao=self)

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_codae_dilog()
        template_notif = "logistica_notificacao_confirma_cancelamento_distribuidor.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
        titulo_notif_confirmada = self._titulo_notificacao_cancelamento_confirmado()
        link = f"/logistica/envio-requisicoes-entrega-completo?numero_requisicao={self.numero_solicitacao}"
        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif_confirmada, usuarios, link, tipo, log_transicao
        )

    @xworkflows.after_transition("solicita_alteracao")
    def _solicita_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DISTRIBUIDOR_SOLICITA_ALTERACAO_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("dilog_aceita_alteracao")
    def _dilog_aceita_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DILOG_ACEITA_ALTERACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("dilog_nega_alteracao")
    def _dilog_nega_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DILOG_NEGA_ALTERACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    class Meta:
        abstract = True


class FluxoSolicitacaoDeAlteracao(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = SolicitacaoDeAlteracaoWorkFlow
    status = xwf_models.StateField(workflow_class)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    def _preenche_template_e_envia_email(
        self, template, assunto, titulo, partes_interessadas, log_transicao, situacao
    ):
        html = render_to_string(
            template_name=template,
            context={
                "titulo": titulo,
                "solicitacao": self.numero_solicitacao,
                "log_transicao": log_transicao,
                "situacao": situacao,
            },
        )
        envia_email_em_massa_task.delay(
            assunto=assunto, emails=partes_interessadas, corpo="", html=html
        )

    def _partes_interessadas_dilog(self):
        # Envia email somente para COORDENADOR_LOGISTICA.
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=("COORDENADOR_LOGISTICA",),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario.email for usuario in queryset]

    def _partes_interessadas_codae_dilog(self):
        # Envia email somente para COORDENADOR_CODAE_DILOG_LOGISTICA.
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=("COORDENADOR_CODAE_DILOG_LOGISTICA",),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario.email for usuario in queryset]

    def _usuarios_partes_interessadas_codae_dilog(self):
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=(
                "COORDENADOR_LOGISTICA",
                "COORDENADOR_CODAE_DILOG_LOGISTICA",
            ),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario for usuario in queryset]

    def _preenche_template_e_cria_notificacao(
        self,
        log_transicao,
        template_notif,
        titulo_notif,
        usuarios,
        link,
        tipo,
        situacao=None,
    ):
        if usuarios:
            texto_notificacao = render_to_string(
                template_name=template_notif,
                context={
                    "solicitacao": self,
                    "log_transicao": log_transicao,
                    "situacao": situacao,
                },
            )
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_ALTERACAO_REQUISICAO_ENTREGA,
                    titulo=titulo_notif,
                    descricao=texto_notificacao,
                    usuario=usuario,
                    link=link,
                    solicitacao_alteracao=self,
                )

    def _monta_notificacao_aceita_ou_nega_solicitacao(self, situacao, log_transicao):
        usuarios = self._usuarios_partes_interessadas_distribuidor()
        template_notif = "logistica_notificacao_dilog_aceita_ou_nega_alteracao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
        titulo_notif = (
            f"Solicitação de Alteração Nº {self.numero_solicitacao} {situacao}."
        )
        link = f"/logistica/consulta-solicitacao-alteracao?numero_solicitacao={self.numero_solicitacao}"

        self._preenche_template_e_cria_notificacao(
            log_transicao, template_notif, titulo_notif, usuarios, link, tipo, situacao
        )

    def _resolve_pendencia_solicitacao_alteracao(self):
        titulo_notif = f"Solicitação de Alteração Nº {self.numero_solicitacao}"
        Notificacao.resolver_pendencia(titulo=titulo_notif, solicitacao_alteracao=self)

    def _partes_interessadas_distribuidor(self):
        # Envia email somente para vinculos do distribuidor.
        email_query_set_distribuidor = self.requisicao.distribuidor.vinculos.filter(
            ativo=True
        ).values_list("usuario__email", flat=True)

        return [email for email in email_query_set_distribuidor]

    def _usuarios_partes_interessadas_distribuidor(self):
        # retornar objeto de usuários ativos, vinculados ao distribuidor da requisicao
        if self.requisicao.distribuidor:
            vinculos = self.requisicao.distribuidor.vinculos.filter(ativo=True)

            return [vinculo.usuario for vinculo in vinculos]
        else:
            return []

    def _envia_email_distribuidor_solicita_alteracao(
        self, log_transicao, partes_interessadas
    ):
        url = f"{base_url}/logistica/gestao-solicitacao-alteracao?numero_solicitacao={self.numero_solicitacao}"
        html = render_to_string(
            template_name="logistica_distribuidor_solicita_alteracao.html",
            context={
                "titulo": "Solicitação de Alteração",
                "solicitacao": self,
                "log_transicao": log_transicao,
                "url": url,
            },
        )
        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Solicitação de Alteração N° {self.numero_solicitacao}",
            emails=partes_interessadas,
            corpo="",
            html=html,
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DISTRIBUIDOR_SOLICITA_ALTERACAO_SOLICITACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        partes_interessadas = (
            self._partes_interessadas_dilog() + self._partes_interessadas_codae_dilog()
        )
        self._envia_email_distribuidor_solicita_alteracao(
            log_transicao=log_transicao, partes_interessadas=partes_interessadas
        )
        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_codae_dilog()
        template_notif = "logistica_notificacao_distribuidor_solicita_alteracao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_PENDENCIA
        titulo_notif = f"Solicitação de Alteração Nº {self.numero_solicitacao}"
        link = f"/logistica/gestao-solicitacao-alteracao?numero_solicitacao={self.numero_solicitacao}"

        self._preenche_template_e_cria_notificacao(
            log_transicao, template_notif, titulo_notif, usuarios, link, tipo
        )

    @xworkflows.after_transition("dilog_aceita")
    def _dilog_aceita_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DILOG_ACEITA_ALTERACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )
        # Monta e-mail de aceite
        titulo = "Solicitação de Alteração Aceita"
        assunto = (
            f"[SIGPAE] Resposta à Solicitação de Alteração N° {self.numero_solicitacao}"
        )
        situacao = "ACEITA"
        template = "logistica_dilog_aceita_ou_nega_alteracao.html"
        partes_interessadas = self._partes_interessadas_distribuidor()

        self._preenche_template_e_envia_email(
            template, assunto, titulo, partes_interessadas, log_transicao, situacao
        )

        # Monta Notificacao
        self._monta_notificacao_aceita_ou_nega_solicitacao(situacao, log_transicao)

        # Resolve a pendência
        self._resolve_pendencia_solicitacao_alteracao()

    @xworkflows.after_transition("dilog_nega")
    def _dilog_nega_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.DILOG_NEGA_ALTERACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        # Monta e-mail de negação
        titulo = "Solicitação de Alteração Negada"
        assunto = (
            f"[SIGPAE] Resposta à Solicitação de Alteração N° {self.numero_solicitacao}"
        )
        situacao = "NEGADA"
        template = "logistica_dilog_aceita_ou_nega_alteracao.html"
        partes_interessadas = self._partes_interessadas_distribuidor()

        self._preenche_template_e_envia_email(
            template, assunto, titulo, partes_interessadas, log_transicao, situacao
        )

        # Monta Notificacao
        self._monta_notificacao_aceita_ou_nega_solicitacao(situacao, log_transicao)

        # Resolve a pendência
        self._resolve_pendencia_solicitacao_alteracao()

    class Meta:
        abstract = True


class FluxoGuiaRemessa(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = GuiaRemessaWorkFlow
    status = xwf_models.StateField(workflow_class)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    def _preenche_template_e_envia_email(
        self, template, assunto, titulo, partes_interessadas, log_transicao, url
    ):
        html = render_to_string(
            template_name=template,
            context={
                "titulo": titulo,
                "guia": self.numero_guia,
                "log_transicao": log_transicao,
                "url": url,
            },
        )
        envia_email_em_massa_task.delay(
            assunto=assunto, emails=partes_interessadas, corpo="", html=html
        )

    def _preenche_template_e_cria_notificacao_insucesso(
        self, template_notif, titulo_notif, usuarios, link, tipo, insucesso
    ):
        if usuarios:
            texto_notificacao = render_to_string(
                template_name=template_notif,
                context={"solicitacao": self, "insucesso": insucesso},
            )
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
                    titulo=titulo_notif,
                    descricao=texto_notificacao,
                    usuario=usuario,
                    link=link,
                    guia=self,
                )

    def _preenche_template_e_cria_notificacao(
        self, template_notif, titulo_notif, usuarios, link, tipo
    ):
        if usuarios:
            texto_notificacao = render_to_string(
                template_name=template_notif, context={"solicitacao": self, "url": link}
            )
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_GUIA_DE_REMESSA,
                    titulo=titulo_notif,
                    descricao=texto_notificacao,
                    usuario=usuario,
                    link=link,
                    guia=self,
                )

    def _resolve_pendencia_atraso_conferencia(self):
        titulo_notif = f"Registre a conferência da Guia de Remessa de alimentos! | Guia: {self.numero_guia}"
        Notificacao.resolver_pendencia(titulo=titulo_notif, guia=self)

    def _partes_interessadas_codae_dilog(self):
        # Envia email somente para COORDENADOR_CODAE_DILOG_LOGISTICA.
        queryset = Usuario.objects.filter(
            vinculos__perfil__nome__in=("COORDENADOR_CODAE_DILOG_LOGISTICA",),
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        return [usuario.email for usuario in queryset]

    def _partes_interessadas_escola(self):
        # Envia email somente para usuários ativos vinculados a escola da guia
        if self.escola and self.escola.contato:
            return [self.escola.contato.email]
        else:
            return []

    def _usuarios_partes_interessadas_escola(self):
        # retornar objeto de usuários ativos, vinculados a escola da guia
        if self.escola:
            vinculos = self.escola.vinculos.filter(ativo=True)

            return [vinculo.usuario for vinculo in vinculos]
        else:
            return []

    @xworkflows.after_transition("distribuidor_confirma_guia")
    def _distribuidor_confirma_guia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("distribuidor_confirma_guia_envia_email_e_notificacao")
    def _dispara_email_e_notificacao_de_confirmacao_ao_distribuidor_hook(
        self, *args, **kwargs
    ):
        # Monta e-mail
        url = f"{base_url}/logistica/conferir-entrega?numero_guia={self.numero_guia}"
        titulo = "Hoje tem Entrega de alimentos"
        assunto = f"[SIGPAE] Nova Guia de Remessa N° {self.numero_guia}"
        template = "logistica_distribuidor_confirma_requisicao.html"
        partes_interessadas = self._partes_interessadas_escola()

        self._preenche_template_e_envia_email(
            template, assunto, titulo, partes_interessadas, None, url
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_escola()
        template_notif = "logistica_notificacao_distribuidor_confirma_requisicao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
        titulo_notif = (
            f"Nova Guia de Remessa Nº {self.numero_guia}. "
            + "Prepare-se para receber os alimentos em sua Unidade Escolar!"
        )
        link = f"/logistica/conferir-entrega?numero_guia={self.numero_guia}"

        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif, usuarios, link, tipo
        )

    @xworkflows.after_transition("distribuidor_registra_insucesso")
    def _distribuidor_registra_insucesso_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_escola()
        template_notif = "logistica_notificacao_escola_aviso_insucesso_entrega.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
        titulo_notif = f"Insucesso de Entrega - Guia de Remessa {self.numero_guia}"
        link = f"/logistica/conferir-entrega?numero_guia={self.numero_guia}"
        insucesso = self.insucessos.last() if self.insucessos else None
        self._preenche_template_e_cria_notificacao_insucesso(
            template_notif, titulo_notif, usuarios, link, tipo, insucesso
        )

    @xworkflows.after_transition("escola_recebe")
    def _escola_recebe_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("escola_nao_recebe")
    def _escola_nao_recebe_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        # Monta e-mail
        url = f"{base_url}/logistica/conferir-entrega"
        titulo = "Reposição de alimentos Não Recebidos"
        assunto = "[SIGPAE] Prepare-se para uma possível reposição dos alimentos não recebidos!"
        template = "logistica_escola_aviso_reposicao.html"
        partes_interessadas = (
            self._partes_interessadas_escola() + self._partes_interessadas_codae_dilog()
        )

        self._preenche_template_e_envia_email(
            template, assunto, titulo, partes_interessadas, log_transicao, url
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_escola()
        template_notif = "logistica_notificacao_escola_aviso_reposicao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
        titulo_notif = f"Prepare-se para receber a Reposição de Alimentos da Guia de Remessa Nº {self.numero_guia}"
        link = f"/logistica/conferir-entrega?numero_guia={self.numero_guia}"

        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif, usuarios, link, tipo
        )

    @xworkflows.after_transition("escola_recebe_parcial")
    def _escola_recebe_parcial_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

        # Monta e-mail
        url = f"{base_url}/logistica/conferir-entrega"
        titulo = "Reposição de alimentos Não Recebidos"
        assunto = "[SIGPAE] Prepare-se para uma possível reposição dos alimentos não recebidos!"
        template = "logistica_escola_aviso_reposicao.html"
        partes_interessadas = self._partes_interessadas_escola()

        self._preenche_template_e_envia_email(
            template, assunto, titulo, partes_interessadas, log_transicao, url
        )

        # Monta Notificacao
        usuarios = self._usuarios_partes_interessadas_escola()
        template_notif = "logistica_notificacao_escola_aviso_reposicao.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
        titulo_notif = f"Prepare-se para receber a Reposição de Alimentos da Guia de Remessa Nº {self.numero_guia}"
        link = f"/logistica/conferir-entrega?numero_guia={self.numero_guia}"

        self._preenche_template_e_cria_notificacao(
            template_notif, titulo_notif, usuarios, link, tipo
        )

    @xworkflows.after_transition("escola_recebe_parcial_atraso")
    def _escola_recebe_parcial_atraso_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("reposicao_parcial")
    def _reposicao_parcial_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("reposicao_total")
    def _reposicao_total_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ABASTECIMENTO_GUIA_DE_REMESSA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    class Meta:
        abstract = True


class FluxoHomologacaoProduto(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = HomologacaoProdutoWorkflow
    status = xwf_models.StateField(workflow_class)
    DIAS_PARA_CANCELAR = 2

    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        self.rastro_terceirizada = (
            self.criado_por.vinculos.filter(data_inicial__lte=self.criado_em)
            .last()
            .instituicao
        )
        self.save()

    @property
    def pode_excluir(self):
        return self.status == self.workflow_class.RASCUNHO

    @property
    def template_mensagem(self):
        raise NotImplementedError(
            "Deve criar um property que recupera o assunto e corpo mensagem desse objeto"
        )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    #
    # Esses hooks são chamados automaticamente após a
    # transition do status ser chamada.
    # Ex. >>> alimentacao_continua.inicia_fluxo(param1, param2, key1='val')
    #

    def _preenche_template_e_envia_email(
        self, assunto, titulo, user, partes_interessadas
    ):
        template = "fluxo_autorizar_negar_cancelar.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "movimentacao_realizada": str(self.status),
            "perfil_que_autorizou": user.nome,
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_autorizar_negar_cancelar.html",
            dados_template={
                "titulo": titulo,
                "tipo_solicitacao": self.DESCRICAO,
                "movimentacao_realizada": str(self.status),
                "perfil_que_autorizou": user.nome,
            },
            html=html,
        )

    def _partes_interessadas_codae_homologa_ou_nao_homologa(self):
        # Envia email somente para ESCOLAS selecionadas
        escolas_ids = m.Escola.objects.filter(
            enviar_email_por_produto=True
        ).values_list("id", flat=True)

        content_type = ContentType.objects.get_for_model(m.Escola)

        usuarios_escolas_selecionadas = (
            Usuario.objects.filter(
                vinculos__object_id__in=escolas_ids,
                vinculos__content_type=content_type,
                vinculos__ativo=True,
            )
            .values_list("email", flat=True)
            .distinct()
        )

        usuarios_terceirizada = self.rastro_terceirizada.todos_emails_por_modulo(
            "Gestão de Produto"
        )
        if self.status == self.workflow_class.CODAE_NAO_HOMOLOGADO:
            usuarios_terceirizada = self.rastro_terceirizada.emails_por_modulo(
                "Gestão de Produto"
            )

        return list(usuarios_escolas_selecionadas) + usuarios_terceirizada

    def _envia_email_codae_homologa(self, log_transicao, link_pdf):
        html = render_to_string(
            template_name="produto_codae_homologa.html",
            context={
                "titulo": "Produto Homologado com sucesso",
                "produto": self.produto,
                "log_transicao": log_transicao,
                "link_pdf": link_pdf,
            },
        )
        envia_email_em_massa_task.delay(
            assunto="Produto Homologado com sucesso",
            emails=self._partes_interessadas_codae_homologa_ou_nao_homologa(),
            corpo="",
            html=html,
        )

    def _envia_email_codae_nao_homologa(self, log_transicao, link_pdf):
        html = render_to_string(
            template_name="produto_codae_nao_homologa.html",
            context={
                "titulo": "Produto não homologado",
                "produto": self.produto,
                "log_transicao": log_transicao,
                "link_pdf": link_pdf,
            },
        )
        envia_email_em_massa_task.delay(
            assunto="Produto não homologado",
            emails=self._partes_interessadas_codae_homologa_ou_nao_homologa(),
            corpo="",
            html=html,
        )

    def _partes_interessadas_codae_questiona(self):
        emails = [self.produto.criado_por.email]
        emails += self.rastro_terceirizada.emails_por_modulo("Gestão de Produto")
        return list(set(emails))

    def _envia_email_codae_questiona(self, log_transicao, link_pdf):
        html = render_to_string(
            template_name="produto_codae_questiona.html",
            context={
                "titulo": "Produto Cadastrado Exige Correção",
                "produto": self.produto,
                "log_transicao": log_transicao,
                "link_pdf": link_pdf,
            },
        )
        envia_email_em_massa_task.delay(
            assunto="Produto Cadastrado Exige Correção",
            emails=self._partes_interessadas_codae_questiona(),
            corpo="",
            html=html,
        )

    def _envia_email_escola_ou_nutricionista_reclamou(self, reclamacao):
        html = render_to_string(
            template_name="produto_escola_ou_nutricionista_reclamou.html",
            context={
                "titulo": "Nova reclamação de produto",
                "produto": self.produto,
                "reclamacao": reclamacao,
            },
        )
        partes_interessadas = Usuario.objects.filter(
            vinculos__perfil__nome__in=[
                "COORDENADOR_GESTAO_PRODUTO",
                "ADMINISTRADOR_GESTAO_PRODUTO",
            ],
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
        )
        envia_email_em_massa_task.delay(
            assunto="Nova reclamação de produto requer análise",
            emails=[usuario.email for usuario in partes_interessadas],
            corpo="",
            html=html,
        )

    def _partes_interessadas_codae_pede_analise_sensorial(self):
        return self.rastro_terceirizada.emails_por_modulo("Gestão de Produto")

    def _envia_email_codae_pede_analise_sensorial(self, log_transicao, link_pdf):
        html = render_to_string(
            template_name="produto_codae_pede_analise_sensorial.html",
            context={
                "titulo": "Solicitação de Análise Sensorial",
                "produto": self.produto,
                "protocolo": self.protocolo_analise_sensorial,
                "log_transicao": log_transicao,
                "link_pdf": link_pdf,
            },
        )
        envia_email_em_massa_task.delay(
            assunto="[SIGPAE] Solicitação de Análise Sensorial",
            emails=self._partes_interessadas_codae_pede_analise_sensorial(),
            corpo="",
            html=html,
        )

    def _partes_interessadas_codae_ativa_ou_suspende(self):
        return self.rastro_terceirizada.todos_emails_por_modulo("Gestão de Produto")

    def _envia_email_codae_ativa_ou_suspende(
        self, log_transicao, template_name, assunto
    ):
        html = render_to_string(
            template_name=template_name,
            context={
                "produto": self.produto,
                "log_transicao": log_transicao,
            },
        )
        emails = self._partes_interessadas_codae_ativa_ou_suspende()
        envia_email_em_massa_task.delay(
            assunto=assunto, emails=emails, corpo="", html=html
        )

    def _envia_email_codae_questiona_produto(
        self, reclamacao, log_transicao, emails, link
    ):
        html = render_to_string(
            template_name="codae_questiona_reclamacao.html",
            context={
                "produto": self.produto,
                "reclamacao": reclamacao,
                "marca": self.produto.marca,
                "criado_em": log_transicao.criado_em.strftime("%d/%m/%Y - %H:%M"),
                "log_transicao": log_transicao,
                "link_questionamento": link,
            },
        )

        envia_email_em_massa_task.delay(
            assunto="Questionamento da CODAE", emails=emails, corpo="", html=html
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        if not self.rastro_terceirizada:
            self._salva_rastro_solicitacao()
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("codae_homologa")
    def _codae_homologa_hook(self, *args, **kwargs):
        user = kwargs["user"]
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO, usuario=user
        )
        for anexo in kwargs.get("anexos", []):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )
        if not kwargs.get("nao_enviar_email", False):
            self._envia_email_codae_homologa(
                log_transicao=log_transicao, link_pdf=kwargs["link_pdf"]
            )

    @xworkflows.after_transition("codae_recusou_reclamacao")
    def _codae_recusou_reclamacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")

        if kwargs.get("suspensao_parcial"):
            self.salva_log_com_justificativa_e_anexos(
                LogSolicitacoesUsuario.SUSPENSO_EM_ALGUNS_EDITAIS,
                kwargs["request"],
                justificativa,
            )
        else:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO,
                justificativa=justificativa,
                usuario=user,
            )

    @xworkflows.after_transition("terceirizada_inativa")
    def _inativa_homologacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INATIVA, usuario=user
        )

    @xworkflows.after_transition("codae_nao_homologa")
    def _codae_nao_homologa_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_NAO_HOMOLOGADO,
            usuario=user,
            justificativa=justificativa,
        )
        self._envia_email_codae_nao_homologa(log_transicao, kwargs["link_pdf"])

    @xworkflows.after_transition("codae_questiona")
    def _codae_questiona_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
            usuario=user,
            justificativa=justificativa,
        )
        self._envia_email_codae_questiona(log_transicao, link_pdf=kwargs["link_pdf"])

    @xworkflows.after_transition("codae_pede_analise_sensorial")
    def _codae_pede_analise_sensorial_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
            usuario=user,
            justificativa=justificativa,
        )
        self._envia_email_codae_pede_analise_sensorial(
            log_transicao=log_transicao, link_pdf=kwargs["link_pdf"]
        )

    @xworkflows.after_transition("codae_cancela_analise_sensorial")
    def _codae_cancela_analise_sensorial_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_CANCELOU_ANALISE_SENSORIAL,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("terceirizada_cancelou_solicitacao_homologacao")
    def _terceirizada_cancelou_solicitacao_homologacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("terceirizada_responde_analise_sensorial")
    def _terceirizada_responde_analise_sensorial_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            usuario=user,
            justificativa=justificativa,
        )
        for anexo in kwargs.get("anexos", []):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )

    @xworkflows.after_transition(
        "terceirizada_responde_analise_sensorial_da_reclamacao"
    )
    def _terceirizada_responde_analise_sensorial_da_reclamacao_hook(
        self, *args, **kwargs
    ):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("terceirizada_responde_analise_sensorial_homologado")
    def _terceirizada_responde_analise_sensorial_homologado_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("codae_pediu_analise_reclamacao")
    def _codae_pediu_analise_reclamacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        reclamacao = kwargs.get("reclamacao", None)
        justificativa = kwargs.get("justificativa", "")
        link = (
            f"{base_url}/gestao-produto/responder-reclamacao/consulta?uuid={self.uuid}"
        )
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_RECLAMACAO,
            usuario=user,
            justificativa=justificativa,
        )
        for anexo in kwargs.get("anexos"):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )
        if reclamacao:
            emails = reclamacao.escola.lote.terceirizada.emails_por_modulo(
                "Gestão de Produto"
            )
            self._envia_email_codae_questiona_produto(
                reclamacao, log_transicao, emails, link
            )

    @xworkflows.after_transition("codae_questiona_nutrisupervisor")
    def _codae_questiona_nutrisupervisor_hook(self, *args, **kwargs):
        user = kwargs["user"]
        reclamacao = kwargs.get("reclamacao", None)
        justificativa = kwargs.get("justificativa", "")
        link = f"{base_url}/gestao-produto/responder-questionamento-nutrisupervisor/?nome_produto={self.produto.nome}"
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            usuario=user,
            justificativa=justificativa,
        )
        for anexo in kwargs.get("anexos"):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )
        if reclamacao:
            emails = [reclamacao.criado_por.email]
            self._envia_email_codae_questiona_produto(
                reclamacao, log_transicao, emails, link
            )

    @xworkflows.after_transition("codae_questiona_ue")
    def _codae_questiona_ue_hook(self, *args, **kwargs):
        user = kwargs["user"]
        reclamacao = kwargs.get("reclamacao", None)
        justificativa = kwargs.get("justificativa", "")
        link = f"{base_url}/gestao-produto/responder-questionamento-ue/?nome_produto={self.produto.nome}"
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU_UE,
            usuario=user,
            justificativa=justificativa,
        )
        for anexo in kwargs.get("anexos"):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )
        if reclamacao:
            emails = [reclamacao.criado_por.email, reclamacao.escola.contato.email]
            self._envia_email_codae_questiona_produto(
                reclamacao, log_transicao, emails, link
            )

    @xworkflows.after_transition("codae_autorizou_reclamacao")
    def _codae_autorizou_reclamacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        log_transicao = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO,
            usuario=user,
            justificativa=justificativa,
        )
        for anexo in kwargs.get("anexos"):
            arquivo = convert_base64_to_contentfile(anexo.get("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )

    @xworkflows.after_transition("escola_ou_nutricionista_reclamou")
    def _escola_ou_nutricionista_reclamou_hook(self, *args, **kwargs):
        user = kwargs["user"]
        reclamacao = kwargs["reclamacao"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            usuario=user,
            justificativa=reclamacao["reclamacao"],
        )
        if not kwargs.get("nao_enviar_email", None):
            self._envia_email_escola_ou_nutricionista_reclamou(reclamacao)

    def salva_log_com_justificativa_e_anexos(
        self, evento, request, justificativa_suspensao_ativacao=None
    ):
        justificativa_ = justificativa_suspensao_ativacao
        log_transicao = self.salvar_log_transicao(
            status_evento=evento,
            usuario=request.user,
            justificativa=(
                justificativa_ if justificativa_ else request.data["justificativa"]
            ),
        )
        for anexo in request.data.pop("anexos", []):
            arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
            AnexoLogSolicitacoesUsuario.objects.create(
                log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
            )
        return log_transicao

    @xworkflows.after_transition("codae_suspende")
    def _codae_suspende_hook(self, *args, **kwargs):
        log_suspensao = self.salva_log_com_justificativa_e_anexos(
            LogSolicitacoesUsuario.CODAE_SUSPENDEU, kwargs["request"]
        )
        self._envia_email_codae_ativa_ou_suspende(
            log_suspensao,
            template_name="produto_codae_suspende.html",
            assunto="[SIGPAE] Suspensão de Produto",
        )

    @xworkflows.after_transition("codae_ativa")
    def _codae_ativa_hook(self, *args, **kwargs):
        log_ativacao = self.salva_log_com_justificativa_e_anexos(
            LogSolicitacoesUsuario.CODAE_HOMOLOGADO, kwargs["request"]
        )
        self._envia_email_codae_ativa_ou_suspende(
            log_ativacao,
            template_name="produto_codae_ativa.html",
            assunto="[SIGPAE] Ativação de Produto",
        )

    @xworkflows.after_transition("terceirizada_responde_reclamacao")
    def _terceirizada_responde_reclamacao_hook(self, *args, **kwargs):
        self.salva_log_com_justificativa_e_anexos(
            LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            kwargs["request"],
        )

    @xworkflows.after_transition("ue_respondeu_questionamento")
    def _ue_respondeu_questionamento_hook(self, *args, **kwargs):
        self.salva_log_com_justificativa_e_anexos(
            LogSolicitacoesUsuario.UE_RESPONDEU_RECLAMACAO, kwargs["request"]
        )

    @xworkflows.after_transition("nutrisupervisor_respondeu_questionamento")
    def _nutrisupervisor_respondeu_questionamento_hook(self, *args, **kwargs):
        self.salva_log_com_justificativa_e_anexos(
            LogSolicitacoesUsuario.NUTRISUPERVISOR_RESPONDEU_RECLAMACAO,
            kwargs["request"],
        )

    @xworkflows.after_transition("codae_cancela_solicitacao_correcao")
    def _codae_cancela_solicitacao_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = f"<p>{self.produto.nome}</p>"
        justificativa += "<br><p>Justificativa:</p>"
        justificativa += kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_CANCELOU_SOLICITACAO_CORRECAO,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("terceirizada_cancela_solicitacao_correcao")
    def _terceirizada_cancela_solicitacao_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = f"<p>{self.produto.nome}</p>"
        justificativa += "<br><p>Justificativa:</p>"
        justificativa += kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_CANCELOU_SOLICITACAO_CORRECAO,
            usuario=user,
            justificativa=justificativa,
        )

    class Meta:
        abstract = True


class FluxoAprovacaoPartindoDaEscola(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = PedidoAPartirDaEscolaWorkflow
    status = xwf_models.StateField(workflow_class)
    DIAS_UTEIS_PARA_CANCELAR = 2

    rastro_escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_escola",
        editable=False,
    )
    rastro_dre = models.ForeignKey(
        "escola.DiretoriaRegional",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="%(app_label)s_%(class)s_rastro_dre",
        blank=True,
        editable=False,
    )
    rastro_lote = models.ForeignKey(
        "escola.Lote",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_lote",
        editable=False,
    )
    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        self.rastro_escola = self.escola
        self.rastro_dre = self.escola.diretoria_regional
        self.rastro_lote = self.escola.lote
        self.rastro_terceirizada = self.escola.lote.terceirizada
        self.save()

    def eh_alteracao_lanche_emergencial(self):
        from ..cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
        from ..cardapio.alteracao_tipo_alimentacao_cemei.models import (
            AlteracaoCardapioCEMEI,
        )

        return (
            (isinstance(self, (AlteracaoCardapio, AlteracaoCardapioCEMEI)))
            and self.motivo
            and self.motivo.nome == "Lanche Emergencial"
        )

    def get_dias_suspensao(self):
        from sme_sigpae_api.escola.models import DiaSuspensaoAtividades

        dias_suspensao = DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
            self.escola, self.DIAS_UTEIS_PARA_CANCELAR
        )
        return dias_suspensao

    def checa_se_pode_cancelar(self, data_do_evento=None):
        if self.eh_alteracao_lanche_emergencial():
            return
        dias_suspensao = self.get_dias_suspensao()
        if not data_do_evento:
            data_do_evento = self.data
            if isinstance(data_do_evento, datetime.datetime):
                data_do_evento = data_do_evento.date()
        data_minima_cancelamento = obter_dias_uteis_apos(
            datetime.date.today(), self.DIAS_UTEIS_PARA_CANCELAR + dias_suspensao
        )
        if data_minima_cancelamento >= data_do_evento:
            raise xworkflows.InvalidTransitionError(
                f"Só pode cancelar com no mínimo {self.DIAS_UTEIS_PARA_CANCELAR} dia(s) úteis de antecedência"
            )

    def cancelar_pedido(self, user, justificativa):
        """O objeto que herdar de FluxoAprovacaoPartindoDaEscola, deve ter um property data.

        Dado dias de antecedencia de prazo, verifica se pode e altera o estado
        """
        if self.status == self.workflow_class.ESCOLA_CANCELOU:
            raise xworkflows.InvalidTransitionError("Solicitação já está cancelada")

        self.checa_se_pode_cancelar()

        self.status = self.workflow_class.ESCOLA_CANCELOU
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
            usuario=user,
            justificativa=justificativa,
        )
        self.save()
        # envia email para partes interessadas
        id_externo = "#" + self.id_externo
        assunto = "[SIGPAE] Status de solicitação - " + id_externo
        titulo = f"Solicitação de {self.tipo} Cancelada"
        log_criado = self.logs.last().criado_em
        criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
        self._preenche_template_e_envia_email_ue_cancela(
            assunto, titulo, id_externo, criado_em, self._partes_interessadas_ue_cancela
        )

    @property
    def pode_excluir(self):
        return self.status == self.workflow_class.RASCUNHO

    @property
    def ta_na_dre(self):
        return self.status == self.workflow_class.DRE_A_VALIDAR

    @property
    def ta_na_escola(self):
        return self.status in [
            self.workflow_class.RASCUNHO,
            self.workflow_class.DRE_PEDIU_ESCOLA_REVISAR,
        ]

    @property
    def ta_na_codae(self):
        return self.status == self.workflow_class.DRE_VALIDADO

    @property
    def ta_na_terceirizada(self):
        return self.status == self.workflow_class.CODAE_AUTORIZADO

    @property
    def _partes_interessadas_inicio_fluxo(self):
        """Quando a escola faz a solicitação, as pessoas da DRE são as partes interessadas.

        Será retornada uma lista de emails para envio via celery.
        """
        email_query_set = self.rastro_dre.vinculos.filter(ativo=True).values_list(
            "usuario__email", flat=False
        )
        return [email for email in email_query_set]

    @property
    def _partes_interessadas_ue_cancela(self):
        email_query_set_terceirizada = (
            self.escola.lote.terceirizada.emails_terceirizadas.filter(
                modulo__nome="Gestão de Alimentação"
            ).values_list("email", flat=True)
        )
        return list(email_query_set_terceirizada)

    @property
    def _partes_interessadas_dre_nao_valida(self):
        # Quando DRE nega apenas o contato da escola recebe email
        return [self.rastro_escola.contato.email]

    @property
    def _partes_interessadas_codae_nega(self):
        # Quando CODAE nega apenas o contato da escola recebe email
        return [self.rastro_escola.contato.email]

    @property
    def _partes_interessadas_codae_autoriza(self):
        email_escola_lista = [self.rastro_escola.contato.email]
        email_query_set_terceirizada = (
            self.rastro_escola.lote.terceirizada.emails_terceirizadas.filter(
                modulo__nome="Gestão de Alimentação"
            ).values_list("email", flat=True)
        )
        return email_escola_lista + list(email_query_set_terceirizada)

    @property
    def partes_interessadas_terceirizadas_tomou_ciencia(self):
        # TODO: definir partes interessadas
        return []

    @property
    def template_mensagem(self):
        raise NotImplementedError(
            "Deve criar um property que recupera o assunto e corpo mensagem desse objeto"
        )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    #
    # Esses hooks são chamados automaticamente após a
    # transition do status ser chamada.
    # Ex. >>> alimentacao_continua.inicia_fluxo(param1, param2, key1='val')
    #

    def _preenche_template_e_envia_email_dre_nega(
        self, assunto, titulo, id_externo, criado_em, partes_interessadas
    ):
        url = f'{env("REACT_APP_URL")}/{self.path}'
        template = "fluxo_dre_nega.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "id_externo": id_externo,
            "criado_em": criado_em,
            "nome_ue": self.rastro_escola.nome,
            "url": url,
            "nome_dre": self.escola.diretoria_regional.nome,
            "nome_lote": self.escola.lote.nome,
            "movimentacao_realizada": str(self.status),
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_dre_nega.html",
            dados_template=dados_template,
            html=html,
        )

    def _preenche_template_e_envia_email_ue_cancela(
        self, assunto, titulo, id_externo, criado_em, partes_interessadas
    ):
        url = f'{env("REACT_APP_URL")}/{self.path}'
        template = "fluxo_ue_cancela.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "id_externo": id_externo,
            "criado_em": criado_em,
            "nome_ue": self.rastro_escola.nome,
            "url": url,
            "nome_dre": self.escola.diretoria_regional.nome,
            "nome_lote": self.escola.lote.nome,
            "movimentacao_realizada": str(self.status),
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_ue_cancela.html",
            dados_template=dados_template,
            html=html,
        )

    def _preenche_template_e_envia_email_codae_autoriza_ou_nega(
        self, assunto, titulo, id_externo, criado_em, partes_interessadas
    ):
        url = f'{env("REACT_APP_URL")}/{self.path}'
        template = "fluxo_codae_autoriza_ou_nega.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "id_externo": id_externo,
            "criado_em": criado_em,
            "nome_ue": self.rastro_escola.nome,
            "url": url,
            "nome_dre": self.escola.diretoria_regional.nome,
            "nome_lote": self.escola.lote.nome,
            "movimentacao_realizada": str(self.status),
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_codae_autoriza_ou_nega.html",
            dados_template=dados_template,
            html=html,
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        self.foi_solicitado_fora_do_prazo = self.prioridade in ["PRIORITARIO", "LIMITE"]
        self._salva_rastro_solicitacao()
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO, usuario=user
        )

    @xworkflows.after_transition("dre_valida")
    def _dre_valida_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DRE_VALIDOU, usuario=user
            )

    @xworkflows.after_transition("dre_pede_revisao")
    def _dre_pede_revisao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DRE_PEDIU_REVISAO, usuario=user
            )

    @xworkflows.after_transition("dre_nao_valida")
    def _dre_nao_valida_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        # manda email pra escola que solicitou de que a solicitacao NAO foi
        # validada
        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - " + id_externo
            titulo = f"Solicitação de {self.tipo} Não Validada"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
                justificativa=justificativa,
                usuario=user,
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            self._preenche_template_e_envia_email_dre_nega(
                assunto,
                titulo,
                id_externo,
                criado_em,
                self._partes_interessadas_dre_nao_valida,
            )

    @xworkflows.after_transition("escola_revisa")
    def _escola_revisa_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.ESCOLA_REVISOU, usuario=user
            )

    @xworkflows.after_transition("codae_questiona")
    def _codae_questiona_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
                justificativa=justificativa,
                usuario=user,
            )

    @xworkflows.before_transition("codae_autoriza_questionamento")
    @xworkflows.before_transition("codae_autoriza")
    def _codae_autoriza_hook_antes(self, *args, **kwargs):
        from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
            AlteracaoCardapio,
        )
        from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
            AlteracaoCardapioCEMEI,
        )

        if (
            self.foi_solicitado_fora_do_prazo
            and self.status
            != PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
        ):
            if (
                isinstance(self, (AlteracaoCardapio, AlteracaoCardapioCEMEI))
                and self.motivo.nome == "Lanche Emergencial"
            ):
                return
            raise xworkflows.InvalidTransitionError(
                "CODAE não pode autorizar direto caso seja em cima da hora, deve questionar"
            )

    @xworkflows.after_transition("codae_autoriza_questionamento")
    @xworkflows.after_transition("codae_autoriza")
    def _codae_autoriza_hook(self, *args, **kwargs):
        # manda email para escola que solicitou e para os emails do módulo Gestão de Alimentação da
        # terceirizada responsável
        # a solicitacao foi autorizada
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - " + id_externo
            titulo = f"Solicitação de {self.tipo} Autorizada"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
                usuario=user,
                justificativa=justificativa,
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            self._preenche_template_e_envia_email_codae_autoriza_ou_nega(
                assunto,
                titulo,
                id_externo,
                criado_em,
                self._partes_interessadas_codae_autoriza,
            )

    @xworkflows.after_transition("codae_nega_questionamento")
    @xworkflows.after_transition("codae_nega")
    def _codae_recusou_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        # manda email pra escola que solicitou e a DRE dela que validou de que
        # a solicitacao NAO foi autorizada
        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - " + id_externo
            titulo = f"Solicitação de {self.tipo} Negada"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
                usuario=user,
                justificativa=justificativa,
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            self._preenche_template_e_envia_email_codae_autoriza_ou_nega(
                assunto,
                titulo,
                id_externo,
                criado_em,
                self._partes_interessadas_codae_nega,
            )

    @xworkflows.after_transition("terceirizada_toma_ciencia")
    def _terceirizada_toma_ciencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
                usuario=user,
            )

    @xworkflows.after_transition("terceirizada_responde_questionamento")
    def _terceirizada_responde_questionamento_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                justificativa=justificativa,
                resposta_sim_nao=resposta_sim_nao,
                usuario=user,
            )

    class Meta:
        abstract = True


class FluxoAprovacaoPartindoDaDiretoriaRegional(
    xwf_models.WorkflowEnabled, models.Model
):
    workflow_class = PedidoAPartirDaDiretoriaRegionalWorkflow
    status = xwf_models.StateField(workflow_class)
    DIAS_UTEIS_PARA_CANCELAR = 2

    rastro_escolas = models.ManyToManyField(
        "escola.Escola",
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_escola",
        editable=False,
    )
    rastro_dre = models.ForeignKey(
        "escola.DiretoriaRegional",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="%(app_label)s_%(class)s_rastro_dre",
        blank=True,
        editable=False,
    )
    rastro_lote = models.ForeignKey(
        "escola.Lote",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_lote",
        editable=False,
    )
    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        escolas = [i.escola for i in self.escolas_quantidades.all()]
        self.rastro_escolas.set(escolas)
        self.rastro_dre = self.diretoria_regional
        self.rastro_lote = self.lote
        self.rastro_terceirizada = self.lote.terceirizada
        self.save()

    def get_dias_suspensao(self):
        from sme_sigpae_api.escola.models import DiaSuspensaoAtividades

        dias_suspensao = (
            DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                self.diretoria_regional, self.DIAS_UTEIS_PARA_CANCELAR
            )
        )
        return dias_suspensao

    def checa_se_pode_cancelar(self, data_do_evento=None):
        dias_suspensao = self.get_dias_suspensao()
        if not data_do_evento:
            data_do_evento = self.data
            if isinstance(data_do_evento, datetime.datetime):
                data_do_evento = data_do_evento.date()
        data_minima_cancelamento = obter_dias_uteis_apos(
            datetime.date.today(), self.DIAS_UTEIS_PARA_CANCELAR + dias_suspensao
        )
        if data_minima_cancelamento >= data_do_evento:
            raise xworkflows.InvalidTransitionError(
                f"Só pode cancelar com no mínimo {self.DIAS_UTEIS_PARA_CANCELAR} dia(s) úteis de antecedência"
            )

    def cancelar_pedido(self, user, justificativa=""):
        """O objeto que herdar de FluxoAprovacaoPartindoDaDiretoriaRegional, deve ter um property data.

        Atualmente o único pedido da DRE é o Solicitação kit lanche unificada
        Dado dias de antecedencia de prazo, verifica se pode e altera o estado
        """
        if self.status == self.workflow_class.DRE_CANCELOU:
            raise xworkflows.InvalidTransitionError("Solicitação já está cancelada")

        self.checa_se_pode_cancelar()

        self.status = self.workflow_class.DRE_CANCELOU
        status_ev = LogSolicitacoesUsuario.DRE_CANCELOU
        if isinstance(user.vinculo_atual.instituicao, m.Escola):
            status_ev = LogSolicitacoesUsuario.ESCOLA_CANCELOU
        self.salvar_log_transicao(
            status_evento=status_ev, usuario=user, justificativa=justificativa
        )
        self.save()
        # envia email para partes interessadas
        assunto = "[SIGPAE] Status de solicitação - #" + self.id_externo
        titulo = "Status de solicitação - #" + self.id_externo
        self._preenche_template_e_envia_email(
            assunto, titulo, user, self._partes_interessadas_cancelamento
        )

    @property
    def pode_excluir(self):
        return self.status == self.workflow_class.RASCUNHO

    @property
    def ta_na_dre(self):
        return self.status in [
            self.workflow_class.CODAE_PEDIU_DRE_REVISAR,
            self.workflow_class.RASCUNHO,
        ]

    @property
    def ta_na_codae(self):
        return self.status == self.workflow_class.CODAE_A_AUTORIZAR

    @property
    def ta_na_terceirizada(self):
        return self.status == self.workflow_class.CODAE_AUTORIZADO

    @property
    def _partes_interessadas_cancelamento(self):
        return []

    @staticmethod
    def _partes_interessadas_codae_nega(escola):
        return [escola.contato.email]

    @staticmethod
    def _partes_interessadas_codae_autoriza(escola):
        email_escola = [escola.contato.email]
        email_query_set_terceirizada = (
            escola.lote.terceirizada.emails_terceirizadas.filter(
                modulo__nome="Gestão de Alimentação"
            ).values_list("email", flat=True)
        )
        return email_escola + list(email_query_set_terceirizada)

    @property
    def partes_interessadas_inicio_fluxo(self):
        # TODO: definir partes interessadas
        return []

    @property
    def partes_interessadas_terceirizadas_tomou_ciencia(self):
        # TODO: definir partes interessadas
        return []

    @property
    def template_mensagem(self):
        raise NotImplementedError(
            "Deve criar um property que recupera o assunto e corpo mensagem desse objeto"
        )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        raise NotImplementedError("Deve criar um método salvar_log_transicao")

    def _preenche_template_e_envia_email(
        self, assunto, titulo, user, partes_interessadas
    ):
        template = "fluxo_autorizar_negar_cancelar.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "movimentacao_realizada": str(self.status),
            "perfil_que_autorizou": user.nome,
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_autorizar_negar_cancelar.html",
            dados_template={
                "titulo": titulo,
                "tipo_solicitacao": self.DESCRICAO,
                "movimentacao_realizada": str(self.status),
                "perfil_que_autorizou": user.nome,
            },
            html=html,
        )

    def _preenche_template_e_envia_email_codae_autoriza_ou_nega(
        self, assunto, titulo, id_externo, user, criado_em, partes_interessadas, escola
    ):
        url = f'{env("REACT_APP_URL")}/{self.path}'
        template = "fluxo_dre_solicita_e_codae_autoriza_ou_nega.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "id_externo": id_externo,
            "criado_em": criado_em,
            "nome_ue": escola.nome,
            "url": url,
            "nome_dre": self.rastro_dre.nome,
            "nome_lote": escola.lote.nome,
            "movimentacao_realizada": str(self.status),
        }
        html = render_to_string(template, dados_template)

        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_dre_solicita_e_codae_autoriza_ou_nega.html",
            dados_template=dados_template,
            html=html,
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        self.foi_solicitado_fora_do_prazo = self.prioridade in ["PRIORITARIO", "LIMITE"]
        user = kwargs["user"]

        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO, usuario=user
        )
        self._salva_rastro_solicitacao()

    @xworkflows.after_transition("codae_autoriza_questionamento")
    @xworkflows.after_transition("codae_autoriza")
    def _codae_autoriza_hook(self, *args, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        user = kwargs["user"]
        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - #" + self.id_externo
            titulo = f"Solicitação de {self.tipo} Autorizada"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
                usuario=user,
                justificativa=justificativa,
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            escolas = [eq.escola for eq in self.escolas_quantidades.all()]
            for escola in escolas:
                self._preenche_template_e_envia_email_codae_autoriza_ou_nega(
                    assunto,
                    titulo,
                    id_externo,
                    user,
                    criado_em,
                    self._partes_interessadas_codae_autoriza(escola),
                    escola,
                )

    @xworkflows.after_transition("codae_questiona")
    def _codae_questiona_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
                justificativa=justificativa,
                usuario=user,
            )

    @xworkflows.after_transition("terceirizada_toma_ciencia")
    def _terceirizada_toma_ciencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
                usuario=user,
            )

    @xworkflows.after_transition("terceirizada_responde_questionamento")
    def _terceirizada_responde_questionamento_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                justificativa=justificativa,
                resposta_sim_nao=resposta_sim_nao,
                usuario=user,
            )

    @xworkflows.after_transition("codae_nega_questionamento")
    @xworkflows.after_transition("codae_nega")
    def _codae_recusou_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - #" + self.id_externo
            titulo = f"Solicitação de {self.tipo} Negada"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
                usuario=user,
                justificativa=justificativa,
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            escolas = [eq.escola for eq in self.escolas_quantidades.all()]
            for escola in escolas:
                self._preenche_template_e_envia_email_codae_autoriza_ou_nega(
                    assunto,
                    titulo,
                    id_externo,
                    user,
                    criado_em,
                    self._partes_interessadas_codae_nega(escola),
                    escola,
                )

    class Meta:
        abstract = True


class FluxoInformativoPartindoDaEscola(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = InformativoPartindoDaEscolaWorkflow
    status = xwf_models.StateField(workflow_class)
    DIAS_UTEIS_PARA_CANCELAR = 2

    rastro_escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_escola",
        editable=False,
    )
    rastro_dre = models.ForeignKey(
        "escola.DiretoriaRegional",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="%(app_label)s_%(class)s_rastro_dre",
        blank=True,
        editable=False,
    )
    rastro_lote = models.ForeignKey(
        "escola.Lote",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_lote",
        editable=False,
    )
    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        self.rastro_escola = self.escola
        self.rastro_dre = self.escola.diretoria_regional
        self.rastro_lote = self.escola.lote
        self.rastro_terceirizada = self.escola.lote.terceirizada
        self.save()

    @property
    def pode_excluir(self):
        return self.status == self.workflow_class.RASCUNHO

    @property
    def partes_interessadas_informacao(self):
        email_query_set_terceirizada = (
            self.escola.lote.terceirizada.emails_terceirizadas.filter(
                modulo__nome="Gestão de Alimentação"
            ).values_list("email", flat=True)
        )
        return list(email_query_set_terceirizada)

    @property
    def partes_interessadas_terceirizadas_tomou_ciencia(self):
        # TODO: definir partes interessadas
        return []

    @property
    def partes_interessadas_escola_cancelou(self):
        # TODO: definir partes interessadas
        return []

    def _preenche_template_e_envia_email(
        self, assunto, titulo, id_externo, user, criado_em, partes_interessadas
    ):
        url = f'{env("REACT_APP_URL")}/{self.path}'
        template = "fluxo_ue_informa_suspensao.html"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "id_externo": id_externo,
            "criado_em": criado_em,
            "nome_ue": self.escola.nome,
            "url": url,
            "nome_dre": self.escola.diretoria_regional.nome,
            "nome_lote": self.escola.lote.nome,
            "movimentacao_realizada": str(self.status),
            "perfil_que_autorizou": user.nome,
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template="fluxo_codae_autoriza_ou_nega.html",
            dados_template=dados_template,
            html=html,
        )

    def get_dias_suspensao(self):
        from sme_sigpae_api.escola.models import DiaSuspensaoAtividades

        dias_suspensao = DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
            self.escola, self.DIAS_UTEIS_PARA_CANCELAR
        )
        return dias_suspensao

    def checa_se_pode_cancelar(self, data_do_evento=None):
        dias_suspensao = self.get_dias_suspensao()
        if not data_do_evento:
            data_do_evento = self.data
            if isinstance(data_do_evento, datetime.datetime):
                data_do_evento = data_do_evento.date()
        data_minima_cancelamento = obter_dias_uteis_apos(
            datetime.date.today(), self.DIAS_UTEIS_PARA_CANCELAR + dias_suspensao
        )
        if data_minima_cancelamento >= data_do_evento:
            raise xworkflows.InvalidTransitionError(
                f"Só pode cancelar com no mínimo {self.DIAS_UTEIS_PARA_CANCELAR} dia(s) úteis de antecedência"
            )

    def cancelar_pedido(self, user, justificativa):
        self.checa_se_pode_cancelar()
        self.escola_cancela(user=user, justificativa=justificativa)

    @xworkflows.after_transition("informa")
    def _informa_hook(self, *args, **kwargs):
        user = kwargs["user"]

        if user:
            id_externo = "#" + self.id_externo
            assunto = "[SIGPAE] Status de solicitação - " + id_externo
            titulo = f"Solicitação de {self.tipo}"
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.INICIO_FLUXO, usuario=user
            )
            log_criado = self.logs.last().criado_em
            criado_em = log_criado.strftime("%d/%m/%Y - %H:%M")
            self._preenche_template_e_envia_email(
                assunto,
                titulo,
                id_externo,
                user,
                criado_em,
                self.partes_interessadas_informacao,
            )

        self._salva_rastro_solicitacao()

    @xworkflows.after_transition("terceirizada_toma_ciencia")
    def _terceirizada_toma_ciencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
                usuario=user,
            )

    @xworkflows.after_transition("escola_cancela")
    def _escola_cancela_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs["justificativa"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                justificativa=justificativa,
                usuario=user,
            )

    class Meta:
        abstract = True


class FluxoDietaEspecialPartindoDaEscola(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = DietaEspecialWorkflow
    status = xwf_models.StateField(workflow_class)

    rastro_escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_escola",
        editable=False,
    )
    rastro_dre = models.ForeignKey(
        "escola.DiretoriaRegional",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="%(app_label)s_%(class)s_rastro_dre",
        blank=True,
        editable=False,
    )
    rastro_lote = models.ForeignKey(
        "escola.Lote",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_lote",
        editable=False,
    )
    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        escola = (
            self.criado_por.vinculos.filter(data_inicial__lte=self.criado_em)
            .last()
            .instituicao
        )
        self.rastro_escola = escola
        self.rastro_dre = escola.diretoria_regional
        if escola.tipo_gestao and escola.tipo_gestao.nome == "PARCEIRA":
            self.rastro_lote = None
            self.rastro_terceirizada = None
        else:
            self.rastro_lote = escola.lote
            self.rastro_terceirizada = escola.lote.terceirizada
        self.save()

    def termina(self, usuario):
        if not self.ativo or self.status not in [
            self.workflow_class.CODAE_AUTORIZADO,
            self.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            self.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
            self.workflow_class.CODAE_NEGOU_INATIVACAO,
        ]:
            raise xworkflows.InvalidTransitionError(
                "Só é permitido terminar dietas autorizadas e ativas"
            )
        if self.data_termino is None:
            raise xworkflows.InvalidTransitionError(
                "Não pode terminar uma dieta sem data de término"
            )
        if self.data_termino and self.data_termino > datetime.date.today():
            raise xworkflows.InvalidTransitionError(
                "Não pode terminar uma dieta antes da data"
            )
        self.status = self.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
            usuario=usuario,
            justificativa="Atingiu data limite e foi terminada automaticamente",
        )
        self.save()
        self._envia_email_termino()

    @property
    def _partes_interessadas_inicio_fluxo(self):
        """Quando a escola faz a solicitação, as pessoas da DRE são as partes interessadas.

        Será retornada uma lista de emails para envio via celery.
        """
        email_query_set = self.rastro_escola.vinculos.filter(ativo=True).values_list(
            "usuario__email", flat=False
        )
        return [email for email in email_query_set]

    @property
    def _partes_interessadas_termino(self):
        """Obtém endereços de email das partes interessadas num término de dieta especial.

        A dieta especial termina quando a data de término é atingida.
        São as partes interessadas:
            - perfil "ADMINISTRADOR_EMPRESA" vinculado à terceirizada relacionada
              à escola destino da dieta
            - email de contato da escola (escola.contato.email)
        """
        escola = self.rastro_escola
        try:
            emails_terceirizada = self.rastro_terceirizada.emails_por_modulo(
                "Dieta Especial"
            )
            email_escola_eol = [escola.contato.email]
            email_lista = emails_terceirizada + email_escola_eol
        except AttributeError:
            email_lista = []
        return email_lista

    @property  # noqa c901
    def _partes_interessadas_codae_autoriza_ou_nega(self):
        try:
            email_escola_eol = self.escola.contato.email
            email_lista = [email_escola_eol]
        except AttributeError:
            email_lista = []
        if self.rastro_terceirizada:
            email_lista += self.rastro_terceirizada.emails_por_modulo("Dieta Especial")
        return email_lista

    @property
    def partes_interessadas_terceirizadas_tomou_ciencia(self):
        # TODO: definir partes interessadas
        return []

    @property  # noqa c901
    def _partes_interessadas_codae_autoriza(self):
        escola = self.escola_destino
        try:
            email_escola_destino_eol = [escola.contato.email]
        except AttributeError:
            email_escola_destino_eol = []
        try:
            emails_terceirizadas = self.rastro_terceirizada.emails_por_modulo(
                "Dieta Especial"
            )
        except AttributeError:
            emails_terceirizadas = []
        return email_escola_destino_eol + emails_terceirizadas

    @property
    def _partes_interessadas_codae_cancela(self):
        escola = self.escola_destino
        try:
            emails_terceirizadas = self.rastro_terceirizada.emails_por_modulo(
                "Dieta Especial"
            )
            email_escola_eol = [escola.contato.email]
            email_lista = emails_terceirizadas + email_escola_eol
        except AttributeError:
            email_lista = []
        return email_lista

    @property
    def template_mensagem(self):
        raise NotImplementedError(
            "Deve criar um property que recupera o assunto e corpo mensagem desse objeto"
        )

    def _envia_email_autorizar(
        self, assunto, titulo, user, partes_interessadas, dieta_origem
    ):
        from ..relatorios.relatorios import relatorio_dieta_especial_protocolo

        template = "fluxo_autorizar_dieta.html"
        dados_template = {
            "nome_aluno": self.aluno.nome,
            "codigo_eol_aluno": self.aluno.codigo_eol,
            "data_inicio": self.data_inicio.strftime("%d/%m/%Y"),
            "data_termino": self.data_termino.strftime("%d/%m/%Y"),
        }

        html = render_to_string(template, dados_template)

        html_string_relatorio = relatorio_dieta_especial_protocolo(None, dieta_origem)

        anexo = {
            "arquivo": html_to_pdf_email_anexo(html_string_relatorio),
            "nome": f"dieta_especial_{dieta_origem.id_externo}.pdf",
            "mimetypes": "application/pdf",
        }

        for email in partes_interessadas:
            envia_email_unico_com_anexo_inmemory(
                assunto=assunto,
                corpo=html,
                email=email,
                anexo_nome=anexo.get("nome"),
                mimetypes=anexo.get("mimetypes"),
                anexo=anexo.get("arquivo"),
            )

    def _preenche_template_e_envia_email(
        self, assunto, titulo, user, partes_interessadas, transicao
    ):
        url = None
        if transicao == "codae_nega":
            url = f'{env("REACT_APP_URL")}/dieta-especial'
            url += f"/relatorio?uuid={self.uuid}&ehInclusaoContinua=false&card=negadas"
        dados_template = {
            "titulo": titulo,
            "tipo_solicitacao": self.DESCRICAO,
            "nome_aluno": self.aluno.nome,
            "cod_eol_aluno": self.aluno.codigo_eol,
            "movimentacao_realizada": str(self.status),
            "perfil_que_autorizou": user.nome,
            "escola": self.escola.nome,
            "lote": (
                self.escola.lote.nome if self.escola.lote else "Sem Lote (Parceira)"
            ),
            "url": url,
            "data_log": self.log_mais_recente.criado_em.strftime("%d/%m/%Y - %H:%M"),
        }
        if transicao == "codae_autoriza":
            template = "fluxo_codae_autoriza_dieta.html"
            dados_template["acao"] = "autorizada"
        elif transicao == "codae_nega":
            template = "fluxo_codae_nega_dieta.html"
            dados_template["acao"] = "negada"
        elif transicao == "cancelar_pedido":
            template = "fluxo_dieta_alta_medica.html"
        else:
            template = "fluxo_autorizar_negar_cancelar.html"

        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=partes_interessadas,
            template=template,
            dados_template=dados_template,
            html=html,
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        self._salva_rastro_solicitacao()
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO, usuario=user
        )

    @xworkflows.after_transition("cancelar_pedido")
    def _cancelar_pedido_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs["justificativa"]
        alta_medica = kwargs.get("alta_medica", False)
        assunto = "[SIGPAE] Status de solicitação - #" + self.id_externo
        titulo = (
            f'Status de solicitação - "{self.aluno.codigo_eol} - {self.aluno.nome}"'
        )
        if alta_medica:
            titulo = self.str_dre_lote_escola
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
            usuario=user,
            justificativa=justificativa,
        )
        if self.tipo_solicitacao != "CANCELAMENTO_DIETA":
            self._preenche_template_e_envia_email(
                assunto,
                titulo,
                user,
                self._partes_interessadas_codae_cancela,
                "cancelar_pedido" if alta_medica else None,
            )

    @xworkflows.after_transition("negar_cancelamento_pedido")
    def _negar_cancelamento_pedido_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs["justificativa"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU_CANCELAMENTO,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("cancelar_aluno_mudou_escola")
    def _cancelar_aluno_mudou_escola_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
            usuario=kwargs["user"],
        )

    @xworkflows.after_transition("cancelar_aluno_nao_pertence_rede")
    def _cancelar_aluno_nao_pertence_rede_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
            usuario=kwargs["user"],
        )

    @xworkflows.after_transition("codae_nega")
    def _codae_nega_hook(self, *args, **kwargs):
        user = kwargs["user"]
        assunto = "[SIGPAE] Status de Solicitação - #" + self.id_externo
        titulo = (
            f'Status de Solicitação - "{self.aluno.codigo_eol} - {self.aluno.nome}"'
        )
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU, usuario=user
        )
        self._preenche_template_e_envia_email(
            assunto,
            titulo,
            user,
            self._partes_interessadas_codae_autoriza_ou_nega,
            "codae_nega",
        )

    @xworkflows.after_transition("codae_autoriza")
    def _codae_autoriza_hook(self, *args, **kwargs):
        user = kwargs["user"]
        eh_importacao = kwargs.get("eh_importacao", None)
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU, usuario=user
        )
        if not eh_importacao:
            if self.tipo_solicitacao == "ALTERACAO_UE":
                assunto = "Alerta de atendimento de Dieta Especial no CEI-Polo/Recreio nas férias"
                titulo = "Alerta de atendimento de Dieta Especial no CEI-Polo/Recreio nas férias"
                dieta_origem = self.aluno.dietas_especiais.filter(
                    tipo_solicitacao="COMUM",
                    ativo=True,
                    status=self.workflow_class.CODAE_AUTORIZADO,
                ).last()
                self._envia_email_autorizar(
                    assunto,
                    titulo,
                    user,
                    self._partes_interessadas_codae_autoriza,
                    dieta_origem,
                )
            else:
                assunto = "[SIGPAE] Status de solicitação - #" + self.id_externo
                titulo = self.str_dre_lote_escola
                self._preenche_template_e_envia_email(
                    assunto,
                    titulo,
                    user,
                    self._partes_interessadas_codae_autoriza_ou_nega,
                    "codae_autoriza",
                )

    @xworkflows.after_transition("inicia_fluxo_inativacao")
    def _inicia_fluxo_inativacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("codae_autoriza_inativacao")
    def _codae_autoriza_inativacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
            usuario=user,
        )

    @xworkflows.after_transition("codae_nega_inativacao")
    def _codae_nega_inativacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO,
            usuario=user,
            justificativa=justificativa,
        )

    @xworkflows.after_transition("terceirizada_toma_ciencia_inativacao")
    def _terceirizada_toma_ciencia_inativacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
                usuario=user,
            )

    @xworkflows.after_transition("terceirizada_toma_ciencia")
    def _terceirizada_toma_ciencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
                usuario=user,
            )

    def _envia_email_termino(self):
        assunto = f"[SIGPAE] Prazo de fornecimento de dieta encerrado - Solicitação #{self.id_externo}"
        template = "fluxo_dieta_especial_termina.html"
        titulo = self.str_dre_lote_escola
        dados_template = {
            "eol_aluno": self.aluno.codigo_eol,
            "nome_aluno": self.aluno.nome,
            "titulo": titulo,
        }
        html = render_to_string(template, dados_template)
        envia_email_em_massa_task.delay(
            assunto=assunto,
            corpo="",
            emails=self._partes_interessadas_termino,
            html=html,
        )

    class Meta:
        abstract = True


class ReclamacaoProdutoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    AGUARDANDO_AVALIACAO = "AGUARDANDO_AVALIACAO"  # INICIO
    AGUARDANDO_RESPOSTA_TERCEIRIZADA = "AGUARDANDO_RESPOSTA_TERCEIRIZADA"
    RESPONDIDO_TERCEIRIZADA = "RESPONDIDO_TERCEIRIZADA"
    AGUARDANDO_ANALISE_SENSORIAL = "AGUARDANDO_ANALISE_SENSORIAL"
    ANALISE_SENSORIAL_RESPONDIDA = "ANALISE_SENSORIAL_RESPONDIDA"
    AGUARDANDO_RESPOSTA_UE = "AGUARDANDO_RESPOSTA_UE"
    RESPONDIDO_UE = "RESPONDIDO_UE"
    AGUARDANDO_RESPOSTA_NUTRISUPERVISOR = "AGUARDANDO_RESPOSTA_NUTRISUPERVISOR"
    RESPONDIDO_NUTRISUPERVISOR = "RESPONDIDO_NUTRISUPERVISOR"
    CODAE_ACEITOU = "CODAE_ACEITOU"
    CODAE_RECUSOU = "CODAE_RECUSOU"
    CODAE_RESPONDEU = "CODAE_RESPONDEU"

    states = (
        (AGUARDANDO_AVALIACAO, "Aguardando avaliação da CODAE"),
        (AGUARDANDO_RESPOSTA_TERCEIRIZADA, "Aguardando resposta da terceirizada"),
        (AGUARDANDO_RESPOSTA_UE, "Aguardando resposta da U.E"),
        (AGUARDANDO_RESPOSTA_NUTRISUPERVISOR, "Aguardando resposta do nutrisupervisor"),
        (AGUARDANDO_ANALISE_SENSORIAL, "Aguardando análise sensorial."),
        (ANALISE_SENSORIAL_RESPONDIDA, "Análise sensorial respondida."),
        (RESPONDIDO_TERCEIRIZADA, "Respondido pela terceirizada"),
        (RESPONDIDO_UE, "Respondido pela U.E"),
        (RESPONDIDO_NUTRISUPERVISOR, "Respondido pelo nutrisupervisor"),
        (CODAE_ACEITOU, "CODAE aceitou"),
        (CODAE_RECUSOU, "CODAE recusou"),
        (CODAE_RESPONDEU, "CODAE respondeu ao reclamante"),
    )

    transitions = (
        (
            "codae_questiona_terceirizada",
            [
                AGUARDANDO_AVALIACAO,
                ANALISE_SENSORIAL_RESPONDIDA,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            AGUARDANDO_RESPOSTA_TERCEIRIZADA,
        ),
        (
            "terceirizada_responde",
            AGUARDANDO_RESPOSTA_TERCEIRIZADA,
            RESPONDIDO_TERCEIRIZADA,
        ),
        (
            "codae_questiona_ue",
            [
                AGUARDANDO_AVALIACAO,
                ANALISE_SENSORIAL_RESPONDIDA,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            AGUARDANDO_RESPOSTA_UE,
        ),
        ("ue_responde", AGUARDANDO_RESPOSTA_UE, RESPONDIDO_UE),
        (
            "codae_questiona_nutrisupervisor",
            [
                AGUARDANDO_AVALIACAO,
                ANALISE_SENSORIAL_RESPONDIDA,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
        ),
        (
            "nutrisupervisor_responde",
            AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
            RESPONDIDO_NUTRISUPERVISOR,
        ),
        (
            "codae_aceita",
            [
                AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                AGUARDANDO_AVALIACAO,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                AGUARDANDO_ANALISE_SENSORIAL,
                ANALISE_SENSORIAL_RESPONDIDA,
                AGUARDANDO_RESPOSTA_UE,
                RESPONDIDO_UE,
            ],
            CODAE_ACEITOU,
        ),
        (
            "codae_recusa",
            [
                AGUARDANDO_RESPOSTA_TERCEIRIZADA,
                AGUARDANDO_AVALIACAO,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                AGUARDANDO_ANALISE_SENSORIAL,
                ANALISE_SENSORIAL_RESPONDIDA,
                AGUARDANDO_RESPOSTA_UE,
                AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            CODAE_RECUSOU,
        ),
        (
            "codae_responde",
            [
                AGUARDANDO_AVALIACAO,
                ANALISE_SENSORIAL_RESPONDIDA,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            CODAE_RESPONDEU,
        ),
        (
            "codae_pede_analise_sensorial",
            [
                AGUARDANDO_AVALIACAO,
                ANALISE_SENSORIAL_RESPONDIDA,
                RESPONDIDO_TERCEIRIZADA,
                RESPONDIDO_NUTRISUPERVISOR,
                RESPONDIDO_UE,
            ],
            AGUARDANDO_ANALISE_SENSORIAL,
        ),
        (
            "codae_cancela_analise_sensorial",
            AGUARDANDO_ANALISE_SENSORIAL,
            AGUARDANDO_AVALIACAO,
        ),
        (
            "terceirizada_responde_analise_sensorial",
            AGUARDANDO_ANALISE_SENSORIAL,
            ANALISE_SENSORIAL_RESPONDIDA,
        ),
    )

    initial_state = AGUARDANDO_AVALIACAO


class FluxoReclamacaoProduto(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = ReclamacaoProdutoWorkflow
    status = xwf_models.StateField(workflow_class)

    def _partes_interessadas_suspensao_por_reclamacao(self):
        queryset = Usuario.objects.filter(
            vinculos__ativo=True,
            vinculos__data_inicial__isnull=False,
            vinculos__data_final__isnull=True,
            vinculos__perfil__nome__in=[
                "ADMINISTRADOR_UE",
                "DIRETOR_UE",
                "COORDENADOR_SUPERVISAO_NUTRICAO",
                "ADMINISTRADOR_SUPERVISAO_NUTRICAO",
            ],
        )
        emails_terceirizadas = (
            self.homologacao_produto.rastro_terceirizada.todos_emails_por_modulo(
                "Gestão de Produto"
            )
        )
        return [usuario.email for usuario in queryset] + emails_terceirizadas

    def _envia_email_recusa_reclamacao(self, log_recusa):
        html = render_to_string(
            template_name="produto_codae_recusou_reclamacao.html",
            context={
                "titulo": "Reclamação Analisada",
                "reclamacao": self,
                "log_recusa": log_recusa,
            },
        )
        envia_email_unico_task.delay(
            assunto="[SIGPAE] Reclamação Analisada",
            email=self.criado_por.email,
            corpo="",
            html=html,
        )

    def _envia_email_resposta_reclamacao(self, log_resposta):
        html = render_to_string(
            template_name="produto_codae_responde_reclamacao.html",
            context={
                "titulo": "Resposta a reclamação realizada",
                "reclamacao": self,
                "log_resposta": log_resposta,
            },
        )
        envia_email_unico_task.delay(
            assunto="[SIGPAE] Resposta a reclamação realizada",
            email=self.criado_por.email,
            corpo="",
            html=html,
        )

    def _envia_email_aceite_reclamacao(self, log_aceite):
        html = render_to_string(
            template_name="produto_codae_suspende.html",
            context={
                "titulo": "Suspensão de Produto",
                "produto": self.homologacao_produto.produto,
                "log_transicao": log_aceite,
            },
        )
        envia_email_em_massa_task.delay(
            assunto="[SIGPAE] Suspensão de Produto",
            emails=self._partes_interessadas_suspensao_por_reclamacao(),
            corpo="",
            html=html,
        )

    @xworkflows.after_transition("codae_aceita")
    def _codae_aceita_hook(self, *args, **kwargs):
        log_aceite = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO, **kwargs
        )
        self._envia_email_aceite_reclamacao(log_aceite)

    @xworkflows.after_transition("codae_recusa")
    def _codae_recusa_hook(self, *args, **kwargs):
        log_recusa = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO, **kwargs
        )
        self._envia_email_recusa_reclamacao(log_recusa)

    @xworkflows.after_transition("codae_questiona_terceirizada")
    def _codae_questiona_terceirizada_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU_TERCEIRIZADA, **kwargs
        )

    @xworkflows.after_transition("codae_questiona_ue")
    def _codae_questiona_ue_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU_UE, **kwargs
        )

    @xworkflows.after_transition("codae_questiona_nutrisupervisor")
    def _codae_questiona_nutrisupervisor_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU_NUTRISUPERVISOR,
            **kwargs,
        )

    @xworkflows.after_transition("codae_responde")
    def _codae_responde_hook(self, *args, **kwargs):
        log_resposta = self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_RESPONDEU_RECLAMACAO, **kwargs
        )
        self._envia_email_resposta_reclamacao(log_resposta)

    @xworkflows.after_transition("terceirizada_responde")
    def _terceirizada_responde_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
            **kwargs,
        )

    @xworkflows.after_transition("ue_responde")
    def _ue_responde_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.UE_RESPONDEU_RECLAMACAO, **kwargs
        )

    @xworkflows.after_transition("nutrisupervisor_responde")
    def _nutrisupervisor_responde_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.NUTRISUPERVISOR_RESPONDEU_RECLAMACAO,
            **kwargs,
        )

    @xworkflows.after_transition("codae_pede_analise_sensorial")
    def _codae_pede_analise_sensorial_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL, **kwargs
        )

    @xworkflows.after_transition("codae_cancela_analise_sensorial")
    def _codae_cancela_analise_sensorial_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            **kwargs,
        )

    @xworkflows.after_transition("terceirizada_responde_analise_sensorial")
    def _terceirizada_responde_analise_sensorial_hook(self, *args, **kwargs):
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL,
            **kwargs,
        )

    class Meta:
        abstract = True


class SolicitacaoCadastroProdutoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"  # INICIO
    CONFIRMADA = "CONFIRMADA"

    states = (
        (AGUARDANDO_CONFIRMACAO, "Aguardando confirmação"),
        (CONFIRMADA, "Confirmada"),
    )

    transitions = (
        ("terceirizada_atende_solicitacao", AGUARDANDO_CONFIRMACAO, CONFIRMADA),
    )

    initial_state = AGUARDANDO_CONFIRMACAO


class FluxoSolicitacaoCadastroProduto(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = SolicitacaoCadastroProdutoWorkflow
    status = xwf_models.StateField(workflow_class)

    def _partes_interessadas_solicitacao_cadastro_produto(self):
        queryset = Usuario.objects.filter(
            vinculos__ativo=True,
            vinculos__perfil__nome__in=[
                "ADMINISTRADOR_GESTAO_PRODUTO",
                "COORDENADOR_GESTAO_PRODUTO",
                "COORDENADOR_DIETA_ESPECIAL",
            ],
        )
        return [usuario.email for usuario in queryset]

    def _envia_email_solicitacao_realizada(self):
        html = render_to_string(
            template_name="dieta_especial_solicitou_cadastro_produto.html",
            context={
                "titulo": "Solicitação de cadastro de novo produto realizada",
                "solicitacao": self,
            },
        )

        assunto = "[SIGPAE] Solicitação de cadastro de novo produto realizada"
        emails = self._partes_interessadas_solicitacao_cadastro_produto()
        emails.append(self.terceirizada.contatos.last().email)
        corpo = ""

        envia_email_em_massa_task.delay(
            assunto=assunto, emails=emails, corpo=corpo, html=html
        )


class SolicitacaoMedicaoInicialWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE = "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"
    MEDICAO_ENVIADA_PELA_UE = "MEDICAO_ENVIADA_PELA_UE"
    MEDICAO_CORRECAO_SOLICITADA = "MEDICAO_CORRECAO_SOLICITADA"
    MEDICAO_CORRECAO_SOLICITADA_CODAE = "MEDICAO_CORRECAO_SOLICITADA_CODAE"
    MEDICAO_CORRIGIDA_PELA_UE = "MEDICAO_CORRIGIDA_PELA_UE"
    MEDICAO_CORRIGIDA_PARA_CODAE = "MEDICAO_CORRIGIDA_PARA_CODAE"
    MEDICAO_APROVADA_PELA_DRE = "MEDICAO_APROVADA_PELA_DRE"
    MEDICAO_APROVADA_PELA_CODAE = "MEDICAO_APROVADA_PELA_CODAE"

    states = (
        (
            MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
            "Em aberto para preenchimento pela UE",
        ),
        (MEDICAO_ENVIADA_PELA_UE, "Enviado pela UE"),
        (MEDICAO_CORRECAO_SOLICITADA, "Correção solicitada DRE"),
        (MEDICAO_CORRECAO_SOLICITADA_CODAE, "Correção solicitada CODAE"),
        (MEDICAO_CORRIGIDA_PELA_UE, "Corrigido para DRE"),
        (MEDICAO_CORRIGIDA_PARA_CODAE, "Corrigido para CODAE"),
        (MEDICAO_APROVADA_PELA_DRE, "Aprovado pela DRE"),
        (MEDICAO_APROVADA_PELA_CODAE, "Aprovado por CODAE"),
    )

    transitions = (
        (
            "inicia_fluxo",
            MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
            MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        ),
        ("ue_envia", MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE, MEDICAO_ENVIADA_PELA_UE),
        (
            "dre_pede_correcao",
            [
                MEDICAO_CORRECAO_SOLICITADA,
                MEDICAO_ENVIADA_PELA_UE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PELA_UE,
            ],
            MEDICAO_CORRECAO_SOLICITADA,
        ),
        (
            "codae_pede_correcao_periodo",
            [
                MEDICAO_CORRECAO_SOLICITADA_CODAE,
                MEDICAO_APROVADA_PELA_CODAE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PARA_CODAE,
            ],
            MEDICAO_CORRECAO_SOLICITADA_CODAE,
        ),
        (
            "codae_aprova_periodo",
            [
                MEDICAO_CORRECAO_SOLICITADA_CODAE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PARA_CODAE,
            ],
            MEDICAO_APROVADA_PELA_CODAE,
        ),
        (
            "codae_pede_correcao_ocorrencia",
            [
                MEDICAO_CORRECAO_SOLICITADA_CODAE,
                MEDICAO_APROVADA_PELA_CODAE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PARA_CODAE,
            ],
            MEDICAO_CORRECAO_SOLICITADA_CODAE,
        ),
        (
            "codae_aprova_ocorrencia",
            [
                MEDICAO_CORRECAO_SOLICITADA_CODAE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PARA_CODAE,
            ],
            MEDICAO_APROVADA_PELA_CODAE,
        ),
        (
            "ue_corrige",
            [MEDICAO_CORRECAO_SOLICITADA, MEDICAO_CORRIGIDA_PELA_UE],
            MEDICAO_CORRIGIDA_PELA_UE,
        ),
        (
            "ue_corrige_ocorrencia_para_codae",
            [MEDICAO_CORRECAO_SOLICITADA_CODAE, MEDICAO_CORRIGIDA_PARA_CODAE],
            MEDICAO_CORRIGIDA_PARA_CODAE,
        ),
        (
            "ue_corrige_periodo_grupo_para_codae",
            [MEDICAO_CORRECAO_SOLICITADA_CODAE, MEDICAO_CORRIGIDA_PARA_CODAE],
            MEDICAO_CORRIGIDA_PARA_CODAE,
        ),
        (
            "ue_corrige_medicao_para_codae",
            MEDICAO_CORRECAO_SOLICITADA_CODAE,
            MEDICAO_CORRIGIDA_PARA_CODAE,
        ),
        (
            "dre_aprova",
            [
                MEDICAO_ENVIADA_PELA_UE,
                MEDICAO_CORRECAO_SOLICITADA,
                MEDICAO_CORRIGIDA_PELA_UE,
            ],
            MEDICAO_APROVADA_PELA_DRE,
        ),
        (
            "codae_aprova_medicao",
            [MEDICAO_APROVADA_PELA_DRE, MEDICAO_CORRIGIDA_PARA_CODAE],
            MEDICAO_APROVADA_PELA_CODAE,
        ),
        (
            "codae_pede_correcao_medicao",
            [
                MEDICAO_CORRECAO_SOLICITADA_CODAE,
                MEDICAO_APROVADA_PELA_DRE,
                MEDICAO_CORRIGIDA_PARA_CODAE,
            ],
            MEDICAO_CORRECAO_SOLICITADA_CODAE,
        ),
    )

    initial_state = MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE


class FluxoSolicitacaoMedicaoInicial(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = SolicitacaoMedicaoInicialWorkflow
    status = xwf_models.StateField(workflow_class)

    rastro_lote = models.ForeignKey(
        "escola.Lote",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_lote",
        editable=False,
    )
    rastro_terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_rastro_terceirizada",
        editable=False,
    )

    def _salva_rastro_solicitacao(self):
        self.rastro_lote = self.escola.lote
        self.rastro_terceirizada = self.escola.lote.terceirizada
        self.save()

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        self._salva_rastro_solicitacao()
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
                usuario=user,
            )

    @xworkflows.after_transition("ue_envia")
    def _ue_envia_hook(self, *args, **kwargs):
        from ..medicao_inicial.models import OcorrenciaMedicaoInicial

        user = kwargs["user"]
        if user:
            if not user.vinculo_atual.perfil.nome == DIRETOR_UE:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            log_transicao = self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE,
                usuario=user,
            )
            if isinstance(self, OcorrenciaMedicaoInicial):
                anexos = kwargs.get("anexos")
                if anexos is not None:
                    for anexo in anexos:
                        arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
                        AnexoLogSolicitacoesUsuario.objects.create(
                            log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
                        )

    @xworkflows.after_transition("dre_aprova")
    def _dre_aprova_hook(self, *args, **kwargs):
        from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes

        from ..medicao_inicial.models import (
            Medicao,
            OcorrenciaMedicaoInicial,
            SolicitacaoMedicaoInicial,
        )

        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [COGESTOR_DRE]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            if isinstance(self, OcorrenciaMedicaoInicial) or isinstance(self, Medicao):
                self.deletar_log_correcao(
                    status_evento=[
                        LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA,
                        LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
                    ]
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
                usuario=user,
            )
            if (
                isinstance(self, SolicitacaoMedicaoInicial)
                and self.escola
                and self.escola.contato
                and self.escola.contato.email
            ):
                url = f'{env("REACT_APP_URL")}/medicao-inicial'
                url += f"/detalhamento-do-lancamento?mes={self.mes}&ano={self.ano}"
                html = render_to_string(
                    template_name="medicao_dre_codae_aprova_solicitacao.html",
                    context={
                        "titulo": "Medição Inicial aprovada pela DRE",
                        "url": url,
                        "mes": converte_numero_em_mes(int(self.mes)).lower,
                        "ano": self.ano,
                        "usuario": "DRE",
                    },
                )
                envia_email_unico_task.delay(
                    assunto="[SIGPAE] Medição Inicial aprovada pela DRE",
                    email=self.escola.contato.email,
                    corpo="",
                    html=html,
                )

    @xworkflows.after_transition("dre_pede_correcao")
    def _dre_pede_correcao_hook(self, *args, **kwargs):
        from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes

        from ..medicao_inicial.models import (
            Medicao,
            OcorrenciaMedicaoInicial,
            SolicitacaoMedicaoInicial,
        )

        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            if user.vinculo_atual.perfil.nome not in [COGESTOR_DRE]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            if isinstance(self, OcorrenciaMedicaoInicial) or isinstance(self, Medicao):
                self.deletar_log_correcao(
                    status_evento=[
                        LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA,
                        LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
                    ]
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA,
                usuario=user,
                justificativa=justificativa,
            )
            if (
                isinstance(self, SolicitacaoMedicaoInicial)
                and self.escola
                and self.escola.contato
                and self.escola.contato.email
            ):
                url = f'{env("REACT_APP_URL")}/medicao-inicial'
                url += f"/detalhamento-do-lancamento?mes={self.mes}&ano={self.ano}"
                html = render_to_string(
                    template_name="medicao_dre_codae_solicita_correcao.html",
                    context={
                        "titulo": "Solicitação de correção da Medição Inicial pela DRE",
                        "url": url,
                        "mes": converte_numero_em_mes(int(self.mes)).lower,
                        "ano": self.ano,
                        "usuario": "DRE",
                    },
                )
                envia_email_unico_task.delay(
                    assunto="Solicitação de correção da Medição Inicial pela DRE",
                    email=self.escola.contato.email,
                    corpo="",
                    html=html,
                )

    @xworkflows.after_transition("codae_pede_correcao_ocorrencia")
    def _codae_pede_correcao_ocorrencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.deletar_log_correcao(
                status_evento=[
                    LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                    LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                ]
            )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                usuario=user,
                justificativa=justificativa,
            )

    @xworkflows.after_transition("codae_aprova_ocorrencia")
    def _codae_aprova_ocorrencia_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.deletar_log_correcao(
                status_evento=[
                    LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                    LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                ]
            )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                usuario=user,
            )

    @xworkflows.after_transition("codae_pede_correcao_periodo")
    def _codae_pede_correcao_periodo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.deletar_log_correcao(
                status_evento=[
                    LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                    LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                ]
            )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                usuario=user,
                justificativa=justificativa,
            )

    @xworkflows.after_transition("codae_aprova_periodo")
    def _codae_aprova_periodo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.deletar_log_correcao(
                status_evento=[
                    LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                    LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                ]
            )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                usuario=user,
            )

    @xworkflows.after_transition("codae_aprova_medicao")
    def _codae_aprova_medicao_hook(self, *args, **kwargs):
        from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes

        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
                usuario=user,
            )
            if self.escola and self.escola.contato and self.escola.contato.email:
                url = f'{env("REACT_APP_URL")}/medicao-inicial'
                url += f"/detalhamento-do-lancamento?mes={self.mes}&ano={self.ano}"
                html = render_to_string(
                    template_name="medicao_dre_codae_aprova_solicitacao.html",
                    context={
                        "titulo": "Medição Inicial aprovada pela CODAE",
                        "url": url,
                        "mes": converte_numero_em_mes(int(self.mes)).lower,
                        "ano": self.ano,
                        "usuario": "CODAE",
                    },
                )
                envia_email_unico_task.delay(
                    assunto="[SIGPAE] Medição Inicial aprovada pela CODAE",
                    email=self.escola.contato.email,
                    corpo="",
                    html=html,
                )

    @xworkflows.after_transition("codae_pede_correcao_medicao")
    def _codae_pede_correcao_medicao_hook(self, *args, **kwargs):
        from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes

        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [ADMINISTRADOR_MEDICAO]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE,
                usuario=user,
            )
            if self.escola and self.escola.contato and self.escola.contato.email:
                url = f'{env("REACT_APP_URL")}/medicao-inicial'
                url += f"/detalhamento-do-lancamento?mes={self.mes}&ano={self.ano}"
                html = render_to_string(
                    template_name="medicao_dre_codae_solicita_correcao.html",
                    context={
                        "titulo": "Solicitação de correção da Medição Inicial pela CODAE",
                        "url": url,
                        "mes": converte_numero_em_mes(int(self.mes)).lower,
                        "ano": self.ano,
                        "usuario": "CODAE",
                    },
                )
                envia_email_unico_task.delay(
                    assunto="[SIGPAE] Solicitação de correção da Medição Inicial pela CODAE",
                    email=self.escola.contato.email,
                    corpo="",
                    html=html,
                )

    @xworkflows.after_transition("ue_corrige")
    def _ue_corrige_hook(self, *args, **kwargs):
        from ..medicao_inicial.models import OcorrenciaMedicaoInicial

        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user:
            if not user.vinculo_atual.perfil.nome == DIRETOR_UE:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )

            status = LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE

            if isinstance(self, OcorrenciaMedicaoInicial):
                log_antigo = self.logs.filter(status_evento=status)

                if log_antigo:
                    log_antigo = log_antigo.first()
                    log_antigo.anexos.all().delete()
                    log_antigo.delete()

                log_transicao = self.salvar_log_transicao(
                    status_evento=status, usuario=user, justificativa=justificativa
                )
                for anexo in kwargs.get("anexos", []):
                    arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
                    AnexoLogSolicitacoesUsuario.objects.create(
                        log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
                    )
            else:
                self.salvar_log_transicao(
                    status_evento=status, usuario=user, justificativa=justificativa
                )

    @xworkflows.after_transition("ue_corrige_ocorrencia_para_codae")
    def _ue_corrige_ocorrencia_para_codae_hook(self, *args, **kwargs):
        from ..medicao_inicial.models import OcorrenciaMedicaoInicial

        user = kwargs["user"]
        justificativa = kwargs.get("justificativa", "")
        if user and isinstance(self, OcorrenciaMedicaoInicial):
            if not user.vinculo_atual.perfil.nome == DIRETOR_UE:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )

            status = LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE

            log_antigo = self.logs.filter(status_evento=status)

            if log_antigo:
                log_antigo = log_antigo.first()
                log_antigo.anexos.all().delete()
                log_antigo.delete()

            log_transicao = self.salvar_log_transicao(
                status_evento=status, usuario=user, justificativa=justificativa
            )
            for anexo in kwargs.get("anexos", []):
                arquivo = convert_base64_to_contentfile(anexo.pop("base64"))
                AnexoLogSolicitacoesUsuario.objects.create(
                    log=log_transicao, arquivo=arquivo, nome=anexo["nome"]
                )

    @xworkflows.after_transition("ue_corrige_periodo_grupo_para_codae")
    def _ue_corrige_periodo_grupo_para_codae_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            if not user.vinculo_atual.perfil.nome == DIRETOR_UE:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
                usuario=user,
            )

    @xworkflows.after_transition("ue_corrige_medicao_para_codae")
    def _ue_corrige_medicao_para_codae_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            if user.vinculo_atual.perfil.nome not in [DIRETOR_UE]:
                raise PermissionDenied(
                    "Você não tem permissão para executar essa ação."
                )
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
                usuario=user,
            )

    class Meta:
        abstract = True


class CronogramaWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"
    ASSINADO_E_ENVIADO_AO_FORNECEDOR = "ASSINADO_E_ENVIADO_AO_FORNECEDOR"
    ALTERACAO_CODAE = "ALTERACAO_CODAE"
    ASSINADO_FORNECEDOR = "ASSINADO_FORNECEDOR"
    SOLICITADO_ALTERACAO = "SOLICITADO_ALTERACAO"
    ASSINADO_DILOG_ABASTECIMENTO = "ASSINADO_DILOG_ABASTECIMENTO"
    ASSINADO_CODAE = "ASSINADO_CODAE"

    states = (
        (RASCUNHO, "Rascunho"),
        (ASSINADO_E_ENVIADO_AO_FORNECEDOR, "Assinado e Enviado ao Fornecedor"),
        (ALTERACAO_CODAE, "Alteração CODAE"),
        (ASSINADO_FORNECEDOR, "Assinado Fornecedor"),
        (SOLICITADO_ALTERACAO, "Solicitado Alteração"),
        (ASSINADO_DILOG_ABASTECIMENTO, "Assinado Abastecimento"),
        (ASSINADO_CODAE, "Assinado CODAE"),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, ASSINADO_E_ENVIADO_AO_FORNECEDOR),
        ("fornecedor_assina", ASSINADO_E_ENVIADO_AO_FORNECEDOR, ASSINADO_FORNECEDOR),
        (
            "dilog_abastecimento_assina",
            ASSINADO_FORNECEDOR,
            ASSINADO_DILOG_ABASTECIMENTO,
        ),
        ("codae_assina", ASSINADO_DILOG_ABASTECIMENTO, ASSINADO_CODAE),
        ("fornecedor_solicita_alteracao", ASSINADO_CODAE, SOLICITADO_ALTERACAO),
        ("codae_realiza_alteracao", ASSINADO_CODAE, ALTERACAO_CODAE),
        (
            "finaliza_solicitacao_alteracao",
            [SOLICITADO_ALTERACAO, ALTERACAO_CODAE],
            ASSINADO_CODAE,
        ),
    )

    initial_state = RASCUNHO


class FluxoCronograma(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = CronogramaWorkflow
    status = xwf_models.StateField(workflow_class)

    def _preenche_template(self, template_notif, log_transicao, perfil=None):
        esconder_dados = perfil in ["ADMINISTRADOR_EMPRESA"]
        texto_notificacao = render_to_string(
            template_name=template_notif,
            context={
                "solicitacao": self.numero,
                "log_transicao": log_transicao,
                "objeto": self,
                "esconder_dados": esconder_dados,
            },
        )
        return texto_notificacao

    def _cria_notificacao(
        self, template_notif, titulo_notif, usuarios, link, tipo, log_transicao=None
    ):
        if usuarios:
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=Notificacao.CATEGORIA_NOTIFICACAO_CRONOGRAMA,
                    titulo=titulo_notif,
                    descricao=self._preenche_template(
                        template_notif, log_transicao, usuario.vinculo_atual.perfil.nome
                    ),
                    usuario=usuario,
                    link=link,
                    cronograma=self,
                )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ENVIADO_AO_FORNECEDOR,
                usuario=user,
            )

    @xworkflows.after_transition("fornecedor_assina")
    def _fornecedor_assina_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELO_FORNECEDOR,
                usuario=user,
            )

            url_detalhe_cronograma = (
                f"/pre-recebimento/detalhe-cronograma?uuid={self.uuid}"
            )

            contexto = {
                "numero_cronograma": self.numero,
                "nome_produto": self.ficha_tecnica.produto.nome,
                "nome_empresa": self.empresa.nome_fantasia,
                "nome_usuario_empresa": user.nome,
                "cpf_usuario_empresa": user.cpf_formatado_e_censurado,
                "data_evento": self.log_mais_recente.criado_em.strftime("%d/%m/%Y"),
                "url_detalhe_cronograma": base_url + url_detalhe_cronograma,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_assinatura_fornecedor.html",
                contexto_template=contexto,
                titulo_notificacao=f"Cronograma {self.numero} assinado pelo Fornecedor",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_AVISO,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_CRONOGRAMA,
                link_acesse_aqui=url_detalhe_cronograma,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    DILOG_ABASTECIMENTO
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Assinatura do Cronograma {self.numero}\npelo Fornecedor",
                assunto=f"[SIGPAE] Assinatura do Cronograma {self.numero} pelo Fornecedor",
                template="pre_recebimento_email_assinatura_fornecedor.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    DILOG_ABASTECIMENTO,
                    somente_email=True,
                ),
            )

    def _envia_email_solicita_alteracao_para_cronograma(self, user):
        log_transicao = self.log_mais_recente
        uuid_solicitacao_alteracao = self.solicitacoes_de_alteracao.last().uuid
        url = f'{env("REACT_APP_URL")}/pre-recebimento/detalhe-alteracao-cronograma?uuid={uuid_solicitacao_alteracao}'

        html = render_to_string(
            template_name="pre_recebumento_notificacao_alteracao_cronograma.html",
            context={
                "titulo": f"Solicitação de Alteração do Cronograma {self.numero}",
                "solicitacao": self.numero,
                "url": url,
                "usuario": user.nome,
                "log_transicao": log_transicao,
                "hidden_email": True,
            },
        )

        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Solicitação de Alteração do Cronograma {self.numero}",
            corpo="",
            html=html,
            emails=PartesInteressadasService.usuarios_por_perfis(
                "DILOG_CRONOGRAMA", somente_email=True
            ),
        )

    @xworkflows.after_transition("fornecedor_solicita_alteracao")
    def _fornecedor_solicita_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.FORNECEDOR_SOLICITA_ALTERACAO_CRONOGRAMA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )
        self._envia_email_solicita_alteracao_para_cronograma(user)

    @xworkflows.after_transition("codae_realiza_alteracao")
    def _codae_realiza_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.CODAE_ALTERA_CRONOGRAMA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("cronograma_assina")
    def _cronograma_assina_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELO_USUARIO_CRONOGRAMA,
                usuario=user,
            )

    @xworkflows.after_transition("dilog_abastecimento_assina")
    def _dilog_abastecimento_assina_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELO_DILOG_ABASTECIMENTO,
                usuario=user,
            )

            url_detalhe_cronograma = (
                f"/pre-recebimento/detalhe-cronograma?uuid={self.uuid}"
            )

            contexto = {
                "numero_cronograma": self.numero,
                "nome_produto": self.ficha_tecnica.produto.nome,
                "nome_usuario": user.nome,
                "registro_funcional": user.registro_funcional,
                "data_evento": self.log_mais_recente.criado_em.strftime("%d/%m/%Y"),
                "url_detalhe_cronograma": base_url + url_detalhe_cronograma,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_assinatura_cronograma.html",
                contexto_template=contexto,
                titulo_notificacao=f"Cronograma {self.numero} assinado pelo Abastecimento",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_AVISO,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_CRONOGRAMA,
                link_acesse_aqui=url_detalhe_cronograma,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    [DILOG_CRONOGRAMA, DILOG_DIRETORIA]
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Assinatura do Cronograma {self.numero}\npelo Abastecimento",
                assunto=f"[SIGPAE] Assinatura do Cronograma {self.numero} pelo Abastecimento",
                template="pre_recebimento_email_assinatura_dilog_abastecimento.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    DILOG_DIRETORIA,
                    somente_email=True,
                ),
            )

    @xworkflows.after_transition("codae_assina")
    def _codae_assina_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELA_CODAE,
                usuario=user,
            )

            # Montar Notificação
            log_transicao = self.log_mais_recente
            usuarios = [
                *PartesInteressadasService.usuarios_por_perfis("DILOG_CRONOGRAMA"),
                *PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                    self
                ),
            ]
            template_notif = "pre_recebimento_notificacao_assinatura_codae.html"
            tipo = Notificacao.TIPO_NOTIFICACAO_AVISO
            titulo_notificacao = f"Cronograma {self.numero} assinado pela CODAE"
            link = f"/pre-recebimento/detalhe-cronograma?uuid={self.uuid}"
            self._cria_notificacao(
                template_notif, titulo_notificacao, usuarios, link, tipo, log_transicao
            )

            self._envia_email_notificacao_codae_assina_cronograma()

    def _envia_email_notificacao_codae_assina_cronograma(self):
        numero_cronograma = self.numero
        log_transicao = self.log_mais_recente
        url_cronograma = (
            f"{base_url}/pre-recebimento/detalhe-cronograma?uuid={self.uuid}"
        )

        html = render_to_string(
            template_name="pre_recebimento_email_assinatura_cronograma_codae.html",
            context={
                "titulo": f"Cronograma Assinado: Nº {numero_cronograma}",
                "numero_cronograma": numero_cronograma,
                "log_transicao": log_transicao,
                "url_cronograma": url_cronograma,
            },
        )

        partes_interessadas = PartesInteressadasService.usuarios_por_perfis(
            ["DILOG_CRONOGRAMA", "DILOG_ABASTECIMENTO"], True
        ) + PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
            self, True
        )

        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Assinatura do cronograma Nº {numero_cronograma}",
            emails=partes_interessadas,
            corpo="",
            html=html,
        )

    @xworkflows.after_transition("finaliza_solicitacao_alteracao")
    def _codae_finaliza_solicitacao_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELA_CODAE,
                usuario=user,
            )

    class Meta:
        abstract = True


class CronogramaAlteracaoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    SOLICITACAO_CRIADA = "SOLICITACAO_CRIADA"
    EM_ANALISE = "EM_ANALISE"
    ALTERACAO_ENVIADA_FORNECEDOR = "ALTERACAO_ENVIADA_FORNECEDOR"
    FORNECEDOR_CIENTE = "FORNECEDOR_CIENTE"
    CRONOGRAMA_CIENTE = "CRONOGRAMA_CIENTE"
    APROVADO_DILOG_ABASTECIMENTO = "APROVADO_DILOG_ABASTECIMENTO"
    REPROVADO_DILOG_ABASTECIMENTO = "REPROVADO_DILOG_ABASTECIMENTO"
    APROVADO_DILOG = "APROVADO_DILOG"
    REPROVADO_DILOG = "REPROVADO_DILOG"

    states = (
        (SOLICITACAO_CRIADA, "Solicitação criada"),
        (EM_ANALISE, "Em análise"),
        (ALTERACAO_ENVIADA_FORNECEDOR, "Alteração Enviada ao Fornecedor"),
        (FORNECEDOR_CIENTE, "Fornecedor Ciente"),
        (CRONOGRAMA_CIENTE, "Cronograma ciente"),
        (APROVADO_DILOG_ABASTECIMENTO, "Aprovado Abastecimento"),
        (REPROVADO_DILOG_ABASTECIMENTO, "Reprovado Abastecimento"),
        (APROVADO_DILOG, "Aprovado DILOG"),
        (REPROVADO_DILOG, "Reprovado DILOG"),
    )

    transitions = (
        ("inicia_fluxo", SOLICITACAO_CRIADA, EM_ANALISE),
        ("inicia_fluxo_codae", SOLICITACAO_CRIADA, ALTERACAO_ENVIADA_FORNECEDOR),
        ("fornecedor_ciente", ALTERACAO_ENVIADA_FORNECEDOR, FORNECEDOR_CIENTE),
        ("cronograma_ciente", EM_ANALISE, CRONOGRAMA_CIENTE),
        ("dilog_abastecimento_aprova", CRONOGRAMA_CIENTE, APROVADO_DILOG_ABASTECIMENTO),
        (
            "dilog_abastecimento_reprova",
            CRONOGRAMA_CIENTE,
            REPROVADO_DILOG_ABASTECIMENTO,
        ),
        (
            "dilog_aprova",
            [APROVADO_DILOG_ABASTECIMENTO, REPROVADO_DILOG_ABASTECIMENTO],
            APROVADO_DILOG,
        ),
        (
            "dilog_reprova",
            [APROVADO_DILOG_ABASTECIMENTO, REPROVADO_DILOG_ABASTECIMENTO],
            REPROVADO_DILOG,
        ),
    )

    initial_state = SOLICITACAO_CRIADA


class FluxoAlteracaoCronograma(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = CronogramaAlteracaoWorkflow
    status = xwf_models.StateField(workflow_class)

    def _preenche_template(self, template_notif, log_transicao, perfil=None):
        texto_notificacao = render_to_string(
            template_name=template_notif,
            context={
                "solicitacao": self.numero_solicitacao,
                "log_transicao": log_transicao,
                "objeto": self,
                "numero_cronograma": self.cronograma.numero,
                "fornecedor": log_transicao.usuario.nome,
            },
        )
        return texto_notificacao

    def _cria_notificacao(
        self,
        template_notif,
        titulo_notif,
        usuarios,
        link,
        tipo,
        categoria_notif,
        log_transicao=None,
    ):
        if usuarios:
            for usuario in usuarios:
                Notificacao.notificar(
                    tipo=tipo,
                    categoria=categoria_notif,
                    titulo=titulo_notif,
                    descricao=self._preenche_template(
                        template_notif, log_transicao, usuario.vinculo_atual.perfil.nome
                    ),
                    usuario=usuario,
                    link=link,
                    cronograma=self,
                )

    def _envia_email_notificacao_alteracao_cronograma_codae(self):
        numero_cronograma = self.cronograma.numero
        log_transicao = self.log_mais_recente
        url_solicitacao_alteracao = (
            f"{base_url}/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        )

        html = render_to_string(
            template_name="pre_recebimento_notificacao_alteracao_cronograma_codae.html",
            context={
                "titulo": f"Alteração do Cronograma {numero_cronograma}",
                "numero_cronograma": numero_cronograma,
                "log_transicao": log_transicao,
                "url_solicitacao_alteracao": url_solicitacao_alteracao,
            },
        )

        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Alteração do Cronograma {numero_cronograma}",
            corpo="",
            html=html,
            emails=PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                self.cronograma, somente_email=True
            ),
        )

    def _envia_email_notificacao_ciencia_fornecedor(self, user):
        numero_cronograma = self.cronograma.numero
        url_solicitacao_alteracao = (
            f"{base_url}/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        )
        log_transicao = self.log_mais_recente

        html = render_to_string(
            template_name="pre_recebimento_notificacao_alteracao_cronograma_codae_ciencia_fornecedor.html",
            context={
                "titulo": f"Solicitação de Alteração do Cronograma {numero_cronograma}",
                "numero_cronograma": numero_cronograma,
                "url_solicitacao_alteracao": url_solicitacao_alteracao,
                "fornecedor": user.nome,
                "log_transicao": log_transicao,
            },
        )

        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Ciência da Alteração do Cronograma {numero_cronograma}",
            corpo="",
            html=html,
            emails=PartesInteressadasService.usuarios_por_perfis(
                nomes_perfis=[
                    "DILOG_CRONOGRAMA",
                    "DILOG_ABASTECIMENTO",
                    "DILOG_DIRETORIA",
                ],
                somente_email=True,
            ),
        )

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.SOLICITACAO_ALTERACAO_CRONOGRAMA_EM_ANALISE,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )

    @xworkflows.after_transition("inicia_fluxo_codae")
    def _inicia_fluxo_codae_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.ALTERACAO_CRONOGRAMA_ENVIADA_AO_FORNECEDOR,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )

        template = "pre_recebimento_notificacao_solicitacao_cronograma_codae.html"
        titulo_notificacao = f"Alteração do Cronograma Nº {self.cronograma.numero}"
        usuarios = PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
            self.cronograma
        )
        link = f"/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
        log_transicao = self.log_mais_recente
        categoria_notificacao = Notificacao.CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA
        self._cria_notificacao(
            template,
            titulo_notificacao,
            usuarios,
            link,
            tipo,
            categoria_notificacao,
            log_transicao,
        )

        self._envia_email_notificacao_alteracao_cronograma_codae()

    @xworkflows.after_transition("cronograma_ciente")
    def _cronograma_ciente_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.CRONOGRAMA_CIENTE_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )

            # Montar Notificação
            log_transicao = self.log_mais_recente
            usuarios = PartesInteressadasService.usuarios_por_perfis(
                "DILOG_ABASTECIMENTO"
            )
            template_notif = (
                "pre_recebimento_notificacao_solicitacao_cronograma_ciente.html"
            )
            tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
            titulo_notificacao = (
                f" Solicitação de Alteração do Cronograma Nº {self.cronograma.numero}"
            )
            link = f"/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
            categoria_notificacao = (
                Notificacao.CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA
            )
            self._cria_notificacao(
                template_notif,
                titulo_notificacao,
                usuarios,
                link,
                tipo,
                categoria_notificacao,
                log_transicao,
            )

    @xworkflows.after_transition("fornecedor_ciente")
    def _fornecedor_ciente_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FORNECEDOR_CIENTE_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )
            log_transicao = self.log_mais_recente
            usuarios = PartesInteressadasService.usuarios_por_perfis(
                ["DILOG_CRONOGRAMA", "DILOG_ABASTECIMENTO", "DILOG_DIRETORIA"]
            )
            template_notif = "pre_recebimento_notificacao_alteracao_cronograma_codae_ciencia_fornecedor.html"
            tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
            titulo_notificacao = f"Ciência da Alteração do Cronograma Nº {self.cronograma.numero} pelo Fornecedor"
            link = f"/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
            categoria_notificacao = (
                Notificacao.CATEGORIA_NOTIFICACAO_ALTERACAO_CRONOGRAMA
            )
            self._cria_notificacao(
                template_notif,
                titulo_notificacao,
                usuarios,
                link,
                tipo,
                categoria_notificacao,
                log_transicao,
            )
            self._envia_email_notificacao_ciencia_fornecedor(user)

    def _montar_dilog_abastecimento_notificacao(self):
        log_transicao = self.log_mais_recente
        usuarios = PartesInteressadasService.usuarios_por_perfis("DILOG_DIRETORIA")
        template_notif = (
            "pre_recebimento_notificacao_solicitacao_parecer_dilog_abastecimento.html"
        )
        tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
        titulo_notificacao = (
            f" Solicitação de Alteração do Cronograma Nº {self.cronograma.numero}"
        )
        link = f"/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        categoria_notificacao = (
            Notificacao.CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA
        )
        self._cria_notificacao(
            template_notif,
            titulo_notificacao,
            usuarios,
            link,
            tipo,
            categoria_notificacao,
            log_transicao,
        )

    @xworkflows.after_transition("dilog_abastecimento_aprova")
    def _dilog_abastecimento_aprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.APROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )
            self._montar_dilog_abastecimento_notificacao()

    @xworkflows.after_transition("dilog_abastecimento_reprova")
    def _dilog_abastecimento_reprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.REPROVADO_DILOG_ABASTECIMENTO_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )
            self._montar_dilog_abastecimento_notificacao()

    def _montar_dilog_notificacao(self):
        log_transicao = self.log_mais_recente
        usuarios = [
            *PartesInteressadasService.usuarios_por_perfis(
                ["DILOG_ABASTECIMENTO", "DILOG_CRONOGRAMA"]
            ),
            *PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                self.cronograma
            ),
        ]
        template_notif = "pre_recebimento_notificacao_solicitacao_parecer_codae.html"
        tipo = Notificacao.TIPO_NOTIFICACAO_ALERTA
        titulo_notificacao = (
            f" Solicitação de Alteração do Cronograma Nº {self.cronograma.numero}"
        )
        link = f"/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        categoria_notificacao = (
            Notificacao.CATEGORIA_NOTIFICACAO_SOLICITACAO_ALTERACAO_CRONOGRAMA
        )
        self._cria_notificacao(
            template_notif,
            titulo_notificacao,
            usuarios,
            link,
            tipo,
            categoria_notificacao,
            log_transicao,
        )

    def _envia_email_notificacao_retorno_codae_alteracao_cronograma(
        self, status_analise
    ):
        numero_cronograma = self.cronograma.numero
        log_transicao = self.log_mais_recente
        url_solicitacao_alteracao = (
            f"{base_url}/pre-recebimento/detalhe-alteracao-cronograma?uuid={self.uuid}"
        )

        html = render_to_string(
            template_name="pre_recebimento_email_solicitacao_cronograma_parecer_codae.html",
            context={
                "titulo": f"Retorno Solicitação de Alteração do Cronograma {numero_cronograma}",
                "numero_cronograma": numero_cronograma,
                "log_transicao": log_transicao,
                "status_analise": status_analise,
                "url_solicitacao_alteracao": url_solicitacao_alteracao,
            },
        )

        partes_interessadas = (
            PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                self.cronograma, True
            )
            + PartesInteressadasService.usuarios_por_perfis(
                ["DILOG_CRONOGRAMA", "DILOG_ABASTECIMENTO"], True
            )
        )

        envia_email_em_massa_task.delay(
            assunto=f"[SIGPAE] Retorno Solicitação de Alteração do Cronograma {numero_cronograma}",
            emails=partes_interessadas,
            corpo="",
            html=html,
        )

    @xworkflows.after_transition("dilog_aprova")
    def _dilog_aprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.APROVADO_DILOG_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )
            self._montar_dilog_notificacao()
            self._envia_email_notificacao_retorno_codae_alteracao_cronograma("APROVOU")

    @xworkflows.after_transition("dilog_reprova")
    def _dilog_reprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.REPROVADO_DILOG_SOLICITACAO_ALTERACAO,
                usuario=user,
                justificativa=kwargs.get("justificativa", ""),
            )
            self._montar_dilog_notificacao()
            self._envia_email_notificacao_retorno_codae_alteracao_cronograma("REPROVOU")

    class Meta:
        abstract = True


class NotificacaoOcorrenciaWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"
    NOTIFICACAO_CRIADA = "NOTIFICACAO_CRIADA"
    NOTIFICACAO_ENVIADA_FISCAL = "NOTIFICACAO_ENVIADA_FISCAL"
    NOTIFICACAO_SOLICITADA_ALTERACAO = "NOTIFICACAO_SOLICITADA_ALTERACAO"
    NOTIFICACAO_ASSINADA_FISCAL = "NOTIFICACAO_ASSINADA_FISCAL"

    states = (
        (RASCUNHO, "Rascunho"),
        (NOTIFICACAO_CRIADA, "Notificação Criada"),
        (NOTIFICACAO_ENVIADA_FISCAL, "Notificação Enviada Fiscal"),
        (NOTIFICACAO_SOLICITADA_ALTERACAO, "Solicitado Alteração"),
        (NOTIFICACAO_ASSINADA_FISCAL, "Assinada Fiscal"),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, RASCUNHO),
        ("cria_notificacao", RASCUNHO, NOTIFICACAO_CRIADA),
        ("envia_fiscal", NOTIFICACAO_CRIADA, NOTIFICACAO_ENVIADA_FISCAL),
        (
            "solicita_alteracao",
            NOTIFICACAO_ENVIADA_FISCAL,
            NOTIFICACAO_SOLICITADA_ALTERACAO,
        ),
        ("assina_fiscal", NOTIFICACAO_ENVIADA_FISCAL, NOTIFICACAO_ASSINADA_FISCAL),
    )

    initial_state = RASCUNHO


class FluxoNotificacaoOcorrencia(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = NotificacaoOcorrenciaWorkflow
    status = xwf_models.StateField(workflow_class)

    @xworkflows.after_transition("cria_notificacao")
    def _cria_notificacao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.NOTIFICACAO_CRIADA,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("envia_fiscal")
    def _envia_fiscal_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.NOTIFICACAO_ENVIADA_FISCAL,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("solicita_alteracao")
    def _solicita_alteracao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.NOTIFICACAO_SOLICITADA_ALTERACAO,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    @xworkflows.after_transition("assina_fiscal")
    def _assina_fiscal_hook(self, *args, **kwargs):
        user = kwargs["user"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.NOTIFICACAO_ASSINADA_FISCAL,
            usuario=user,
            justificativa=kwargs.get("justificativa", ""),
        )

    class Meta:
        abstract = True


class LayoutDeEmbalagemWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    LAYOUT_CRIADO = "LAYOUT_CRIADO"
    ENVIADO_PARA_ANALISE = "ENVIADO_PARA_ANALISE"
    APROVADO = "APROVADO"
    SOLICITADO_CORRECAO = "SOLICITADO_CORRECAO"

    states = (
        (LAYOUT_CRIADO, "Layout Criado"),
        (ENVIADO_PARA_ANALISE, "Enviado para Análise"),
        (APROVADO, "Aprovado"),
        (SOLICITADO_CORRECAO, "Solicitado Correção"),
    )

    transitions = (
        ("inicia_fluxo", LAYOUT_CRIADO, ENVIADO_PARA_ANALISE),
        ("codae_aprova", ENVIADO_PARA_ANALISE, APROVADO),
        (
            "codae_solicita_correcao",
            [ENVIADO_PARA_ANALISE, APROVADO],
            SOLICITADO_CORRECAO,
        ),
        ("fornecedor_realiza_correcao", SOLICITADO_CORRECAO, ENVIADO_PARA_ANALISE),
        ("fornecedor_atualiza", APROVADO, ENVIADO_PARA_ANALISE),
    )

    initial_state = LAYOUT_CRIADO


class FluxoLayoutDeEmbalagem(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = LayoutDeEmbalagemWorkflow
    status = xwf_models.StateField(workflow_class)

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.LAYOUT_ENVIADO_PARA_ANALISE,
                usuario=user,
            )

            nome_empresa = self.ficha_tecnica.empresa.nome_fantasia
            data_envio = self.log_mais_recente.criado_em.strftime("%d/%m/%Y")
            numero_ficha = self.ficha_tecnica.numero
            url_layout_embalagens = (
                f"/pre-recebimento/analise-layout-embalagem?uuid={self.uuid}"
            )
            perfis_interessados = [
                constants.DILOG_QUALIDADE,
                constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                constants.COORDENADOR_GESTAO_PRODUTO,
            ]

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_fornecedor_envia_layout_embalagem.html",
                contexto_template={
                    "numero_ficha": numero_ficha,
                    "nome_produto": self.ficha_tecnica.produto.nome,
                    "nome_usuario_empresa": user.nome,
                    "cpf_usuario_empresa": user.cpf_formatado_e_censurado,
                },
                titulo_notificacao=f"Layout de Embalagens enviado em {data_envio} pelo Fornecedor {nome_empresa}",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_ALERTA,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS,
                link_acesse_aqui=url_layout_embalagens,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    perfis_interessados
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Layouts Pendentes de Aprovação\nFicha Técnica {numero_ficha}",
                assunto=f"[SIGPAE] Layouts Pendentes de Aprovação | Ficha Técnica {numero_ficha}",
                template="pre_recebimento_email_fornecedor_envia_layout_embalagem.html",
                contexto_template={
                    "nome_empresa": nome_empresa,
                    "numero_ficha": numero_ficha,
                    "data_envio": data_envio,
                    "url_layout_embalagens": base_url + url_layout_embalagens,
                },
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    perfis_interessados, somente_email=True
                ),
            )

    @xworkflows.after_transition("codae_aprova")
    def _codae_aprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.LAYOUT_APROVADO, usuario=user
            )

    @xworkflows.after_transition("codae_solicita_correcao")
    def _codae_solicita_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.LAYOUT_SOLICITADO_CORRECAO,
                usuario=user,
            )

            numero_ficha = self.ficha_tecnica.numero
            url_corrigir_layout_embalagens = (
                f"/pre-recebimento/corrigir-layout-embalagem?uuid={self.uuid}"
            )

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_codae_solicita_correcao_layout_embalagem.html",
                contexto_template={
                    "numero_ficha": numero_ficha,
                    "nome_produto": self.ficha_tecnica.produto.nome,
                },
                titulo_notificacao=(
                    "Solicitação de Alteração do Layout de Embalagens referente a Ficha Técnica "
                    + f"{numero_ficha}"
                ),
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_ALERTA,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS,
                link_acesse_aqui=url_corrigir_layout_embalagens,
                usuarios=PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                    self.ficha_tecnica
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Solicitação de Correção Layout de Embalagens {numero_ficha}",
                assunto=f"[SIGPAE] Solicitação de Correção Layout de Embalagens {numero_ficha}",
                template="pre_recebimento_email_codae_solicita_correcao_layout_embalagem.html",
                contexto_template={
                    "numero_ficha": numero_ficha,
                    "data_solicitacao": self.log_mais_recente.criado_em.strftime(
                        "%d/%m/%Y"
                    ),
                    "url_layout_embalagens": base_url + url_corrigir_layout_embalagens,
                },
                destinatarios=PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                    self.ficha_tecnica, somente_email=True
                ),
            )

    @xworkflows.after_transition("fornecedor_realiza_correcao")
    def _fornecedor_realiza_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.LAYOUT_CORRECAO_REALIZADA,
                usuario=user,
            )
            self._notificar_correcao_ou_atualizacao(user)

    @xworkflows.after_transition("fornecedor_atualiza")
    def _fornecedor_atualiza_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.LAYOUT_ATUALIZADO, usuario=user
            )
            self._notificar_correcao_ou_atualizacao(user)

    def _notificar_correcao_ou_atualizacao(self, usuario):
        data_envio = self.log_mais_recente.criado_em.strftime("%d/%m/%Y")
        nome_empresa = self.ficha_tecnica.empresa
        perfis_interessados = [
            constants.DILOG_QUALIDADE,
            constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
            constants.COORDENADOR_GESTAO_PRODUTO,
        ]

        template = (
            "pre_recebimento_notificacao_fornecedor_corrige_ou_atualiza_layout_embalagem.html",
        )
        contexto_template = {
            "numero_ficha": self.ficha_tecnica.numero,
            "nome_produto": self.ficha_tecnica.produto.nome,
            "nome_usuario_empresa": usuario.nome,
            "cpf_usuario_empresa": usuario.cpf_formatado_e_censurado,
        }
        titulo_notificacao = f"Layout de Embalagens atualizados e enviados em {data_envio} pelo Fornecedor {nome_empresa}"
        tipo_notificacao = Notificacao.TIPO_NOTIFICACAO_ALERTA
        categoria_notificacao = Notificacao.CATEGORIA_NOTIFICACAO_LAYOUT_DE_EMBALAGENS
        link_acesse_aqui = f"/pre-recebimento/analise-layout-embalagem?uuid={self.uuid}"
        usuarios = PartesInteressadasService.usuarios_por_perfis(perfis_interessados)

        preencher_template_e_notificar(
            template=template,
            contexto_template=contexto_template,
            titulo_notificacao=titulo_notificacao,
            tipo_notificacao=tipo_notificacao,
            categoria_notificacao=categoria_notificacao,
            link_acesse_aqui=link_acesse_aqui,
            usuarios=usuarios,
        )

    class Meta:
        abstract = True


class DocumentoDeRecebimentoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    DOCUMENTO_CRIADO = "DOCUMENTO_CRIADO"
    ENVIADO_PARA_ANALISE = "ENVIADO_PARA_ANALISE"
    ENVIADO_PARA_CORRECAO = "ENVIADO_PARA_CORRECAO"
    APROVADO = "APROVADO"

    states = (
        (DOCUMENTO_CRIADO, "Documento Criado"),
        (ENVIADO_PARA_ANALISE, "Enviado para Análise"),
        (ENVIADO_PARA_CORRECAO, "Enviado para Correção"),
        (APROVADO, "Aprovado"),
    )

    transitions = (
        ("inicia_fluxo", DOCUMENTO_CRIADO, ENVIADO_PARA_ANALISE),
        ("qualidade_solicita_correcao", ENVIADO_PARA_ANALISE, ENVIADO_PARA_CORRECAO),
        ("qualidade_aprova_analise", ENVIADO_PARA_ANALISE, APROVADO),
        ("fornecedor_realiza_correcao", ENVIADO_PARA_CORRECAO, ENVIADO_PARA_ANALISE),
        ("fornecedor_atualiza", APROVADO, ENVIADO_PARA_ANALISE),
    )

    initial_state = DOCUMENTO_CRIADO


class FluxoDocumentoDeRecebimento(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = DocumentoDeRecebimentoWorkflow
    status = xwf_models.StateField(workflow_class)

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DOCUMENTO_ENVIADO_PARA_ANALISE,
                usuario=user,
            )

            numero_cronograma = self.cronograma.numero
            url_documento_recebimento = (
                f"/pre-recebimento/analise-documento-recebimento?uuid={self.uuid}"
            )
            contexto = {
                "numero_cronograma": numero_cronograma,
                "nome_empresa": self.cronograma.empresa.nome_fantasia,
                "nome_produto": self.cronograma.ficha_tecnica.produto.nome,
                "data_envio": self.log_mais_recente.criado_em.strftime("%d/%m/%Y"),
                "nome_usuario_empresa": user.nome,
                "cpf_usuario_empresa": user.cpf_formatado_e_censurado,
                "url_documento_recebimento": base_url + url_documento_recebimento,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_fornecedor_envia_documento_recebimento.html",
                contexto_template=contexto,
                titulo_notificacao=f"Documentos do Cronograma {numero_cronograma} foram Enviados para Análise",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_ALERTA,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO,
                link_acesse_aqui=url_documento_recebimento,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    [
                        constants.DILOG_QUALIDADE,
                        constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Documentos de Recebimento Pendentes de Aprovação Cronograma Nº {numero_cronograma}",
                assunto=f"[SIGPAE] Documentos de Recebimento Pendentes de Aprovação | Cronograma Nº {numero_cronograma}",
                template="pre_recebimento_email_fornecedor_envia_documento_recebimento.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    nomes_perfis=[
                        constants.DILOG_QUALIDADE,
                        constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ],
                    somente_email=True,
                ),
            )

    @xworkflows.after_transition("qualidade_solicita_correcao")
    def _qualidade_solicita_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        justificativa = kwargs["justificativa"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DOCUMENTO_ENVIADO_PARA_CORRECAO,
                usuario=user,
                justificativa=justificativa,
            )

            numero_cronograma = self.cronograma.numero
            url_documento_recebimento = (
                f"/pre-recebimento/corrigir-documentos-recebimento?uuid={self.uuid}"
            )
            contexto = {
                "numero_cronograma": numero_cronograma,
                "nome_produto": self.cronograma.ficha_tecnica.produto.nome,
                "data_solicitacao": self.log_mais_recente.criado_em.strftime(
                    "%d/%m/%Y"
                ),
                "url_documento_recebimento": base_url + url_documento_recebimento,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_codae_solicita_correcao_documento_recebimento.html",
                contexto_template=contexto,
                titulo_notificacao=f"Documentos do Cronograma {numero_cronograma} foram Enviados para correção",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_ALERTA,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO,
                link_acesse_aqui=url_documento_recebimento,
                usuarios=PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                    self.cronograma
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Solicitação de Correção Documentos de Recebimento Cronograma Nº {numero_cronograma}",
                assunto=f"[SIGPAE] Solicitação de Correção Documentos de Recebimento do Cronograma Nº {numero_cronograma}",
                template="pre_recebimento_email_codae_solicita_correcao_documento_recebimento.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_vinculados_a_empresa_do_objeto(
                    self.cronograma, somente_email=True
                ),
            )

    @xworkflows.after_transition("qualidade_aprova_analise")
    def _qualidade_aprova_analise_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DOCUMENTO_APROVADO, usuario=user
            )

    @xworkflows.after_transition("fornecedor_realiza_correcao")
    def _fornecedor_realiza_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DOCUMENTO_CORRECAO_REALIZADA,
                usuario=user,
            )

            numero_cronograma = self.cronograma.numero
            url_documento_recebimento = (
                f"/pre-recebimento/analise-documento-recebimento?uuid={self.uuid}"
            )
            contexto = {
                "numero_cronograma": numero_cronograma,
                "nome_empresa": self.cronograma.empresa.nome_fantasia,
                "nome_produto": self.cronograma.ficha_tecnica.produto.nome,
                "nome_usuario_empresa": user.nome,
                "cpf_usuario_empresa": user.cpf_formatado_e_censurado,
                "data_envio": self.log_mais_recente.criado_em.strftime("%d/%m/%Y"),
                "url_documento_recebimento": base_url + url_documento_recebimento,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_fornecedor_corrige_documento_recebimento.html",
                contexto_template=contexto,
                titulo_notificacao=f"Documentos do Cronograma {numero_cronograma} foram corrigidos",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_AVISO,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO,
                link_acesse_aqui=url_documento_recebimento,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    constants.DILOG_QUALIDADE
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Documentos de Recebimento Corrigidos e Pendentes de Aprovação\nCronograma {numero_cronograma}",
                assunto=f"[SIGPAE] Documentos de Recebimento Corrigidos e Pendentes de Aprovação | Cronograma Nº {numero_cronograma}",
                template="pre_recebimento_email_fornecedor_corrige_documento_recebimento.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    nomes_perfis=[
                        constants.DILOG_QUALIDADE,
                        constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ],
                    somente_email=True,
                ),
            )

    @xworkflows.after_transition("fornecedor_atualiza")
    def _fornecedor_atualiza_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.DOCUMENTO_ENVIADO_PARA_ANALISE,
                usuario=user,
            )

            numero_cronograma = self.cronograma.numero
            url_documento_recebimento = (
                f"/pre-recebimento/analise-documento-recebimento?uuid={self.uuid}"
            )
            contexto = {
                "numero_cronograma": numero_cronograma,
                "nome_empresa": self.cronograma.empresa.nome_fantasia,
                "nome_produto": (
                    self.cronograma.ficha_tecnica.produto.nome
                    if self.cronograma.ficha_tecnica
                    else "-"
                ),
                "nome_usuario_empresa": user.nome,
                "cpf_usuario_empresa": user.cpf_formatado_e_censurado,
                "data_envio": self.log_mais_recente.criado_em.strftime("%d/%m/%Y"),
                "url_documento_recebimento": base_url + url_documento_recebimento,
            }

            EmailENotificacaoService.enviar_notificacao(
                template="pre_recebimento_notificacao_fornecedor_envia_documento_recebimento.html",
                contexto_template=contexto,
                titulo_notificacao=f"Documentos do Cronograma {numero_cronograma} foram Enviados para Análise",
                tipo_notificacao=Notificacao.TIPO_NOTIFICACAO_ALERTA,
                categoria_notificacao=Notificacao.CATEGORIA_NOTIFICACAO_DOCUMENTOS_DE_RECEBIMENTO,
                link_acesse_aqui=url_documento_recebimento,
                usuarios=PartesInteressadasService.usuarios_por_perfis(
                    [
                        constants.DILOG_QUALIDADE,
                        constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                ),
            )

            EmailENotificacaoService.enviar_email(
                titulo=f"Documentos de Recebimento Pendentes de Aprovação Cronograma Nº {numero_cronograma}",
                assunto=f"[SIGPAE] Documentos de Recebimento Pendentes de Aprovação | Cronograma Nº {numero_cronograma}",
                template="pre_recebimento_email_fornecedor_envia_documento_recebimento.html",
                contexto_template=contexto,
                destinatarios=PartesInteressadasService.usuarios_por_perfis(
                    nomes_perfis=[
                        constants.DILOG_QUALIDADE,
                        constants.COORDENADOR_CODAE_DILOG_LOGISTICA,
                        constants.DILOG_DIRETORIA,
                        constants.ADMINISTRADOR_CODAE_GABINETE,
                    ],
                    somente_email=True,
                ),
            )

    class Meta:
        abstract = True


class FichaTecnicaDoProdutoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    RASCUNHO = "RASCUNHO"
    ENVIADA_PARA_ANALISE = "ENVIADA_PARA_ANALISE"
    APROVADA = "APROVADA"
    ENVIADA_PARA_CORRECAO = "ENVIADA_PARA_CORRECAO"

    states = (
        (RASCUNHO, "Rascunho"),
        (ENVIADA_PARA_ANALISE, "Enviada para Análise"),
        (APROVADA, "Aprovada"),
        (ENVIADA_PARA_CORRECAO, "Enviada para Correção"),
    )

    transitions = (
        ("inicia_fluxo", RASCUNHO, ENVIADA_PARA_ANALISE),
        ("gpcodae_aprova", ENVIADA_PARA_ANALISE, APROVADA),
        ("gpcodae_envia_para_correcao", ENVIADA_PARA_ANALISE, ENVIADA_PARA_CORRECAO),
        ("fornecedor_corrige", ENVIADA_PARA_CORRECAO, ENVIADA_PARA_ANALISE),
        ("fornecedor_atualiza", APROVADA, ENVIADA_PARA_ANALISE),
    )

    initial_state = RASCUNHO


class FluxoFichaTecnicaDoProduto(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = FichaTecnicaDoProdutoWorkflow
    status = xwf_models.StateField(workflow_class)

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_ANALISE,
                usuario=user,
            )

    @xworkflows.after_transition("gpcodae_aprova")
    def _gpcodae_aprova_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_APROVADA,
                usuario=user,
            )

    @xworkflows.after_transition("gpcodae_envia_para_correcao")
    def _gpcodae_envia_para_correcao_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_CORRECAO,
                usuario=user,
            )

    @xworkflows.after_transition("fornecedor_corrige")
    def _fornecedor_corrige_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_ANALISE,
                usuario=user,
            )

    @xworkflows.after_transition("fornecedor_atualiza")
    def _fornecedor_atualiza_hook(self, *args, **kwargs):
        user = kwargs["user"]
        if user:
            self.salvar_log_transicao(
                status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_ANALISE,
                usuario=user,
            )

    class Meta:
        abstract = True


class FormularioSupervisaoWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    EM_PREENCHIMENTO = "EM_PREENCHIMENTO"
    NUTRIMANIFESTACAO_A_VALIDAR = "NUTRIMANIFESTACAO_A_VALIDAR"
    COM_COMENTARIOS_DE_CODAE = "COM_COMENTARIOS_DE_CODAE"
    VALIDADO_POR_CODAE = "VALIDADO_POR_CODAE"
    APROVADO = "APROVADO"

    states = (
        (EM_PREENCHIMENTO, "Em Preenchimento"),
        (NUTRIMANIFESTACAO_A_VALIDAR, "Enviado para CODAE"),
        (COM_COMENTARIOS_DE_CODAE, "Com comentários de CODAE"),
        (VALIDADO_POR_CODAE, "Validado pela CODAE"),
        (APROVADO, "Aprovado"),
    )

    transitions = (("inicia_fluxo", EM_PREENCHIMENTO, NUTRIMANIFESTACAO_A_VALIDAR),)

    initial_state = EM_PREENCHIMENTO


class FluxoFormularioSupervisao(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = FormularioSupervisaoWorkflow
    status = xwf_models.StateField(workflow_class)

    @xworkflows.after_transition("inicia_fluxo")
    def _inicia_fluxo_hook(self, *args, **kwargs):
        usuario = kwargs["usuario"]
        self.salvar_log_transicao(
            status_evento=LogSolicitacoesUsuario.RELATORIO_ENVIADO_PARA_CODAE,
            usuario=usuario,
            justificativa=kwargs.get("justificativa", ""),
        )

    @property
    def em_preenchimento(self):
        return self.status == FormularioSupervisaoWorkflow.EM_PREENCHIMENTO

    class Meta:
        abstract = True


class RelatorioFinanceiroMedicaoInicialWorkflow(xwf_models.Workflow):
    log_model = ""  # Disable logging to database

    EM_ANALISE = "EM_ANALISE"

    states = ((EM_ANALISE, "Em análise"),)

    transitions = ()

    initial_state = EM_ANALISE


class FluxoRelatorioFinanceiroMedicaoInicial(xwf_models.WorkflowEnabled, models.Model):
    workflow_class = RelatorioFinanceiroMedicaoInicialWorkflow
    status = xwf_models.StateField(workflow_class)

    class Meta:
        abstract = True
