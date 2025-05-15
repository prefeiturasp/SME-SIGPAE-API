import json

import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.cardapio.__tests__.utils import (
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
)
from sme_sigpae_api.cardapio.utils import converter_data
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import (
    InformativoPartindoDaEscolaWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)

pytestmark = pytest.mark.django_db

ENDPOINT_SUSPENSOES = "grupos-suspensoes-alimentacao"


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


def test_terceirizada_marca_conferencia_grupo_suspensao_alimentacao_viewset(
    client_autenticado, grupo_suspensao_alimentacao
):
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, GrupoSuspensaoAlimentacao, "grupos-suspensoes-alimentacao"
    )
