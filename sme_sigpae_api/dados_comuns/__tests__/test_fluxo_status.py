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


def test_ue_envia_sem_lancamentos(medicao_sem_lancamentos, user_diretor_escola):
    usuario, _ = user_diretor_escola
    justificativa = "Não houve aulas no período devido a reformas na escola."
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": justificativa,
    }

    medicao_sem_lancamentos.ue_envia_sem_lancamentos(**kwargs)
    assert (
        medicao_sem_lancamentos.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )

    medicao = medicao_sem_lancamentos.medicoes.first()
    assert (
        medicao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )

    assert medicao_sem_lancamentos.logs.count() == 1
    log = medicao_sem_lancamentos.logs.first()
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE
    assert log.usuario == usuario
    assert log.justificativa == justificativa


def test_ue_envia_sem_lancamentos_usuario_sem_permissao(
    medicao_sem_lancamentos, user_codae_produto
):
    kwargs = {
        "user": user_codae_produto,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    with pytest.raises(
        PermissionDenied, match="Você não tem permissão para executar essa ação."
    ):
        medicao_sem_lancamentos.ue_envia_sem_lancamentos(**kwargs)


def test_ue_envia_sem_lancamentos_erro_medicao(
    medicao_sem_lancamentos, user_diretor_escola
):
    usuario, _ = user_diretor_escola
    kwargs = {
        "user": usuario,
        "justificativa_sem_lancamentos": "Não houve aulas no período devido a reformas na escola.",
    }
    medicao = medicao_sem_lancamentos.medicoes.first()
    with pytest.raises(
        ValidationError, match=r"`Medicao` não possui fluxo `ue_envia_sem_lancamentos`"
    ):
        medicao.ue_envia_sem_lancamentos(**kwargs)
