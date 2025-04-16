import pytest
from freezegun import freeze_time
from model_mommy import mommy
from rest_framework import status

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import (
    PedidoAPartirDaDiretoriaRegionalWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ..models import SolicitacaoKitLancheAvulsa, SolicitacaoKitLancheUnificada

pytestmark = pytest.mark.django_db

ENDPOINT_AVULSO = "solicitacoes-kit-lanche-avulsa"
ENDPOINT_UNIFICADO = "solicitacoes-kit-lanche-unificada"


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_nao_pode(
    client_autenticado, solicitacao_avulsa
):
    client_q_nao_faz_parte_da_escola = client_autenticado
    response = client_q_nao_faz_parte_da_escola.get(f"/{ENDPOINT_AVULSO}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_pode(
    client_admin_django, solicitacao_avulsa
):
    response = client_admin_django.get(f"/{ENDPOINT_AVULSO}/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["results"], list)


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_inicio_fluxo(
    client_autenticado_da_escola, solicitacao_avulsa, periodo_escolar
):
    assert str(solicitacao_avulsa.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    mommy.make(
        "escola.AlunosMatriculadosPeriodoEscola",
        escola=solicitacao_avulsa.escola,
        quantidade_alunos=800,
        periodo_escolar=periodo_escolar,
    )
    response = client_autenticado_da_escola.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == "DRE_A_VALIDAR"
    solicitacao_avulsa_atualizada = SolicitacaoKitLancheAvulsa.objects.get(
        id=solicitacao_avulsa.id
    )
    assert (
        str(solicitacao_avulsa_atualizada.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    assert str(json["uuid"]) == str(solicitacao_avulsa.uuid)


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_inicio_fluxo_exception(
    client_autenticado_da_escola, solicitacao_avulsa_dre_a_validar, periodo_escolar
):
    assert (
        str(solicitacao_avulsa_dre_a_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    mommy.make(
        "escola.AlunosMatriculadosPeriodoEscola",
        escola=solicitacao_avulsa_dre_a_validar.escola,
        quantidade_alunos=800,
        periodo_escolar=periodo_escolar,
    )
    response = client_autenticado_da_escola.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_a_validar.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'inicia_fluxo' isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_dre_valida(
    client_autenticado_da_dre, solicitacao_avulsa_dre_a_validar
):
    assert (
        str(solicitacao_avulsa_dre_a_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )

    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_a_validar.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_dre_valida_erro(
    client_autenticado_da_dre, solicitacao_avulsa_rascunho
):
    assert (
        str(solicitacao_avulsa_rascunho.status)
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )

    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_rascunho.uuid}/{constants.DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'dre_valida' isn't available from state "
            + "'RASCUNHO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_dre_nao_valida(
    client_autenticado_da_dre, solicitacao_avulsa_dre_a_validar
):
    assert (
        str(solicitacao_avulsa_dre_a_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    justificativa = "TESTE@@@@"
    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_a_validar.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/",
        data={"justificativa": justificativa},
        content_type="application/json",
    )
    json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA
    assert json["logs"][0]["justificativa"] == justificativa


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_nao_dre_valida_erro(
    client_autenticado_da_dre, solicitacao_avulsa_rascunho
):
    assert (
        str(solicitacao_avulsa_rascunho.status)
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )

    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_rascunho.uuid}/{constants.DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'dre_nao_valida' isn't available from state "
            + "'RASCUNHO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_autoriza(
    client_autenticado_da_codae, solicitacao_avulsa_dre_validado
):
    assert (
        str(solicitacao_avulsa_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_validado.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_autoriza_erro(
    client_autenticado_da_codae, solicitacao_avulsa_dre_a_validar
):
    assert (
        str(solicitacao_avulsa_dre_a_validar.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )

    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_a_validar.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'codae_autoriza_questionamento' isn't available from state "
            + "'DRE_A_VALIDAR'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_questiona(
    client_autenticado_da_codae, solicitacao_avulsa_dre_validado
):
    assert (
        str(solicitacao_avulsa_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_validado.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_terc_resp_quest(
    client_autenticado_da_terceirizada, solicitacao_avulsa_codae_questionado
):
    justificativa = "VAI DAR NÂO :("
    resposta_sim_nao = False
    assert (
        str(solicitacao_avulsa_codae_questionado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_AVULSO}/"
        f"{solicitacao_avulsa_codae_questionado.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta_sim_nao},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["logs"][0]["justificativa"] == justificativa
    assert (
        json["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_terc_resp_quest_erro(
    client_autenticado_da_terceirizada, solic_avulsa_terc_respondeu_questionamento
):
    justificativa = "VAI DAR NÂO :("
    resposta_sim_nao = False
    assert (
        str(solic_avulsa_terc_respondeu_questionamento.status)
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_AVULSO}/"
        f"{solic_avulsa_terc_respondeu_questionamento.uuid}/"
        f"{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta_sim_nao},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'terceirizada_responde_questionamento' isn't available from state "
            + "'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_questiona_erro(
    client_autenticado_da_codae, solic_avulsa_terc_respondeu_questionamento
):
    assert (
        str(solic_avulsa_terc_respondeu_questionamento.status)
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solic_avulsa_terc_respondeu_questionamento.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'codae_questiona' isn't available from state "
            + "'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_nega(
    client_autenticado_da_codae, solicitacao_avulsa_dre_validado
):
    assert (
        str(solicitacao_avulsa_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    justificativa = "TESTE_XxX"
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_validado.uuid}/{constants.CODAE_NEGA_PEDIDO}/",
        data={"justificativa": justificativa},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO
    assert json["logs"][0]["justificativa"] == justificativa


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_codae_nega_erro(
    client_autenticado_da_codae, solicitacao_avulsa_codae_autorizado
):
    assert (
        str(solicitacao_avulsa_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_codae_autorizado.uuid}/{constants.CODAE_NEGA_PEDIDO}/",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'codae_nega_questionamento' isn't available from state "
            + "'CODAE_AUTORIZADO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_terceirizada_ciencia(
    client_autenticado_da_terceirizada, solicitacao_avulsa_codae_autorizado
):
    assert (
        str(solicitacao_avulsa_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )

    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_codae_autorizado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_terceirizada_ciencia_erro(
    client_autenticado_da_terceirizada, solicitacao_avulsa_dre_validado
):
    assert (
        str(solicitacao_avulsa_dre_validado.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )

    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_validado.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": (
            "Erro de transição de estado: Transition 'terceirizada_toma_ciencia' isn't available from state "
            + "'DRE_VALIDADO'."
        )
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_relatorio(
    client_autenticado, solicitacao_avulsa_dre_validado
):
    response = client_autenticado.get(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_validado.uuid}/{constants.RELATORIO}/"
    )
    id_externo = solicitacao_avulsa_dre_validado.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="solicitacao_avulsa_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


@freeze_time("2019-11-12")
def test_url_endpoint_solicitacoes_kit_lanche_avulsa_escola_cancela(
    client_autenticado_da_escola, solicitacao_avulsa_codae_autorizado
):
    # A solicitação é do dia 18/11/2019
    assert (
        str(solicitacao_avulsa_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_escola.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_codae_autorizado.uuid}/{constants.ESCOLA_CANCELA}/",
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU


@freeze_time("2019-11-12")
def test_url_endpoint_solicitacoes_kit_lanche_avulsa_escola_cancela_com_dia_suspensao(
    client_autenticado_da_escola,
    dia_suspensao_atividades_2019_11_13,
    solicitacao_avulsa_codae_autorizado,
):
    # A solicitação é do dia 18/11/2019

    assert (
        str(solicitacao_avulsa_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_escola.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_codae_autorizado.uuid}/{constants.ESCOLA_CANCELA}/",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Só pode cancelar com no mínimo 2 dia(s) úteis de antecedência"
    }


@freeze_time("2019-11-17")
def test_url_endpoint_solicitacoes_kit_lanche_avulsa_escola_cancela_error(
    client_autenticado_da_escola, solicitacao_avulsa_codae_autorizado
):
    # A solicitação é do dia 18/11/2019
    assert (
        str(solicitacao_avulsa_codae_autorizado.status)
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_escola.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_codae_autorizado.uuid}/{constants.ESCOLA_CANCELA}/",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Só pode cancelar com no mínimo 2 dia(s) úteis de antecedência"
    }


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_deletar(
    client_autenticado_da_escola, solicitacao_avulsa
):
    assert str(solicitacao_avulsa.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_da_escola.delete(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_deletar_403_nao_e_rascunho(
    client_autenticado_da_escola, solicitacao_avulsa_dre_a_validar
):
    assert (
        str(solicitacao_avulsa_dre_a_validar.status)
        != PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_da_escola.delete(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_dre_a_validar.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }


#
# Unificado
#
# solicitacao_unificada_lista_igual_codae_a_autorizar


def test_url_endpoint_solicitacoes_kit_lanche_unificada_codae_autoriza(
    client_autenticado_da_codae, solicitacao_unificada_lista_igual_codae_a_autorizar
):
    solicacao = solicitacao_unificada_lista_igual_codae_a_autorizar
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.CODAE_AUTORIZA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO


def test_url_endpoint_solicitacoes_kit_lanche_unificada_codae_questiona(
    client_autenticado_da_codae, solicitacao_unificada_lista_igual_codae_a_autorizar
):
    solicacao = solicitacao_unificada_lista_igual_codae_a_autorizar
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.CODAE_QUESTIONA_PEDIDO}/",
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO


def test_url_endpoint_solicitacoes_kit_lanche_unificada_terceirizada_responde(
    client_autenticado_da_terceirizada,
    solicitacao_unificada_lista_igual_codae_questionado,
):
    justificativa = "VAI DAR SIM, TENHO MUITO ESTOQUE EM CASA, MAS VOU TROCAR TODDYNHO POR CHOCOBOM OK? "
    resposta_sim_nao = True
    solicacao = solicitacao_unificada_lista_igual_codae_questionado
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/",
        data={"justificativa": justificativa, "resposta_sim_nao": resposta_sim_nao},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert (
        json["status"]
        == PedidoAPartirDaDiretoriaRegionalWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    assert json["logs"][0]["justificativa"] == justificativa


def test_url_endpoint_solicitacoes_kit_lanche_unificada_codae_autoriza_nega(
    client_autenticado_da_codae, solicitacao_unificada_lista_igual_codae_a_autorizar
):
    solicacao = solicitacao_unificada_lista_igual_codae_a_autorizar
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR
    )
    response = client_autenticado_da_codae.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.CODAE_NEGA_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_NEGOU_PEDIDO


def test_url_endpoint_solicitacoes_kit_lanche_unificado_inicio(
    client_autenticado_da_dre, solicitacao_unificada_lista_igual
):
    """Uma solicitação unificada é dividida em duas ou mais em função dos lotes que ela tem."""
    assert (
        str(solicitacao_unificada_lista_igual.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.RASCUNHO
    )
    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicitacao_unificada_lista_igual.uuid}/{constants.DRE_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json_list = response.json()
    assert isinstance(json_list, list)
    for json in json_list:
        assert isinstance(json, dict)
        assert (
            json["status"] == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR
        )


def test_url_endpoint_solicitacoes_kit_lanche_unificada_terceirizada_ciencia(
    client_autenticado_da_terceirizada,
    solicitacao_unificada_lista_igual_codae_autorizado,
):
    solicacao = solicitacao_unificada_lista_igual_codae_autorizado
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_terceirizada.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.TERCEIRIZADA_TOMOU_CIENCIA}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert (
        json["status"]
        == PedidoAPartirDaDiretoriaRegionalWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    )


@freeze_time("2019-10-09")
def test_url_endpoint_solicitacoes_kit_lanche_unificada_dre_cancela(
    client_autenticado_da_dre, solicitacao_unificada_lista_igual_codae_autorizado
):
    # A solicitação é do dia 14/10/2019
    solicacao = solicitacao_unificada_lista_igual_codae_autorizado
    justificativa = "CANCELA DRE"
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.DRE_CANCELA}/",
        data={"justificativa": justificativa},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU
    assert json["logs"][0]["justificativa"] == justificativa


@freeze_time("2019-10-10")  # também dia 13 ou 14
def test_url_endpoint_solicitacoes_kit_lanche_unificada_dre_cancela_em_cima_da_hora(
    client_autenticado_da_dre, solicitacao_unificada_lista_igual_codae_autorizado
):
    # A solicitação é do dia 14/10/2019
    solicacao = solicitacao_unificada_lista_igual_codae_autorizado
    justificativa = "CANCELA DRE"
    assert (
        str(solicacao.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO
    )
    response = client_autenticado_da_dre.patch(
        f"/{ENDPOINT_UNIFICADO}/{solicacao.uuid}/{constants.DRE_CANCELA}/",
        data={"justificativa": justificativa},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json = response.json()
    assert json == {
        "detail": "Erro de transição de estado: Só pode cancelar com no mínimo 2 dia(s) úteis de antecedência"
    }


def test_url_endpoint_solicitacoes_kit_lanche_unificado_deletar(
    client_autenticado_da_dre, solicitacao_unificada_lista_igual
):
    assert (
        str(solicitacao_unificada_lista_igual.status)
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_da_dre.delete(
        f"/{ENDPOINT_UNIFICADO}/{solicitacao_unificada_lista_igual.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data is None


def test_url_endpoint_solicitacoes_kit_lanche_unificado_get_detalhe(
    client_autenticado_da_terceirizada,
    solicitacao_unificada_lista_igual_codae_questionado,
):
    assert (
        str(solicitacao_unificada_lista_igual_codae_questionado.status)
        == PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_QUESTIONADO
    )
    response = client_autenticado_da_terceirizada.get(
        f"/{ENDPOINT_UNIFICADO}/{solicitacao_unificada_lista_igual_codae_questionado.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(
        solicitacao_unificada_lista_igual_codae_questionado.uuid
    )


def test_url_endpoint_solicitacoes_kit_lanche_unificado_relatorio(
    client_autenticado_da_escola, solicitacao_unificada_lista_igual_codae_questionado
):
    response = client_autenticado_da_escola.get(
        f"/{ENDPOINT_UNIFICADO}/{solicitacao_unificada_lista_igual_codae_questionado.uuid}/{constants.RELATORIO}/"
    )
    id_externo = solicitacao_unificada_lista_igual_codae_questionado.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="solicitacao_unificada_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


@freeze_time("2019-10-11")
def test_create_kit_lanche(
    client_autenticado_da_escola,
    solicitacao_avulsa,
    escola,
    kit_lanche,
    aluno,
    periodo_escolar,
):
    """Primeiro cria-se 3 rascunhos (POST) 200, 200, 200 totalizando 600 alunos que é mais que 500.

    Após isso, vamos efetivar a solicitacao (PATCH), no qual sai de RASCUNHO para DRE_A_VALIDAR, deve-se
    autorizar as duas primeiras 200+200=400 e a ultima deve dar problema por exceder a quantidade de alunos (600)
    da escola
    """
    escola.save()
    mommy.make(
        "escola.AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=400,
        periodo_escolar=periodo_escolar,
    )
    data_do_evento = "27/11/2019"
    step = 200
    solicitacoes_avulsas = []
    for _ in range(3):
        response_criacao1 = client_autenticado_da_escola.post(
            f"/{ENDPOINT_AVULSO}/",
            content_type="application/json",
            data={
                "solicitacao_kit_lanche": {
                    "kits": [kit_lanche.uuid],
                    "descricao": "<p>123213213</p>\n",
                    "data": data_do_evento,
                    "tempo_passeio": 0,
                },
                "local": "TESTE!!!",
                "quantidade_alunos": step,
                "escola": escola.uuid,
                "alunos_com_dieta_especial_participantes": [aluno.uuid],
            },
        )
        # deve permitir todos sem problema pois são criados com status inicial RASCUNHO
        assert response_criacao1.status_code == status.HTTP_201_CREATED
        json = response_criacao1.json()
        assert json["quantidade_alunos"] == step
        assert json["status_explicacao"] == PedidoAPartirDaEscolaWorkflow.RASCUNHO

        solicitacao = SolicitacaoKitLancheAvulsa.objects.get(uuid=json["uuid"])
        solicitacoes_avulsas.append(solicitacao)

    for sol_index in range(len(solicitacoes_avulsas)):
        response = client_autenticado_da_escola.patch(
            f"/{ENDPOINT_AVULSO}/{solicitacoes_avulsas[sol_index].uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
        )
        json = response.json()
        # deve passar pra frente os dois primeiros, o terceiro não deve ser permitido.
        if sol_index < 2:
            assert response.status_code == status.HTTP_200_OK
            assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
        else:
            assert json == {
                "detail": "A quantidade de alunos informados para o evento excede a quantidade de alunos"
                " matriculados na escola. Na data 27-11-2019 já tem pedidos para 400 alunos"
            }


@freeze_time("2019-10-11")
def test_kit_lanche_nao_deve_permitir_editar_status_diretamente(
    client_autenticado_da_escola, solicitacao_avulsa, escola, kit_lanche, aluno
):
    data_teste = "27/11/2019"
    response_criacao1 = client_autenticado_da_escola.post(
        f"/{ENDPOINT_AVULSO}/",
        content_type="application/json",
        data={
            # status não deve surtir efeito
            "status": PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
            "solicitacao_kit_lanche": {
                "kits": [kit_lanche.uuid],
                "descricao": "<p>123213213</p>\n",
                "data": data_teste,
                "tempo_passeio": 0,
            },
            "local": "TESTE!!!",
            "quantidade_alunos": 100,
            "escola": escola.uuid,
            "alunos_com_dieta_especial_participantes": [aluno.uuid],
        },
    )
    assert response_criacao1.status_code == status.HTTP_201_CREATED
    json = response_criacao1.json()
    # deve ser rascunho e não codae autorizado
    assert json["status_explicacao"] == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    assert json.get("status") is None


def test_url_endpoint_consulta_kits_lanche(client_autenticado, kit_lanche):
    client = client_autenticado
    response = client.get("/kit-lanches/consulta-kits/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    item = data["results"][0]

    assert isinstance(item, dict)


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


def test_terceirizada_marca_conferencia_solicitacao_avulsa_viewset(
    client_autenticado, solicitacao_avulsa
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado, SolicitacaoKitLancheAvulsa, "solicitacoes-kit-lanche-avulsa"
    )


def test_terceirizada_marca_conferencia_solicitacao_kitlanche_unificada_viewset(
    client_autenticado, solicitacao_unificada_lista_igual_codae_autorizado
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado,
        SolicitacaoKitLancheUnificada,
        "solicitacoes-kit-lanche-unificada",
    )


def test_url_endpoint_solicitacao_kit_lanche_cemei(client_autenticado_da_escola):
    data = {
        "escola": "230453bb-d6f1-4513-b638-8d6d150d1ac6",
        "local": "Parque do Ibirapuera",
        "alunos_cei_e_ou_emei": "CEI",
        "data": "2020-09-20",
        "solicitacao_cei": {
            "kits": ["b9c58783-9131-4e8d-a5fb-89974ca5cbfc"],
            "alunos_com_dieta_especial_participantes": [
                "2d20157a-4e52-4d25-a4c7-9c0e6b67ee18"
            ],
            "tempo_passeio": 2,
            "faixas_quantidades": [
                {
                    "faixa_etaria": "a26bcacc-a9e0-4f2d-b03d-d9d5ff63f8e7",
                    "quantidade_alunos": 18,
                    "matriculados_quando_criado": 19,
                }
            ],
        },
        "status": "DRE_A_VALIDAR",
        "solicitacao_emei": {
            "kits": ["b9c58783-9131-4e8d-a5fb-89974ca5cbfc"],
            "tempo_passeio": 0,
            "alunos_com_dieta_especial_participantes": [
                "2d20157a-4e52-4d25-a4c7-9c0e6b67ee18"
            ],
            "quantidade_alunos": 12,
            "matriculados_quando_criado": 123,
        },
    }
    response = client_autenticado_da_escola.post(
        "/solicitacao-kit-lanche-cemei/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    uuid_ = response_json["uuid"]

    assert response_json["criado_por"] is not None
    assert response_json["local"] == data["local"]
    assert response_json["data"] == "20/09/2020"
    assert response_json["solicitacao_cei"] is not None
    assert (
        len(response_json["solicitacao_cei"]["alunos_com_dieta_especial_participantes"])
        == 1
    )
    assert response_json["solicitacao_emei"] is not None
    assert (
        len(
            response_json["solicitacao_emei"]["alunos_com_dieta_especial_participantes"]
        )
        == 1
    )

    response = client_autenticado_da_escola.get(
        f'/solicitacao-kit-lanche-cemei/{response_json["uuid"]}/'
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["solicitacao_cei"] is not None
    assert (
        len(response_json["solicitacao_cei"]["alunos_com_dieta_especial_participantes"])
        == 1
    )
    assert response_json["solicitacao_emei"] is not None
    assert (
        len(
            response_json["solicitacao_emei"]["alunos_com_dieta_especial_participantes"]
        )
        == 1
    )

    del data["solicitacao_emei"]

    response = client_autenticado_da_escola.put(
        f"/solicitacao-kit-lanche-cemei/{uuid_}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["solicitacao_emei"] is None

    response = client_autenticado_da_escola.get(
        "/solicitacao-kit-lanche-cemei/?status=RASCUNHO"
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json["results"]) == 1

    response = client_autenticado_da_escola.delete(
        f"/solicitacao-kit-lanche-cemei/{uuid_}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client_autenticado_da_escola.post(
        "/solicitacao-kit-lanche-cemei/", content_type="application/json", data=data
    )
    response_json = response.json()
    uuid_ = response_json["uuid"]
    response = client_autenticado_da_escola.patch(
        f"/solicitacao-kit-lanche-cemei/{uuid_}/inicio-pedido/"
    )
    assert response.json()["status"] == "DRE_A_VALIDAR"
    response = client_autenticado_da_escola.delete(
        f"/solicitacao-kit-lanche-cemei/{uuid_}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        response.json()["detail"]
        == "Você só pode excluir quando o status for RASCUNHO."
    )


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_inicio_fluxo_escola_cmct(
    client_autenticado_da_escola_cmct, solicitacao_avulsa_cmct, periodo_escolar
):
    assert str(solicitacao_avulsa_cmct.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_da_escola_cmct.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_cmct.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == "DRE_A_VALIDAR"
    solicitacao_avulsa_atualizada = SolicitacaoKitLancheAvulsa.objects.get(
        id=solicitacao_avulsa_cmct.id
    )
    assert (
        str(solicitacao_avulsa_atualizada.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    assert str(json["uuid"]) == str(solicitacao_avulsa_cmct.uuid)


def test_url_endpoint_solicitacoes_kit_lanche_avulsa_inicio_fluxo_erro_transicao_escola_cmct(
    client_autenticado_da_escola_cmct, solicitacao_avulsa_cmct, periodo_escolar
):
    solicitacao_avulsa_cmct.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    solicitacao_avulsa_cmct.save()

    assert (
        str(solicitacao_avulsa_cmct.status)
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_da_escola_cmct.patch(
        f"/{ENDPOINT_AVULSO}/{solicitacao_avulsa_cmct.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json = response.json()
    assert (
        json["detail"]
        == "Erro de transição de estado: Transition 'inicia_fluxo' isn't available from state 'DRE_A_VALIDAR'."
    )
