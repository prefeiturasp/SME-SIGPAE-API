from unittest.mock import patch

from copy import deepcopy
from django.core.files.base import ContentFile
import pytest
import xworkflows
from rest_framework.exceptions import PermissionDenied, ValidationError

from sme_sigpae_api.dados_comuns.fluxo_status import (
    ReclamacaoProdutoWorkflow,
    SolicitacaoMedicaoInicialWorkflow,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, AnexoLogSolicitacoesUsuario
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma

pytestmark = pytest.mark.django_db


def test_codae_recusa_hook(reclamacao_produto, user_codae_produto):
    kwargs = {
        "user": user_codae_produto,
        "anexos": [],
        "justificativa": "Produto não atende os requisitos.",
    }
    assert (
        reclamacao_produto.status == ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
    )
    reclamacao_produto.codae_recusa(**kwargs)
    assert reclamacao_produto.status == ReclamacaoProdutoWorkflow.CODAE_RECUSOU


def test_codae_recusa_hook_exception(reclamacao_produto_codae_recusou):
    kwargs, reclamacao_produto = reclamacao_produto_codae_recusou
    with pytest.raises(xworkflows.base.InvalidTransitionError):
        reclamacao_produto.codae_recusa(**kwargs)
    assert reclamacao_produto.status == ReclamacaoProdutoWorkflow.CODAE_RECUSOU


def test_envia_email_recusa_reclamacao(dados_log_recusa):
    _, reclamacao_produto, log_recusa = dados_log_recusa
    reclamacao_produto._envia_email_recusa_reclamacao(log_recusa)
    assert reclamacao_produto.status == ReclamacaoProdutoWorkflow.CODAE_RECUSOU


def test_ue_envia_sem_lancamentos(solicitacao_sem_lancamento, user_diretor_escola):
    usuario, _ = user_diretor_escola
    justificativa = "Não houve aulas no período devido a reformas na escola."
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": justificativa,
    }

    solicitacao_sem_lancamento.ue_envia_sem_lancamentos(**kwargs)
    assert (
        solicitacao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )

    assert solicitacao_sem_lancamento.logs.count() == 1
    log = solicitacao_sem_lancamento.logs.first()
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE
    assert log.usuario == usuario
    assert log.justificativa == justificativa


def test_ue_envia_sem_lancamentos_usuario_sem_permissao(
    solicitacao_sem_lancamento, user_codae_produto
):
    kwargs = {
        "user": user_codae_produto,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    with pytest.raises(
        PermissionDenied, match="Você não tem permissão para executar essa ação."
    ):
        solicitacao_sem_lancamento.ue_envia_sem_lancamentos(**kwargs)


def test_ue_envia_sem_lancamentos_erro_validacao(
    medicao_sem_lancamento, user_diretor_escola
):
    usuario, _ = user_diretor_escola
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    with pytest.raises(
        ValidationError, match=r"`Medicao` não possui fluxo `ue_envia_sem_lancamentos`"
    ):
        medicao_sem_lancamento.ue_envia_sem_lancamentos(**kwargs)


def test_medicao_sem_lancamentos(medicao_sem_lancamento, user_diretor_escola):
    usuario, _ = user_diretor_escola
    justificativa = "Não houve aulas no período devido a reformas na escola."
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": justificativa,
    }
    medicao_sem_lancamento.medicao_sem_lancamentos(**kwargs)
    assert (
        medicao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS
    )

    solicitacao = medicao_sem_lancamento.solicitacao_medicao_inicial
    assert (
        solicitacao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )

    assert medicao_sem_lancamento.logs.count() == 1
    log = medicao_sem_lancamento.logs.first()
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_SEM_LANCAMENTOS
    assert log.usuario == usuario
    assert log.justificativa == justificativa


def test_medicao_sem_lancamentos_usuario_sem_permissao(
    medicao_sem_lancamento, user_codae_produto
):
    kwargs = {
        "user": user_codae_produto,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    with pytest.raises(
        PermissionDenied, match="Você não tem permissão para executar essa ação."
    ):
        medicao_sem_lancamento.medicao_sem_lancamentos(**kwargs)


def test_medicao_sem_lancamentos_erro_validacao(
    solicitacao_sem_lancamento, user_diretor_escola
):
    usuario, _ = user_diretor_escola
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    with pytest.raises(
        ValidationError,
        match=r"`SolicitacaoMedicaoInicial` não possui fluxo `medicao_sem_lancamentos`",
    ):
        solicitacao_sem_lancamento.medicao_sem_lancamentos(**kwargs)


def test_codae_pede_correcao_sem_lancamentos_solicitacao(
    solicitacao_para_corecao, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houve alimentação ofertadada nesse período"
    kwargs = {
        "user": usuario,
        "justificativa": justificativa,
    }
    solicitacao_para_corecao.codae_pede_correcao_sem_lancamentos(**kwargs)
    assert (
        solicitacao_para_corecao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )

    medicao = solicitacao_para_corecao.medicoes.first()
    assert medicao.status == SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS

    assert solicitacao_para_corecao.logs.count() == 1
    log = solicitacao_para_corecao.logs.first()
    assert (
        log.status_evento
        == LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    assert log.usuario == usuario
    assert log.justificativa == justificativa


def test_codae_pede_correcao_sem_lancamentos_solicitacao_usuario_sem_permissao(
    solicitacao_para_corecao, user_diretor_escola
):
    usuario, _ = user_diretor_escola
    justificativa = "Houve alimentação ofertadada nesse período"
    kwargs = {
        "user": usuario,
        "justificativa": justificativa,
    }
    with pytest.raises(
        PermissionDenied, match="Você não tem permissão para executar essa ação."
    ):
        solicitacao_para_corecao.codae_pede_correcao_sem_lancamentos(**kwargs)


def test_codae_pede_correcao_sem_lancamentos_medicao(
    solicitacao_para_corecao, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houve alimentação ofertadada nesse período"
    kwargs = {
        "user": usuario,
        "justificativa": justificativa,
    }
    medicao = solicitacao_para_corecao.medicoes.first()
    medicao.codae_pede_correcao_sem_lancamentos(**kwargs)
    assert (
        medicao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )

    solicitacao = medicao.solicitacao_medicao_inicial
    assert (
        solicitacao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )

    assert medicao.logs.count() == 1
    log = medicao.logs.first()
    assert (
        log.status_evento
        == LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    assert log.usuario == usuario
    assert log.justificativa == justificativa


def test_codae_pede_correcao_sem_lancamentos_medicao_usuario_sem_permissao(
    solicitacao_para_corecao, user_diretor_escola
):
    usuario, _ = user_diretor_escola
    justificativa = "Houve alimentação ofertadada nesse período"
    kwargs = {
        "user": usuario,
        "justificativa": justificativa,
    }

    medicao = solicitacao_para_corecao.medicoes.first()
    with pytest.raises(
        PermissionDenied, match="Você não tem permissão para executar essa ação."
    ):
        medicao.codae_pede_correcao_sem_lancamentos(**kwargs)


def test_finaliza_solicitacao_alteracao_hook(
    solicitacao_alteracao_cronograma,
    user_codae_produto,
):
    solicitacao = solicitacao_alteracao_cronograma
    cronograma = solicitacao.cronograma

    kwargs = {
        "user": user_codae_produto,
        "justificativa": str(solicitacao.uuid),
    }

    cronograma.finaliza_solicitacao_alteracao(**kwargs)
    cronograma.refresh_from_db()

    assert cronograma.status == Cronograma.workflow_class.ASSINADO_CODAE

    assert cronograma.qtd_total_programada == solicitacao.qtd_total_programada

    assert list(cronograma.etapas.values_list("id", flat=True)) == list(
        solicitacao.etapas_novas.values_list("id", flat=True)
    )

    assert list(
        cronograma.programacoes_de_recebimento.values_list("id", flat=True)
    ) == list(solicitacao.programacoes_novas.values_list("id", flat=True))

    log = cronograma.logs.order_by("-criado_em").first()
    assert log.status_evento == LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELA_CODAE
    assert log.usuario == user_codae_produto


def test_codae_pede_correcao_ocorrencia_hook(
    ocorrencia_medicao_inicial_status_aprovado_dre, usuario_nutrimanifestacao
):
    kwargs = {
        "user": usuario_nutrimanifestacao,
        "justificativa": str(ocorrencia_medicao_inicial_status_aprovado_dre.uuid),
    }
    ocorrencia_medicao_inicial_status_aprovado_dre.codae_pede_correcao_ocorrencia(
        **kwargs
    )
    ocorrencia_medicao_inicial_status_aprovado_dre.refresh_from_db()
    log = ocorrencia_medicao_inicial_status_aprovado_dre.logs.order_by(
        "-criado_em"
    ).first()
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA_CODAE
    assert log.usuario == usuario_nutrimanifestacao
    assert log.justificativa == str(ocorrencia_medicao_inicial_status_aprovado_dre.uuid)


def test_codae_aprova_ocorrencia_hook(
    ocorrencia_medicao_inicial_status_aprovado_dre, usuario_nutrimanifestacao
):
    ocorrencia_medicao_inicial_status_aprovado_dre.codae_aprova_ocorrencia(
        user=usuario_nutrimanifestacao
    )
    ocorrencia_medicao_inicial_status_aprovado_dre.refresh_from_db()
    log = ocorrencia_medicao_inicial_status_aprovado_dre.logs.order_by(
        "-criado_em"
    ).first()
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE
    assert log.usuario == usuario_nutrimanifestacao


@patch(
    "sme_sigpae_api.dados_comuns.fluxo_status.FluxoDietaEspecialPartindoDaEscola._preenche_template_e_envia_email"
)
def test_nao_envia_email_de_cancelamento(
    mock_envia_email, solicitacao_dieta_especial, user_diretor_escola
):
    solicitacao_dieta_especial.cancelar_pedido(
        user=user_diretor_escola[0],
        justificativa="Teste",
        alta_medica=False,
        pendente_autorizacao=True,
    )

    mock_envia_email.assert_not_called()


@patch(
    "sme_sigpae_api.dados_comuns.fluxo_status.FluxoDietaEspecialPartindoDaEscola._preenche_template_e_envia_email"
)
def test_nao_envia_email_de_cancelamento_com_tipo_solicitacao_cancelamento(
    mock_envia_email, solicitacao_dieta_especial, user_diretor_escola
):
    solicitacao_dieta_especial.tipo_solicitacao = "CANCELAMENTO_DIETA"
    solicitacao_dieta_especial.save()

    solicitacao_dieta_especial.cancelar_pedido(
        user=user_diretor_escola[0],
        justificativa="Teste",
        alta_medica=False,
        pendente_autorizacao=False,
    )

    mock_envia_email.assert_not_called()


@patch(
    "sme_sigpae_api.dados_comuns.fluxo_status.FluxoDietaEspecialPartindoDaEscola._preenche_template_e_envia_email"
)
def test_envia_email_de_cancelamento(
    mock_envia_email, solicitacao_dieta_especial, user_diretor_escola
):
    solicitacao_dieta_especial.cancelar_pedido(
        user=user_diretor_escola[0],
        justificativa="Teste",
        alta_medica=False,
        pendente_autorizacao=False,
    )
    assunto = (
        "[SIGPAE] Status de solicitação - #" + solicitacao_dieta_especial.id_externo
    )
    titulo = f'Status de solicitação - "{solicitacao_dieta_especial.aluno.codigo_eol} - {solicitacao_dieta_especial.aluno.nome}"'
    mock_envia_email.assert_called_once_with(
        assunto,
        titulo,
        user_diretor_escola[0],
        solicitacao_dieta_especial._partes_interessadas_codae_cancela,
        None,
    )


@patch(
    "sme_sigpae_api.dados_comuns.fluxo_status.FluxoDietaEspecialPartindoDaEscola._preenche_template_e_envia_email"
)
def test_envia_email_de_cancelamento_por_alta_medica(
    mock_envia_email, solicitacao_dieta_especial, user_diretor_escola
):

    solicitacao_dieta_especial.cancelar_pedido(
        user=user_diretor_escola[0],
        justificativa="Teste",
        alta_medica=True,
        pendente_autorizacao=False,
    )
    assunto = (
        "[SIGPAE] Status de solicitação - #" + solicitacao_dieta_especial.id_externo
    )
    titulo = solicitacao_dieta_especial.str_dre_lote_escola
    mock_envia_email.assert_called_once_with(
        assunto,
        titulo,
        user_diretor_escola[0],
        solicitacao_dieta_especial._partes_interessadas_codae_cancela,
        "cancelar_pedido",
    )


@patch("sme_sigpae_api.dados_comuns.fluxo_status.convert_base64_to_contentfile")
def test_deve_acumular_logs_ao_corrigir_multiplas_vezes(
    mock_convert_base64,
    ocorrencia_medicao_inicial_status_aprovado_dre,
    user_diretor_escola,
):
    usuario, _ = user_diretor_escola
    ocorrencia = ocorrencia_medicao_inicial_status_aprovado_dre

    mock_convert_base64.return_value = ContentFile(
        b"arquivo fake", name="doc1.pdf"
    )

    kwargs_1 = {
        "user": usuario,
        "justificativa": "Primeira correção",
        "anexos": [
            {"nome": "doc1.pdf", "base64": "qualquer-coisa"}
        ],
    }

    kwargs_2 = {
        "user": usuario,
        "justificativa": "Segunda correção",
        "anexos": [
            {"nome": "doc2.pdf", "base64": "qualquer-coisa"}
        ],
    }

    ocorrencia._ue_corrige_hook(**deepcopy(kwargs_1))
    ocorrencia._ue_corrige_hook(**deepcopy(kwargs_2))

    status = LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE
    logs = ocorrencia.logs.filter(status_evento=status).order_by("criado_em")

    assert logs.count() == 2

    justificativas = list(logs.values_list("justificativa", flat=True))
    assert "Primeira correção" in justificativas
    assert "Segunda correção" in justificativas


@patch("sme_sigpae_api.dados_comuns.fluxo_status.convert_base64_to_contentfile")
def test_deve_manter_anexos_de_todos_os_logs(
    mock_convert_base64,
    ocorrencia_medicao_inicial_status_aprovado_dre,
    user_diretor_escola,
):
    usuario, _ = user_diretor_escola
    ocorrencia = ocorrencia_medicao_inicial_status_aprovado_dre

    mock_convert_base64.return_value = ContentFile(
        b"arquivo fake", name="anexo.pdf"
    )

    kwargs_1 = {
        "user": usuario,
        "justificativa": "Correção 1",
        "anexos": [
            {"nome": "anexo1.pdf", "base64": "qualquer-coisa"}
        ],
    }

    kwargs_2 = {
        "user": usuario,
        "justificativa": "Correção 2",
        "anexos": [
            {"nome": "anexo2.pdf", "base64": "qualquer-coisa"}
        ],
    }

    ocorrencia._ue_corrige_hook(**deepcopy(kwargs_1))
    ocorrencia._ue_corrige_hook(**deepcopy(kwargs_2))

    status = LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE
    logs = ocorrencia.logs.filter(status_evento=status)

    assert logs.count() == 2
    assert AnexoLogSolicitacoesUsuario.objects.filter(log__in=logs).count() == 2
    assert all(log.anexos.count() == 1 for log in logs)

