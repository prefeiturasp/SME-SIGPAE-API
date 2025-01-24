import uuid
from unittest.mock import Mock

import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow
from sme_sigpae_api.produto.api.serializers.serializers import (
    ReclamacaoDeProdutoSerializer,
)
from sme_sigpae_api.produto.api.viewsets import ReclamacaoProdutoViewSet
from sme_sigpae_api.produto.models import AnaliseSensorial

pytestmark = pytest.mark.django_db


def test_view_muda_status_com_justificativa_e_anexo_retorna_200(
    reclamacao_respondido_terceirizada, mock_view_de_reclamacao_produto
):
    mock_request, viewset = mock_view_de_reclamacao_produto
    assert (
        reclamacao_respondido_terceirizada.status
        == ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
    )
    resposta = viewset.muda_status_com_justificativa_e_anexo(
        mock_request, reclamacao_respondido_terceirizada.codae_recusa
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert (
        resposta.data
        == ReclamacaoDeProdutoSerializer(reclamacao_respondido_terceirizada).data
    )
    assert resposta.data["status"] == ReclamacaoProdutoWorkflow.CODAE_RECUSOU
    assert resposta.data["status_titulo"] == "CODAE recusou"
    assert len(resposta.data["anexos"]) == 0


def test_view_muda_status_com_justificativa_e_anex_retorna_exception(
    reclamacao_respondido_terceirizada, mock_view_de_reclamacao_produto
):
    mock_request, viewset = mock_view_de_reclamacao_produto
    reclamacao_respondido_terceirizada.status = ReclamacaoProdutoWorkflow.CODAE_ACEITOU
    resposta = viewset.muda_status_com_justificativa_e_anexo(
        mock_request, reclamacao_respondido_terceirizada.codae_recusa
    )
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        resposta.data["detail"]
        == "Erro de transição de estado: Transition 'codae_recusa' isn't available from state 'CODAE_ACEITOU'."
    )


def test_view_quantidade_reclamacoes_ativas_retorna_uma(
    reclamacao_respondido_terceirizada,
):
    viewset = ReclamacaoProdutoViewSet()
    reclamacoes_ativas = viewset.quantidade_reclamacoes_ativas(
        reclamacao_respondido_terceirizada
    )
    assert reclamacoes_ativas == 1


def test_view_quantidade_reclamacoes_ativas_retorna_nenhuma(
    reclamacao_respondido_terceirizada,
):
    reclamacao = (
        reclamacao_respondido_terceirizada.homologacao_produto.reclamacoes.first()
    )
    reclamacao.status = ReclamacaoProdutoWorkflow.CODAE_ACEITOU
    reclamacao.save()

    viewset = ReclamacaoProdutoViewSet()
    reclamacoes_ativas = viewset.quantidade_reclamacoes_ativas(
        reclamacao_respondido_terceirizada
    )
    assert reclamacoes_ativas == 0


def test_view_update_analise_sensorial_status(reclamacao_respondido_terceirizada):
    analises_sensoriais = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
    ).all()
    assert analises_sensoriais.count() == 1

    viewset = ReclamacaoProdutoViewSet()
    viewset.update_analise_sensorial_status(
        analises_sensoriais, AnaliseSensorial.STATUS_RESPONDIDA
    )
    analises_aguardando_resposta = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
    ).count()
    assert analises_aguardando_resposta == 0

    analises_respondidas = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_RESPONDIDA
    ).count()
    assert analises_respondidas == 1
