import datetime
import json

import pytest
from freezegun import freeze_time
from rest_framework import status
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.__tests__.conftest import converter_data
from sme_sigpae_api.cardapio.models import (
    AlteracaoCardapio,
    GrupoSuspensaoAlimentacao,
    InversaoCardapio,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import (
    InformativoPartindoDaEscolaWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)

ENDPOINT_INVERSOES = "inversoes-dia-cardapio"
ENDPOINT_SUSPENSOES = "grupos-suspensoes-alimentacao"
ENDPOINT_SUSPENSOES_DE_CEI = "suspensao-alimentacao-de-cei"
ENDPOINT_ALTERACAO_CARD = "alteracoes-cardapio"
ENDPOINT_ALTERACAO_CARD_CEI = "alteracoes-cardapio-cei"
ENDPOINT_VINCULOS_ALIMENTACAO = "vinculos-tipo-alimentacao-u-e-periodo-escolar"
ENDPOINT_HORARIO_DO_COMBO = "horario-do-combo-tipo-de-alimentacao-por-unidade-escolar"

ESCOLA_INFORMA_SUSPENSAO = "informa-suspensao"


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


#
# Suspensão de alimentação
#


def test_permissoes_suspensao_alimentacao_cei_viewset(
    client_autenticado_vinculo_escola_cardapio, suspensao_alimentacao_de_cei
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK

    suspensao_alimentacao_de_cei.status = InformativoPartindoDaEscolaWorkflow.INFORMADO
    suspensao_alimentacao_de_cei.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }

    suspensao_alimentacao_de_cei.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    suspensao_alimentacao_de_cei.save()

    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/{ESCOLA_INFORMA_SUSPENSAO}/"
    )
    assert response.status_code == status.HTTP_200_OK

    suspensao_alimentacao_de_cei.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    suspensao_alimentacao_de_cei.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_permissoes_suspensao_alimentacao_viewset(
    client_autenticado_vinculo_escola_cardapio,
    grupo_suspensao_alimentacao,
    grupo_suspensao_alimentacao_outra_dre,
):
    # pode ver os dados de uma suspensão de alimentação da mesma escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma suspensão de alimentação de outra escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # não pode ver os dados de TODAS as suspensões de alimentação
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }
    grupo_suspensao_alimentacao.status = InformativoPartindoDaEscolaWorkflow.INFORMADO
    grupo_suspensao_alimentacao.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }
    # pode deletar somente se for escola e se estiver como rascunho
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    grupo_suspensao_alimentacao.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    grupo_suspensao_alimentacao.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_suspensao_minhas_solicitacoes(
    client_autenticado_vinculo_escola_cardapio,
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES}/meus_rascunhos/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_url_endpoint_suspensoes_informa(
    client_autenticado_vinculo_escola_cardapio, grupo_suspensao_alimentacao
):
    assert (
        str(grupo_suspensao_alimentacao.status)
        == InformativoPartindoDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao.uuid}/{constants.ESCOLA_INFORMA_SUSPENSAO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == InformativoPartindoDaEscolaWorkflow.INFORMADO
    assert str(json["uuid"]) == str(grupo_suspensao_alimentacao.uuid)


def test_url_endpoint_suspensoes_informa_error(
    client_autenticado_vinculo_escola_cardapio, grupo_suspensao_alimentacao_informado
):
    assert (
        str(grupo_suspensao_alimentacao_informado.status)
        == InformativoPartindoDaEscolaWorkflow.INFORMADO
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/{constants.ESCOLA_INFORMA_SUSPENSAO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'informa' "
        "isn't available from state 'INFORMADO'."
    }


@freeze_time("2022-01-15")
def test_url_endpoint_suspensoes_escola_cancela(
    client_autenticado_vinculo_escola_cardapio, grupo_suspensao_alimentacao_informado
):
    assert (
        str(grupo_suspensao_alimentacao_informado.status)
        == InformativoPartindoDaEscolaWorkflow.INFORMADO
    )

    datas_para_cancelamento = [
        i.data.strftime("%Y-%m-%d")
        for i in grupo_suspensao_alimentacao_informado.suspensoes_alimentacao.all()
    ]

    data = {
        "datas": datas_para_cancelamento,
        "justificativa": "Não quero mais a suspensão",
    }

    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/escola-cancela/",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert resposta["status"] == InformativoPartindoDaEscolaWorkflow.ESCOLA_CANCELOU
    assert str(resposta["uuid"]) == str(grupo_suspensao_alimentacao_informado.uuid)
    assert resposta["logs"][0]["justificativa"] == data["justificativa"]
    assert isinstance(resposta["suspensoes_alimentacao"], list)
    assert len(resposta["suspensoes_alimentacao"]) == 3


@freeze_time("2022-01-15")
def test_url_endpoint_suspensoes_escola_cancela_parcial(
    client_autenticado_vinculo_escola_cardapio, grupo_suspensao_alimentacao_informado
):
    assert (
        str(grupo_suspensao_alimentacao_informado.status)
        == InformativoPartindoDaEscolaWorkflow.INFORMADO
    )

    datas_para_cancelamento = [
        i.data.strftime("%Y-%m-%d")
        for i in grupo_suspensao_alimentacao_informado.suspensoes_alimentacao.all()
    ]
    # Cancelando a primeira data
    data_selecionada = datas_para_cancelamento[0]
    data = {"datas": [data_selecionada], "justificativa": "Não quero mais a suspensão"}
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/escola-cancela/",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert resposta["status"] == InformativoPartindoDaEscolaWorkflow.INFORMADO
    assert str(resposta["uuid"]) == str(grupo_suspensao_alimentacao_informado.uuid)
    assert isinstance(resposta["suspensoes_alimentacao"], list)
    assert len(resposta["suspensoes_alimentacao"]) == 3

    for suspensao in resposta["suspensoes_alimentacao"]:
        if suspensao["data"] == converter_data(data_selecionada):
            assert suspensao["cancelado"] is True
            encontrou_data = True
        else:
            assert suspensao["cancelado"] is False
    assert encontrou_data, f"Nenhuma entrada encontrada para a data {data_selecionada}"

    # Cancelando a segunda data
    data_ja_cancelada = datas_para_cancelamento[0]
    data_selecionada = datas_para_cancelamento[1]
    data = {"datas": [data_selecionada], "justificativa": "Não quero mais a suspensão"}
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/escola-cancela/",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert resposta["status"] == InformativoPartindoDaEscolaWorkflow.INFORMADO
    assert str(resposta["uuid"]) == str(grupo_suspensao_alimentacao_informado.uuid)
    assert isinstance(resposta["suspensoes_alimentacao"], list)
    assert len(resposta["suspensoes_alimentacao"]) == 3

    for suspensao in resposta["suspensoes_alimentacao"]:
        if suspensao["data"] in [
            converter_data(data_selecionada),
            converter_data(data_ja_cancelada),
        ]:
            assert suspensao["cancelado"] is True
            encontrou_data = True
        else:
            assert suspensao["cancelado"] is False
    assert encontrou_data, f"Nenhuma entrada encontrada para a data {data_selecionada}"

    # Cancelando a terceira data
    data_selecionada = datas_para_cancelamento[2]
    data = {"datas": [data_selecionada], "justificativa": "Não quero mais a suspensão"}
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/escola-cancela/",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert resposta["status"] == InformativoPartindoDaEscolaWorkflow.ESCOLA_CANCELOU
    assert str(resposta["uuid"]) == str(grupo_suspensao_alimentacao_informado.uuid)
    assert resposta["logs"][0]["justificativa"] == data["justificativa"]
    assert isinstance(resposta["suspensoes_alimentacao"], list)
    assert len(resposta["suspensoes_alimentacao"]) == 3

    for suspensao in resposta["suspensoes_alimentacao"]:
        assert suspensao["cancelado"] is True


@freeze_time("2022-01-15")
def test_url_endpoint_suspensoes_escola_cancela_erro_suspensao_ja_cancelada(
    client_autenticado_vinculo_escola_cardapio,
    grupo_suspensao_alimentacao_escola_cancelou,
):
    assert (
        str(grupo_suspensao_alimentacao_escola_cancelou.status)
        == InformativoPartindoDaEscolaWorkflow.ESCOLA_CANCELOU
    )
    datas_para_cancelamento = [
        i.data.strftime("%Y-%m-%d")
        for i in grupo_suspensao_alimentacao_escola_cancelou.suspensoes_alimentacao.all()
    ]
    data = {
        "datas": datas_para_cancelamento,
        "justificativa": "Não quero mais a suspensão",
    }

    with pytest.raises(AssertionError, match="Solicitação já está cancelada"):
        response = client_autenticado_vinculo_escola_cardapio.patch(
            f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_escola_cancelou.uuid}/escola-cancela/",
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@freeze_time("2022-01-28")
def test_url_endpoint_suspensoes_escola_cancela_erro_dias_antecedencia(
    client_autenticado_vinculo_escola_cardapio, grupo_suspensao_alimentacao_informado
):
    assert (
        str(grupo_suspensao_alimentacao_informado.status)
        == InformativoPartindoDaEscolaWorkflow.INFORMADO
    )
    datas_para_cancelamento = [
        i.data.strftime("%Y-%m-%d")
        for i in grupo_suspensao_alimentacao_informado.suspensoes_alimentacao.all()
    ]
    data = {
        "datas": [datas_para_cancelamento[0]],
        "justificativa": "Não quero mais a suspensão",
    }

    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/escola-cancela/",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_ = response.json()
    assert json_["detail"] == (
        "Erro de transição de estado: Só pode cancelar com no mínimo 2 dia(s) "
        "úteis de antecedência"
    )


def test_url_endpoint_suspensoes_relatorio(
    client_autenticado, grupo_suspensao_alimentacao_informado
):
    response = client_autenticado.get(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/{constants.RELATORIO}/"
    )
    id_externo = grupo_suspensao_alimentacao_informado.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="solicitacao_suspensao_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_suspensoes_terc_ciencia(
    client_autenticado_vinculo_terceirizada_cardapio,
    grupo_suspensao_alimentacao_informado,
):
    assert (
        str(grupo_suspensao_alimentacao_informado.status)
        == InformativoPartindoDaEscolaWorkflow.INFORMADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao_informado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert (
        json["status"] == InformativoPartindoDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    )
    assert str(json["uuid"]) == str(grupo_suspensao_alimentacao_informado.uuid)


def test_url_endpoint_suspensoes_terc_ciencia_error(
    client_autenticado_vinculo_terceirizada_cardapio, grupo_suspensao_alimentacao
):
    assert (
        str(grupo_suspensao_alimentacao.status)
        == InformativoPartindoDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES}/{grupo_suspensao_alimentacao.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia'"
        " isn't available from state 'RASCUNHO'."
    }


#
# Alteração de cardápio
#


def test_permissoes_alteracao_cardapio_viewset(
    client_autenticado_vinculo_escola_cardapio,
    alteracao_cardapio,
    alteracao_cardapio_outra_dre,
):
    # pode ver os dados de uma alteração de cardápio da mesma escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma alteração de cardápio de outra escola
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_outra_dre.uuid}/"
    )
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    alteracao_cardapio.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }
    # pode deletar somente se for escola e se estiver como rascunho
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    alteracao_cardapio.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_alteracao_minhas_solicitacoes(
    client_autenticado_vinculo_escola_cardapio,
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_ALTERACAO_CARD}/{constants.SOLICITACOES_DO_USUARIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_url_endpoint_alt_card_inicio_403(
    client_autenticado_vinculo_dre_cardapio, alteracao_cardapio
):
    assert str(alteracao_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    # somente escola pode iniciar fluxo
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_url_endpoint_alt_card_criar_update(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio,
    escola,
    tipo_alimentacao,
    alteracao_substituicoes_params,
    periodo_escolar,
):
    hoje = datetime.date.today()
    if hoje.month == 12 and hoje.day in [28, 29, 30, 31]:
        return
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(alteracao_substituicoes_params),
    )
    assert response.status_code == status.HTTP_201_CREATED
    resp_json = response.json()

    dia_alteracao_formatada = datetime.datetime.strptime(
        alteracao_substituicoes_params["alterar_dia"], "%Y-%m-%d"
    ).strftime("%d/%m/%Y")
    assert resp_json["data_inicial"] == dia_alteracao_formatada
    assert resp_json["data_final"] == dia_alteracao_formatada

    assert resp_json["status_explicacao"] == "RASCUNHO"
    assert resp_json["escola"] == str(alteracao_substituicoes_params["escola"])
    assert resp_json["motivo"] == str(alteracao_substituicoes_params["motivo"])

    assert len(resp_json["datas_intervalo"]) == 3

    substituicao = resp_json["substituicoes"][0]
    payload_substituicao = alteracao_substituicoes_params["substituicoes"][0]
    assert substituicao["periodo_escolar"] == str(
        payload_substituicao["periodo_escolar"]
    )
    assert substituicao["tipos_alimentacao_de"][0] == str(
        payload_substituicao["tipos_alimentacao_de"][0]
    )
    assert substituicao["tipos_alimentacao_para"][0] == str(
        payload_substituicao["tipos_alimentacao_para"][0]
    )
    assert substituicao["qtd_alunos"] == 10

    response_update = client_autenticado_vinculo_escola_cardapio.patch(
        f'/{ENDPOINT_ALTERACAO_CARD}/{resp_json["uuid"]}/',
        content_type="application/json",
        data=json.dumps(alteracao_substituicoes_params),
    )
    assert response_update.status_code == status.HTTP_200_OK
    assert len(resp_json["datas_intervalo"]) == 3


def test_url_endpoint_alterar_tipos_alimentacao(
    client_autenticado_vinculo_escola_cardapio, alterar_tipos_alimentacao_data
):
    vinculo = alterar_tipos_alimentacao_data["vinculo"]
    tipos_alimentacao = alterar_tipos_alimentacao_data["tipos_alimentacao"]
    dict_params = {
        "periodo_escolar": str(vinculo.periodo_escolar.uuid),
        "tipo_unidade_escolar": str(vinculo.tipo_unidade_escolar.uuid),
        "tipos_alimentacao": [str(tp.uuid) for tp in tipos_alimentacao],
        "uuid": str(vinculo.uuid),
    }
    url = f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/atualizar_lista_de_vinculos/"
    response = client_autenticado_vinculo_escola_cardapio.put(
        url,
        content_type="application/json",
        data=json.dumps({"vinculos": [dict_params]}),
    )
    vinculo_atualizado = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.first()
    )
    assert response.status_code == status.HTTP_200_OK
    assert vinculo_atualizado.tipos_alimentacao.count() == 2


def test_url_endpoint_alt_card_inicio(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio
):
    assert str(alteracao_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    assert str(json["uuid"]) == str(alteracao_cardapio.uuid)


def test_url_endpoint_alt_card_cei_inicio(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio_cei
):
    assert str(alteracao_cardapio_cei.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{alteracao_cardapio_cei.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    assert str(json["uuid"]) == str(alteracao_cardapio_cei.uuid)


def test_url_endpoint_alt_card_inicio_error(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio_dre_validar
):
    assert (
        str(alteracao_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validar.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'inicia_fluxo'"
        " isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_alt_card_dre_valida(
    client_autenticado_vinculo_dre_cardapio, alteracao_cardapio_dre_validar
):
    assert (
        str(alteracao_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validar.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    assert str(json["uuid"]) == str(alteracao_cardapio_dre_validar.uuid)


def test_url_endpoint_alt_card_codae_questiona(
    client_autenticado_vinculo_codae_cardapio, alteracao_cardapio_dre_validado
):
    assert (
        str(alteracao_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    observacao_questionamento_codae = "VAI_DAR?"
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validado.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/",
        data={"observacao_questionamento_codae": observacao_questionamento_codae},
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["logs"][0]["justificativa"] == observacao_questionamento_codae
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    assert str(json["uuid"]) == str(alteracao_cardapio_dre_validado.uuid)
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validado.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/",
        data={"observacao_questionamento_codae": observacao_questionamento_codae},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_questiona'"
        " isn't available from state 'CODAE_QUESTIONADO'."
    }


def test_url_endpoint_alt_card_terceirizada_responde_questionamento(
    client_autenticado_vinculo_terceirizada_cardapio,
    alteracao_cardapio_codae_questionado,
):
    assert (
        str(alteracao_cardapio_codae_questionado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    justificativa = "VAI DAR NÃO :("
    resposta_sim_nao = False
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/"
        f"{alteracao_cardapio_codae_questionado.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta_sim_nao},
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["logs"][0]["justificativa"] == justificativa
    assert (
        json["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    assert str(json["uuid"]) == str(alteracao_cardapio_codae_questionado.uuid)
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/"
        f"{alteracao_cardapio_codae_questionado.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta_sim_nao},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition "
        "'terceirizada_responde_questionamento' isn't available from state "
        "'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
    }


@freeze_time("2019-10-1")
def test_url_endpoint_alt_card_escola_cancela(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio_codae_questionado
):
    assert (
        str(alteracao_cardapio_codae_questionado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_codae_questionado.uuid}/{constants.ESCOLA_CANCELA}/",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU
    assert str(json["uuid"]) == str(alteracao_cardapio_codae_questionado.uuid)
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_codae_questionado.uuid}/{constants.ESCOLA_CANCELA}/",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Solicitação já está cancelada"
    }


@freeze_time("2019-10-1")
def test_url_endpoint_alt_card_escola_cancela_datas_intervalo(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio_com_datas_intervalo
):
    data = {
        "datas": [
            i.data.strftime("%Y-%m-%d")
            for i in alteracao_cardapio_com_datas_intervalo.datas_intervalo.all()[:1]
        ]
    }
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_com_datas_intervalo.uuid}/{constants.ESCOLA_CANCELA}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_200_OK
    alteracao_cardapio_com_datas_intervalo.refresh_from_db()
    assert alteracao_cardapio_com_datas_intervalo.status == "DRE_A_VALIDAR"

    data = {
        "datas": [
            i.data.strftime("%Y-%m-%d")
            for i in alteracao_cardapio_com_datas_intervalo.datas_intervalo.all()[1:]
        ]
    }
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_com_datas_intervalo.uuid}/{constants.ESCOLA_CANCELA}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_200_OK
    alteracao_cardapio_com_datas_intervalo.refresh_from_db()
    assert alteracao_cardapio_com_datas_intervalo.status == "ESCOLA_CANCELOU"


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_erro_sem_dia_letivo(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    periodo_manha,
    escola_com_vinculo_alimentacao,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_vinculo_alimentacao.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()[0]
        == "Não é possível solicitar Lanche Emergencial para dia(s) não letivo(s)"
    )


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_dia_letivo(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 1
    assert alteracao.datas_intervalo.get().data == datetime.date(2023, 11, 18)


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_inclusao_normal_autorizada(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_nao_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
    inclusao_normal_autorizada_periodo_manha,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_nao_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 1
    assert alteracao.datas_intervalo.get().data == datetime.date(2023, 11, 19)


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_inclusao_normal_autorizada_periodo_errado(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
    inclusao_normal_autorizada_periodo_tarde,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 1
    assert alteracao.datas_intervalo.get().data == datetime.date(2023, 11, 18)


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_inclusao_continua_autorizada(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_nao_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
    inclusao_continua_autorizada_periodo_manha,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_nao_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 2


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_inclusao_continua_autorizada_dias_semana(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
    inclusao_continua_autorizada_periodo_manha_dias_semana,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 1
    assert alteracao.datas_intervalo.get().data == datetime.date(2023, 11, 18)


@freeze_time("2023-11-09")
def test_url_endpoint_alt_card_datas_intervalo_lanche_emergencial_com_inclusao_continua_autorizada_periodo_errado(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    escola_com_dias_letivos,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao,
    tipo_alimentacao_lanche_emergencial,
    inclusao_continua_autorizada_periodo_tarde,
):
    data = {
        "motivo": f"{str(motivo_alteracao_cardapio_lanche_emergencial.uuid)}",
        "data_inicial": "18/11/2023",
        "data_final": "19/11/2023",
        "observacao": "<p>cozinha em reforma</p>",
        "eh_alteracao_com_lanche_repetida": False,
        "escola": f"{str(escola_com_dias_letivos.uuid)}",
        "substituicoes": [
            {
                "periodo_escolar": f"{str(periodo_manha.uuid)}",
                "tipos_alimentacao_de": [f"{str(tipo_alimentacao.uuid)}"],
                "tipos_alimentacao_para": [
                    f"{str(tipo_alimentacao_lanche_emergencial.uuid)}"
                ],
                "qtd_alunos": "100",
            }
        ],
        "datas_intervalo": [{"data": "2023-11-18"}, {"data": "2023-11-19"}],
    }
    response = client_autenticado_vinculo_escola_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    alteracao = AlteracaoCardapio.objects.get(uuid=response.json()["uuid"])
    assert alteracao.datas_intervalo.count() == 1
    assert alteracao.datas_intervalo.get().data == datetime.date(2023, 11, 18)


def test_url_endpoint_alt_card_dre_valida_error(
    client_autenticado_vinculo_dre_cardapio, alteracao_cardapio
):
    assert str(alteracao_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_valida'"
        " isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_alt_card_dre_nao_valida(
    client_autenticado_vinculo_dre_cardapio, alteracao_cardapio_dre_validar
):
    assert (
        str(alteracao_cardapio_dre_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validar.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA
    assert str(json["uuid"]) == str(alteracao_cardapio_dre_validar.uuid)


def test_url_endpoint_alt_card_dre_nao_valida_error(
    client_autenticado_vinculo_dre_cardapio, alteracao_cardapio_dre_validado
):
    assert (
        str(alteracao_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_dre_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validado.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_nao_valida' "
        "isn't available from state 'DRE_VALIDADO'."
    }


def test_url_endpoint_alt_card_codae_autoriza(
    client_autenticado_vinculo_codae_cardapio, alteracao_cardapio_dre_validado
):
    assert (
        str(alteracao_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validado.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    assert str(json["uuid"]) == str(alteracao_cardapio_dre_validado.uuid)


def test_url_endpoint_alt_card_codae_autoriza_error(
    client_autenticado_vinculo_codae_cardapio, alteracao_cardapio
):
    assert str(alteracao_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_autoriza_questionamento' "
        "isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_alt_card_codae_nega(
    client_autenticado_vinculo_codae_cardapio, alteracao_cardapio_dre_validado
):
    assert (
        str(alteracao_cardapio_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_dre_validado.uuid}/{constants.CODAE_NEGA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO
    assert str(json["uuid"]) == str(alteracao_cardapio_dre_validado.uuid)


def test_url_endpoint_alt_card_codae_nega_error(
    client_autenticado_vinculo_codae_cardapio, alteracao_cardapio_codae_autorizado
):
    assert (
        str(alteracao_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_codae_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_codae_autorizado.uuid}/{constants.CODAE_NEGA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_nega_questionamento'"
        " isn't available from state 'CODAE_AUTORIZADO'."
    }


def test_url_endpoint_alt_card_terceirizada_ciencia(
    client_autenticado_vinculo_terceirizada_cardapio,
    alteracao_cardapio_codae_autorizado,
):
    assert (
        str(alteracao_cardapio_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio_codae_autorizado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    assert str(json["uuid"]) == str(alteracao_cardapio_codae_autorizado.uuid)


def test_url_endpoint_alt_card_terceirizada_ciencia_error(
    client_autenticado_vinculo_terceirizada_cardapio, alteracao_cardapio
):
    assert str(alteracao_cardapio.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_terceirizada_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia'"
        " isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_alt_card_relatorio(client_autenticado, alteracao_cardapio):
    response = client_autenticado.get(
        f"/{ENDPOINT_ALTERACAO_CARD}/{alteracao_cardapio.uuid}/{constants.RELATORIO}/"
    )
    id_externo = alteracao_cardapio.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="alteracao_cardapio_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_alt_card_cei_relatorio(
    client_autenticado, alteracao_cardapio_cei
):
    response = client_autenticado.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{alteracao_cardapio_cei.uuid}/{constants.RELATORIO}/"
    )
    id_externo = alteracao_cardapio_cei.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="alteracao_cardapio_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_get_vinculos_tipo_alimentacao(
    client_autenticado_vinculo_escola, vinculo_tipo_alimentacao
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert json[0]["uuid"] == str(vinculo_tipo_alimentacao.uuid)
    assert json[0]["periodo_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.periodo_escolar.uuid
    )
    assert json[0]["tipo_unidade_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid
    )
    assert len(json[0]["tipos_alimentacao"]) == 5

    # testa endpoint de filtro tipo_ue
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/tipo_unidade_escolar/{vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid}/",
    )
    json = response.json()["results"]
    assert json[0]["uuid"] == str(vinculo_tipo_alimentacao.uuid)
    assert json[0]["periodo_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.periodo_escolar.uuid
    )
    assert json[0]["tipo_unidade_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid
    )
    assert len(json[0]["tipos_alimentacao"]) == 5


def test_endpoint_horario_do_combo_tipo_alimentacao_unidade_escolar(
    client_autenticado_vinculo_escola, horario_tipo_alimentacao
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_HORARIO_DO_COMBO}/escola/{horario_tipo_alimentacao.escola.uuid}/"
    )
    json = response.json()["results"]
    assert response.status_code == status.HTTP_200_OK
    assert json[0]["uuid"] == str(horario_tipo_alimentacao.uuid)
    assert json[0]["hora_inicial"] == horario_tipo_alimentacao.hora_inicial
    assert json[0]["hora_final"] == horario_tipo_alimentacao.hora_final
    assert json[0]["tipo_alimentacao"] == {
        "uuid": "c42a24bb-14f8-4871-9ee8-05bc42cf3061",
        "posicao": 2,
        "nome": "Lanche",
    }
    assert json[0]["periodo_escolar"] == {
        "uuid": "22596464-271e-448d-bcb3-adaba43fffc8",
        "tipo_turno": None,
        "nome": "TARDE",
        "posicao": None,
        "possui_alunos_regulares": None,
    }
    assert json[0]["escola"] == {
        "uuid": "a627fc63-16fd-482c-a877-16ebc1a82e57",
        "nome": "EMEF JOAO MENDES",
        "codigo_eol": "000546",
        "quantidade_alunos": 0,
    }


def checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
    client_autenticado, classe, path
):
    obj = classe.objects.first()
    assert not obj.terceirizada_conferiu_gestao

    response = client_autenticado.patch(
        f"/{path}/{obj.uuid}/marcar-conferida/", content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK

    result = response.json()
    assert "terceirizada_conferiu_gestao" in result.keys()
    assert result["terceirizada_conferiu_gestao"]

    obj = classe.objects.first()
    assert obj.terceirizada_conferiu_gestao


def test_terceirizada_marca_conferencia_inversao_cardapio_viewset(
    client_autenticado, inversao_dia_cardapio
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, InversaoCardapio, "inversoes-dia-cardapio"
    )


def test_terceirizada_marca_conferencia_grupo_suspensao_alimentacao_viewset(
    client_autenticado, grupo_suspensao_alimentacao
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, GrupoSuspensaoAlimentacao, "grupos-suspensoes-alimentacao"
    )


def test_terceirizada_marca_conferencia_alteracao_cardapio_viewset(
    client_autenticado, alteracao_cardapio
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, AlteracaoCardapio, "alteracoes-cardapio"
    )


def test_motivos_alteracao_cardapio_escola_cei_queryset(
    client_autenticado_vinculo_escola_cei_cardapio,
    motivo_alteracao_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    motivo_alteracao_cardapio_inativo,
):
    response = client_autenticado_vinculo_escola_cei_cardapio.get(
        "/motivos-alteracao-cardapio/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_motivos_alteracao_cardapio_queryset(
    client_autenticado_vinculo_escola_cardapio,
    motivo_alteracao_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    motivo_alteracao_cardapio_inativo,
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        "/motivos-alteracao-cardapio/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 2


@freeze_time("2023-07-14")
def test_alteracao_cemei_solicitacoes_dre(
    client_autenticado_vinculo_dre_escola_cemei, alteracao_cemei_dre_a_validar
):
    response = client_autenticado_vinculo_dre_escola_cemei.get(
        f"/alteracoes-cardapio-cemei/{constants.PEDIDOS_DRE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={alteracao_cemei_dre_a_validar.rastro_lote.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@freeze_time("2023-07-14")
def test_alteracao_cemei_solicitacoes_codae(
    client_autenticado_vinculo_codae_cardapio, alteracao_cemei_dre_validado
):
    response = client_autenticado_vinculo_codae_cardapio.get(
        f"/alteracoes-cardapio-cemei/{constants.PEDIDOS_CODAE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={alteracao_cemei_dre_validado.rastro_lote.uuid}"
        f"&diretoria_regional={alteracao_cemei_dre_validado.rastro_dre.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_cei(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio,
    periodo_escolar,
    tipo_alimentacao,
    faixas_etarias_ativas,
):
    data = {
        "escola": str(escola_cemei.uuid),
        "motivo": str(motivo_alteracao_cardapio.uuid),
        "alunos_cei_e_ou_emei": "CEI",
        "alterar_dia": "30/07/2023",
        "substituicoes_cemei_cei_periodo_escolar": [
            {
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao.uuid)],
                "tipos_alimentacao_para": [str(tipo_alimentacao.uuid)],
                "faixas_etarias": [
                    {
                        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
                        "quantidade": "12",
                        "matriculados_quando_criado": 33,
                    }
                ],
            }
        ],
        "substituicoes_cemei_emei_periodo_escolar": [],
        "observacao": "<p>adsasdasd</p>",
    }
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["escola"] == str(escola_cemei.uuid)
    assert response.json()["alunos_cei_e_ou_emei"] == "CEI"
    assert len(response.json()["substituicoes_cemei_cei_periodo_escolar"]) == 1
    assert len(response.json()["substituicoes_cemei_emei_periodo_escolar"]) == 0
    assert response.json()["alterar_dia"] == "30/07/2023"
    assert response.json()["status"] == "RASCUNHO"


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_emei(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio,
    periodo_escolar,
    tipo_alimentacao,
):
    data = {
        "escola": str(escola_cemei.uuid),
        "motivo": str(motivo_alteracao_cardapio.uuid),
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": "30/07/2023",
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "30",
                "matriculados_quando_criado": 75,
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao.uuid)],
                "tipos_alimentacao_para": [str(tipo_alimentacao.uuid)],
            }
        ],
        "observacao": "<p>adsasdasd</p>",
    }
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["escola"] == str(escola_cemei.uuid)
    assert response.json()["alunos_cei_e_ou_emei"] == "EMEI"
    assert len(response.json()["substituicoes_cemei_cei_periodo_escolar"]) == 0
    assert len(response.json()["substituicoes_cemei_emei_periodo_escolar"]) == 1
    assert response.json()["alterar_dia"] == "30/07/2023"
    assert response.json()["status"] == "RASCUNHO"
