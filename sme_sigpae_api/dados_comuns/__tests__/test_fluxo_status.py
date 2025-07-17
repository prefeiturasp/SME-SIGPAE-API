import pytest
import xworkflows
from rest_framework.exceptions import PermissionDenied, ValidationError

from sme_sigpae_api.dados_comuns.fluxo_status import (
    ReclamacaoProdutoWorkflow,
    SolicitacaoMedicaoInicialWorkflow,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario

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
