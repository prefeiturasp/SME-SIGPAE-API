import pytest
from django.core.exceptions import ValidationError

from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.medicao_inicial.api.viewsets import SolicitacaoMedicaoInicialViewSet

pytestmark = pytest.mark.django_db


def test_valida_sem_lancamentos_retorna_none(solicitacao_sem_lancamento):
    validado = SolicitacaoMedicaoInicialViewSet._valida_sem_lancamentos(
        None, solicitacao_sem_lancamento
    )
    assert validado is None


def test_valida_sem_lancamentos_retorna_exception(solicitacao_escola_emebs):

    with pytest.raises(
        ValidationError,
        match="Solicitação Medição Inicial não pode voltar para ser preenchida novamente, pois possui lançamentos.",
    ):
        SolicitacaoMedicaoInicialViewSet._valida_sem_lancamentos(
            None, solicitacao_escola_emebs
        )


def test_solicita_correcao_em_solicitacao(
    solicitacao_sem_lancamento, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houva alimentação autorizada no período"
    SolicitacaoMedicaoInicialViewSet._solicita_correcao_em_solicitacao(
        None, solicitacao_sem_lancamento, usuario, justificativa
    )
    assert (
        solicitacao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    medicao = solicitacao_sem_lancamento.medicoes.first()
    assert medicao.status == SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS


def test_solicita_correcao_em_medicoes(
    solicitacao_sem_lancamento, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houva alimentação autorizada no período"
    SolicitacaoMedicaoInicialViewSet._solicita_correcao_em_medicoes(
        None, solicitacao_sem_lancamento, usuario, justificativa
    )
    medicao = solicitacao_sem_lancamento.medicoes.first()
    assert (
        medicao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    assert (
        solicitacao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )
