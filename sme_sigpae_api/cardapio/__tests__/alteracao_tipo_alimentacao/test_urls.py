import datetime
import json

import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.cardapio.__tests__.utils import (
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow

pytestmark = pytest.mark.django_db


ENDPOINT_ALTERACAO_CARD = "alteracoes-cardapio"


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


def test_terceirizada_marca_conferencia_alteracao_cardapio_viewset(
    client_autenticado, alteracao_cardapio
):
    _checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, AlteracaoCardapio, "alteracoes-cardapio"
    )


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
