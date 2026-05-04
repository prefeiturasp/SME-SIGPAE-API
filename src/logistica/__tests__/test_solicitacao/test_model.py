import pytest
from django.contrib.auth import get_user_model

from src.dados_comuns.fluxo_status import (
    GuiaRemessaWorkFlow,
    SolicitacaoRemessaWorkFlow,
)

from ...models.solicitacao import (
    LogSolicitacaoDeCancelamentoPeloPapa,
    SolicitacaoDeAlteracaoRequisicao,
    SolicitacaoRemessa,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_instance_model(solicitacao):
    model = solicitacao
    assert isinstance(model, SolicitacaoRemessa)
    assert model.cnpj
    assert model.numero_solicitacao
    assert model.status
    assert model.sequencia_envio
    assert model.quantidade_total_guias


def test_srt_model(solicitacao):
    assert solicitacao.__str__() == "Solicitação: 559890 - Status: Aguardando envio"


def test_meta_model(solicitacao):
    assert solicitacao._meta.verbose_name == "Solicitação Remessa"
    assert solicitacao._meta.verbose_name_plural == "Solicitações Remessas"


def test_solicitacao_de_alteracao_requisicao_model(solicitacao_de_alteracao_requisicao):
    model = solicitacao_de_alteracao_requisicao
    assert isinstance(model, SolicitacaoDeAlteracaoRequisicao)
    assert model.requisicao
    assert model.motivo
    assert model.justificativa
    assert model.justificativa_aceite
    assert model.justificativa_negacao
    assert model.usuario_solicitante
    assert model.numero_solicitacao


def test_srt_solicitacao_de_alteracao_requisicao_model(
    solicitacao_de_alteracao_requisicao,
):
    assert (
        solicitacao_de_alteracao_requisicao.__str__()
        == "Solicitação de alteração: 00000001-ALT"
    )


def test_meta_solicitacao_de_alteracao_requisicao_model(
    solicitacao_de_alteracao_requisicao,
):
    assert (
        solicitacao_de_alteracao_requisicao._meta.verbose_name
        == "Solicitação de Alteração de Requisição"
    )
    assert (
        solicitacao_de_alteracao_requisicao._meta.verbose_name_plural
        == "Solicitações de Alteração de Requisição"
    )


def test_solicitacao_de_alteracao_requisicao_numero_solicitacao(
    solicitacao_de_alteracao_requisicao,
):
    assert solicitacao_de_alteracao_requisicao.numero_solicitacao == "00000001-ALT"


def test_log_solicitcacao_cancelamento_instance_model(solicitacao_cancelamento_log):
    model = solicitacao_cancelamento_log
    assert isinstance(model, LogSolicitacaoDeCancelamentoPeloPapa)
    assert model.requisicao
    assert model.guias
    assert model.sequencia_envio


def test_srt_log_solicitcacao_cancelamento_model(solicitacao_cancelamento_log):
    assert solicitacao_cancelamento_log.__str__() == "Sol. de cancelamento 123456"


def test_meta_log_solicitcacao_cancelamento_model(solicitacao_cancelamento_log):
    assert (
        solicitacao_cancelamento_log._meta.verbose_name
        == "Log de Solicitação de Cancelamento do PAPA"
    )
    assert (
        solicitacao_cancelamento_log._meta.verbose_name_plural
        == "Logs de Solicitações de Cancelamento do PAPA"
    )


def test_property_solicitacao_cancelada(solicitacao):
    solicitacao.status = SolicitacaoRemessaWorkFlow.PAPA_CANCELA
    solicitacao.save()

    assert solicitacao.cancelada


def test_property_solicitacao_todas_as_guias_canceladas(guia):
    solicitacao = guia.solicitacao

    guia.status = GuiaRemessaWorkFlow.CANCELADA
    guia.save()

    assert solicitacao.todas_as_guias_canceladas
