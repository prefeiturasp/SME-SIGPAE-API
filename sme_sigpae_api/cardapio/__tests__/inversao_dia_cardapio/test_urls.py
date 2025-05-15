import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.cardapio.__tests__.utils import (
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow

pytestmark = pytest.mark.django_db

ENDPOINT_INVERSOES = "inversoes-dia-cardapio"


def test_permissoes_inversao_cardapio_viewset(
    client_autenticado_vinculo_escola_cardapio,
    inversao_dia_cardapio,
    inversao_dia_cardapio_outra_dre,
):
    # pode ver os dados de uma alteração de cardápio da mesma escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma inversão de dia de cardápio de outra escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # não pode ver os dados de TODAS as inversões de dia de cardápio
    response = client_autenticado_vinculo_escola_cardapio.get(f"/{ENDPOINT_INVERSOES}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }
    # pode deletar somente se for escola e se estiver como rascunho
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    inversao_dia_cardapio.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    inversao_dia_cardapio.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_inversao_minhas_solicitacoes(
    client_autenticado_vinculo_escola_cardapio,
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_INVERSOES}/{constants.SOLICITACOES_DO_USUARIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_url_endpoint_solicitacoes_inversao_inicio_fluxo(
    client_autenticado_vinculo_escola_cardapio, inversao_dia_cardapio
):
    assert str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    assert str(json["uuid"]) == str(inversao_dia_cardapio.uuid)


def test_url_endpoint_solicitacoes_inversao_relatorio(
    client_autenticado, inversao_dia_cardapio
):
    response = client_autenticado.get(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio.uuid}/{constants.RELATORIO}/"
    )
    id_externo = inversao_dia_cardapio.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="solicitacao_inversao_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_solicitacoes_inversao_inicio_fluxo_error(
    client_autenticado_vinculo_escola_cardapio, inversao_dia_cardapio_dre_validar
):
    assert (
        str(inversao_dia_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'inicia_fluxo' isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_solicitacoes_inversao_dre_valida(
    client_autenticado_vinculo_dre_cardapio, inversao_dia_cardapio_dre_validar
):
    assert (
        str(inversao_dia_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    assert str(json["uuid"]) == str(inversao_dia_cardapio_dre_validar.uuid)


def test_url_endpoint_solicitacoes_inversao_dre_valida_error(
    client_autenticado_vinculo_dre_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_valida' isn't available from state 'DRE_VALIDADO'."
    }


def test_url_endpoint_solicitacoes_inversao_dre_nao_valida(
    client_autenticado_vinculo_dre_cardapio, inversao_dia_cardapio_dre_validar
):
    assert (
        str(inversao_dia_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA
    assert str(json["uuid"]) == str(inversao_dia_cardapio_dre_validar.uuid)
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_nao_valida' isn't available from state "
        "'DRE_NAO_VALIDOU_PEDIDO_ESCOLA'."
    }


def test_url_endpoint_solicitacoes_inversao_codae_autoriza_403(
    client_autenticado_vinculo_codae_dieta_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_dieta_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_endpoint_solicitacoes_inversao_codae_autoriza(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    assert str(json["uuid"]) == str(inversao_dia_cardapio_dre_validado.uuid)


def test_url_endpoint_solicitacoes_inversao_codae_autoriza_error(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_dre_validar
):
    assert (
        str(inversao_dia_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_autoriza_questionamento' "
        "isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_solicitacoes_inversao_codae_nega(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO
    assert str(json["uuid"]) == str(inversao_dia_cardapio_dre_validado.uuid)


def test_url_endpoint_solicitacoes_inversao_codae_nega_error(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_dre_validar
):
    assert (
        str(inversao_dia_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validar.uuid}/{constants.CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_nega_questionamento'"
        " isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_solicitacoes_inversao_codae_questiona(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    assert str(json["uuid"]) == str(inversao_dia_cardapio_dre_validado.uuid)


def test_url_endpoint_solicitacoes_inversao_codae_questiona_error(
    client_autenticado_vinculo_codae_cardapio, inversao_dia_cardapio_codae_autorizado
):
    assert (
        str(inversao_dia_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_codae_autorizado.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = "Erro de transição de estado: Transition 'codae_questiona' isn't available from state 'CODAE_AUTORIZADO'."
    assert response.json() == {"detail": detail}


def test_url_endpoint_solicitacoes_inversao_terceirizada_responde_questionamento(
    client_autenticado_vinculo_terceirizada_cardapio,
    inversao_dia_cardapio_codae_questionado,
):
    justificativa = "TESTE JUSTIFICATIVA"
    resposta = True
    assert (
        str(inversao_dia_cardapio_codae_questionado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/"
        f"{inversao_dia_cardapio_codae_questionado.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta},
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert (
        json["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    assert json["logs"][0]["justificativa"] == justificativa
    assert json["logs"][0]["resposta_sim_nao"] == resposta
    assert str(json["uuid"]) == str(inversao_dia_cardapio_codae_questionado.uuid)
    assert (
        str(inversao_dia_cardapio_codae_questionado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/"
        f"{inversao_dia_cardapio_codae_questionado.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = "Erro de transição de estado: Transition 'terceirizada_responde_questionamento' isn't available from state 'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
    assert response.json() == {"detail": detail}


def test_url_endpoint_solicitacoes_inversao_terceirizada_ciencia(
    client_autenticado_vinculo_terceirizada_cardapio,
    inversao_dia_cardapio_codae_autorizado,
):
    assert (
        str(inversao_dia_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_codae_autorizado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    assert str(json["uuid"]) == str(inversao_dia_cardapio_codae_autorizado.uuid)


def test_url_endpoint_solicitacoes_inversao_terceirizada_ciencia_error(
    client_autenticado_vinculo_terceirizada_cardapio, inversao_dia_cardapio_dre_validado
):
    assert (
        str(inversao_dia_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_dre_validado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia' "
        "isn't available from state 'DRE_VALIDADO'."
    }


@freeze_time("2019-10-11")
def test_url_endpoint_solicitacoes_inversao_escola_cancela(
    client_autenticado_vinculo_escola_cardapio, inversao_dia_cardapio_codae_autorizado
):
    assert (
        str(inversao_dia_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_codae_autorizado.uuid}/{constants.ESCOLA_CANCELA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU
    assert str(json["uuid"]) == str(inversao_dia_cardapio_codae_autorizado.uuid)


@freeze_time("2019-12-31")
def test_url_endpoint_solicitacoes_inversao_escola_cancela_error(
    client_autenticado_vinculo_escola_cardapio, inversao_dia_cardapio_codae_autorizado
):
    assert (
        str(inversao_dia_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_INVERSOES}/{inversao_dia_cardapio_codae_autorizado.uuid}/{constants.ESCOLA_CANCELA}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Só pode cancelar com no mínimo 2 dia(s) úteis de antecedência"
    }


def test_terceirizada_marca_conferencia_inversao_cardapio_viewset(
    client_autenticado, inversao_dia_cardapio
):
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, InversaoCardapio, "inversoes-dia-cardapio"
    )
