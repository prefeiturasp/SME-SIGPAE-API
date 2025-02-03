import pytest
import xworkflows

from sme_sigpae_api.dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow

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
