from datetime import date

from django.template.loader import render_to_string

from src.dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from src.dados_comuns.fluxo_status import DietaEspecialWorkflow
from src.dados_comuns.utils import envia_email_unico
from src.dieta_especial.logs_models.models import (
    LogDietasAtivasCanceladasAutomaticamente,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)
from src.escola.models import Aluno
from src.paineis_consolidados.models import SolicitacoesCODAE
from src.perfil.models import Usuario


def _dietas_especiais_a_terminar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_termino__lt=date.today(),
        ativo=True,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )


def termina_dietas_especiais(usuario):
    for solicitacao in _dietas_especiais_a_terminar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"):
            solicitacao.dieta_alterada.ativo = True
            solicitacao.dieta_alterada.save()
        solicitacao.termina(usuario)


def _dietas_especiais_a_iniciar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=date.today(),
        ativo=False,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )


def inicia_dietas_temporarias():
    for solicitacao in _dietas_especiais_a_iniciar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"):
            solicitacao.dieta_alterada.ativo = False
            solicitacao.dieta_alterada.save()
            solicitacao.ativo = True
            solicitacao.save()


def _cancelar_dieta_encerramento_matricula(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.sistema_cancela_aluno_encerramento_matricula(user=usuario_admin)
    dieta.save()


def cancela_dietas_pendente_autorizacao():
    dietas_pendentes = (
        SolicitacoesCODAE.get_pendentes_dieta_especial()
        .filter(tipo_solicitacao_dieta="COMUM")
        .order_by("pk")
        .distinct("pk")
    )
    for dieta in dietas_pendentes:
        aluno = Aluno.objects.filter(codigo_eol=dieta.codigo_eol_aluno).first()
        solicitacao_dieta = SolicitacaoDietaEspecial.objects.filter(pk=dieta.pk).first()
        if aluno.escola != solicitacao_dieta.escola_destino:
            _cancelar_dieta_encerramento_matricula(solicitacao_dieta)


def _gerar_log_dietas_ativas_canceladas_automaticamente(
    dieta, dados, fora_da_rede=False
):
    data = dict(
        dieta=dieta,
        codigo_eol_aluno=dados["codigo_eol_aluno"],
        nome_aluno=dados["nome_aluno"],
        codigo_eol_escola_destino=dados.get("codigo_eol_escola_origem"),
        nome_escola_destino=dados.get("nome_escola_origem"),
        codigo_eol_escola_origem=dados.get("codigo_eol_escola_destino"),
        nome_escola_origem=dados.get("nome_escola_destino"),
    )
    if fora_da_rede:
        data["codigo_eol_escola_origem"] = dados.get("codigo_eol_escola_origem")
        data["nome_escola_origem"] = dados.get("nome_escola_origem")
        data["codigo_eol_escola_destino"] = ""
        data["nome_escola_destino"] = ""
    LogDietasAtivasCanceladasAutomaticamente.objects.create(**data)


def _cancelar_dieta(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_mudou_escola(user=usuario_admin)
    dieta.save()


def _cancelar_dieta_aluno_fora_da_rede(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_nao_pertence_rede(user=usuario_admin)
    dieta.save()


def _enviar_email_para_adm_terceirizada_e_escola(
    solicitacao_dieta, aluno, escola, fora_da_rede=False
):
    assunto = (
        f"Cancelamento Automático de Dieta Especial Nº {solicitacao_dieta.id_externo}"
    )
    hoje = date.today().strftime("%d/%m/%Y")
    template = (
        "email/email_dieta_cancelada_automaticamente_terceirizada_escola_destino.html"
    )
    justificativa_cancelamento = "por não pertencer a unidade educacional"
    if fora_da_rede:
        justificativa_cancelamento = "por não estar matriculado"
    dados_template = {
        "nome_aluno": aluno.nome,
        "codigo_eol_aluno": aluno.codigo_eol,
        "dieta_numero": solicitacao_dieta.id_externo,
        "nome_escola": escola.nome,
        "hoje": hoje,
        "justificativa_cancelamento": justificativa_cancelamento,
    }
    html = render_to_string(template, dados_template)
    emails_terceirizada = solicitacao_dieta.rastro_terceirizada.emails_por_modulo(
        "Dieta Especial"
    )
    email_escola = [escola.contato.email]
    email_lista = emails_terceirizada + email_escola
    for email in email_lista:
        envia_email_unico(
            assunto=assunto,
            corpo="",
            email=email,
            template=template,
            dados_template=dados_template,
            html=html,
        )


def _aluno_matriculado_em_outra_ue(aluno, solicitacao_dieta):
    if aluno.escola:
        return aluno.escola.codigo_eol != solicitacao_dieta.escola.codigo_eol
    return False


def cancela_dietas_ativas_automaticamente():
    dietas_ativas_comuns = (
        SolicitacoesCODAE.get_autorizados_dieta_especial()
        .filter(tipo_solicitacao_dieta="COMUM")
        .order_by("pk")
        .distinct("pk")
    )
    for dieta in dietas_ativas_comuns:
        aluno = Aluno.objects.filter(codigo_eol=dieta.codigo_eol_aluno).first()
        solicitacao_dieta = SolicitacaoDietaEspecial.objects.filter(pk=dieta.pk).first()
        if aluno.nao_matriculado:
            dados = dict(
                codigo_eol_aluno=aluno.codigo_eol,
                nome_aluno=aluno.nome,
                codigo_eol_escola_origem=solicitacao_dieta.escola.codigo_eol,
                nome_escola_origem=solicitacao_dieta.escola.nome,
            )
            _gerar_log_dietas_ativas_canceladas_automaticamente(
                solicitacao_dieta, dados, fora_da_rede=True
            )
            _cancelar_dieta_aluno_fora_da_rede(dieta=solicitacao_dieta)
            _enviar_email_para_adm_terceirizada_e_escola(
                solicitacao_dieta,
                aluno,
                escola=solicitacao_dieta.escola,
                fora_da_rede=True,
            )
        elif _aluno_matriculado_em_outra_ue(aluno, solicitacao_dieta):
            dados = dict(
                codigo_eol_aluno=aluno.codigo_eol,
                nome_aluno=aluno.nome,
                codigo_eol_escola_destino=aluno.escola.codigo_eol,
                nome_escola_destino=aluno.escola.nome,
                nome_escola_origem=solicitacao_dieta.escola.nome,
                codigo_eol_escola_origem=solicitacao_dieta.escola.codigo_eol,
            )
            _gerar_log_dietas_ativas_canceladas_automaticamente(
                solicitacao_dieta, dados
            )
            _cancelar_dieta(solicitacao_dieta)
            _enviar_email_para_adm_terceirizada_e_escola(
                solicitacao_dieta, aluno, escola=solicitacao_dieta.escola
            )
        else:
            continue
