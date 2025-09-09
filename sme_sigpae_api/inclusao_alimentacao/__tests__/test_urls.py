import pytest
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from ...dados_comuns import constants
from ...dados_comuns.constants import (
    CODAE_AUTORIZA_PEDIDO,
    CODAE_NEGA_PEDIDO,
    CODAE_QUESTIONA_PEDIDO,
    DRE_INICIO_PEDIDO,
    DRE_NAO_VALIDA_PEDIDO,
    DRE_VALIDA_PEDIDO,
    ESCOLA_CANCELA,
    PEDIDOS_CODAE,
    PEDIDOS_DRE,
    SEM_FILTRO,
    SOLICITACOES_DO_USUARIO,
    TERCEIRIZADA_RESPONDE_QUESTIONAMENTO,
    TERCEIRIZADA_TOMOU_CIENCIA,
)
from ...dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from ...perfil.models import Usuario
from ..models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)

pytestmark = pytest.mark.django_db


def base_get_request(client_autenticado, resource):
    endpoint = f"/{resource}/"
    response = client_autenticado.get(endpoint)
    assert response.status_code == status.HTTP_200_OK


def test_permissoes_grupo_inclusao_normal_viewset(
    client_autenticado_vinculo_escola_inclusao,
    grupo_inclusao_alimentacao_normal,
    grupo_inclusao_alimentacao_normal_outra_dre,
):
    # pode ver os dados de uma suspensão de alimentação da mesma escola
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma suspensão de alimentação de outra escola
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # não pode ver os dados de TODAS as suspensões de alimentação
    response = client_autenticado_vinculo_escola_inclusao.get(
        "/grupos-inclusao-alimentacao-normal/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_url_endpoint_grupos_inclusao_motivos_inclusao_normal(
    client_autenticado_vinculo_escola_inclusao,
):
    base_get_request(
        client_autenticado_vinculo_escola_inclusao, "motivos-inclusao-normal"
    )


def test_url_endpoint_grupos_inclusao_motivos_inclusao_continua(
    client_autenticado_vinculo_escola_inclusao,
):
    base_get_request(
        client_autenticado_vinculo_escola_inclusao, "motivos-inclusao-continua"
    )


def test_url_endpoint_inclusao_normal_inicio_fluxo(
    client_autenticado_vinculo_escola_inclusao, grupo_inclusao_alimentacao_normal
):
    assert (
        grupo_inclusao_alimentacao_normal.status
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal.uuid}/{DRE_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR


def test_url_endpoint_inclusao_normal_inicio_fluxo_erro(
    client_autenticado_vinculo_escola_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/{DRE_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'inicia_fluxo' isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_normal_dre_valida(
    client_autenticado_vinculo_dre_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/{DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO


def test_url_endpoint_inclusao_normal_dre_valida_erro(
    client_autenticado_vinculo_dre_inclusao, grupo_inclusao_alimentacao_normal
):
    assert (
        grupo_inclusao_alimentacao_normal.status
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    assert (
        GrupoInclusaoAlimentacaoNormal.get_solicitacoes_rascunho(
            grupo_inclusao_alimentacao_normal.criado_por
        ).count()
        == 1
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal.uuid}/{DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_valida' isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_inclusao_normal_dre_nao_valida(
    client_autenticado_vinculo_dre_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/"
        + f"{DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA
    )


def test_url_endpoint_inclusao_normal_dre_nao_valida_erro(
    client_autenticado_vinculo_dre_inclusao, grupo_inclusao_alimentacao_normal
):
    assert (
        grupo_inclusao_alimentacao_normal.status
        == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal.uuid}/{DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_nao_valida' isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_inclusao_normal_codae_autoriza(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validado,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validado.uuid}/"
        + f"{CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO


def test_url_endpoint_inclusao_normal_codae_autoriza_erro(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/"
        + f"{CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_autoriza_questionamento' isn't available from "
        + "state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_normal_codae_nega(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validado,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validado.uuid}/"
        + f"{CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO


def test_url_endpoint_inclusao_normal_codae_nega_erro(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/"
        + f"{CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_nega_questionamento' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_normal_codae_questiona(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validado,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validado.uuid}/"
        + f"{CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO


def test_url_endpoint_inclusao_normal_codae_questiona_erro(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/"
        + f"{CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_questiona' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_normal_terc_ciencia(
    client_autenticado_vinculo_terceirizada_inclusao,
    grupo_inclusao_alimentacao_normal_codae_autorizado,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        grupo_inclusao_alimentacao_normal_codae_autorizado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_autorizado.uuid}/"
        f"{TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    )


def test_url_endpoint_inclusao_normal_relatorio(
    client_autenticado, grupo_inclusao_alimentacao_normal_codae_autorizado
):
    response = client_autenticado.get(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_autorizado.uuid}/"
        f"{constants.RELATORIO}/"
    )
    id_externo = grupo_inclusao_alimentacao_normal_codae_autorizado.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="inclusao_alimentacao_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_inclusao_normal_terc_ciencia_erro(
    client_autenticado_vinculo_terceirizada_inclusao,
    grupo_inclusao_alimentacao_normal_dre_validar,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        grupo_inclusao_alimentacao_normal_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_dre_validar.uuid}/"
        + f"{TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_normal_terc_responde_questionamento(
    client_autenticado_vinculo_terceirizada_inclusao,
    grupo_inclusao_alimentacao_normal_codae_questionado,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        grupo_inclusao_alimentacao_normal_codae_questionado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_questionado.uuid}/"
        f"{TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    response = client.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_questionado.uuid}/"
        + f"{TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_responde_questionamento' isn't available "
        + "from state 'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
    }


@freeze_time("2018-12-01")
def test_url_endpoint_inclusao_normal_escola_cancela(
    client_autenticado_vinculo_escola_inclusao,
    grupo_inclusao_alimentacao_normal_codae_autorizado,
):
    assert (
        grupo_inclusao_alimentacao_normal_codae_autorizado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    data = {
        "datas": [
            i.data.strftime("%Y-%m-%d")
            for i in grupo_inclusao_alimentacao_normal_codae_autorizado.inclusoes.all()[
                :1
            ]
        ]
    }
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    assert (
        grupo_inclusao_alimentacao_normal_codae_autorizado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    data = {
        "datas": [
            i.data.strftime("%Y-%m-%d")
            for i in grupo_inclusao_alimentacao_normal_codae_autorizado.inclusoes.all()[
                1:
            ]
        ]
    }
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/grupos-inclusao-alimentacao-normal/{grupo_inclusao_alimentacao_normal_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Solicitação já está cancelada"
    }


def test_permissoes_grupo_inclusao_continua_viewset(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_continua,
    inclusao_alimentacao_continua_outra_dre,
):
    # pode ver os dados de uma suspensão de alimentação da mesma escola
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK
    # Não pode ver dados de uma suspensão de alimentação de outra escola
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # não pode ver os dados de TODAS as suspensões de alimentação
    response = client_autenticado_vinculo_escola_inclusao.get(
        "/inclusoes-alimentacao-continua/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }
    inclusao_alimentacao_continua.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    inclusao_alimentacao_continua.save()
    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }
    # pode deletar somente se for escola e se estiver como rascunho
    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_outra_dre.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    inclusao_alimentacao_continua.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    inclusao_alimentacao_continua.save()
    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_endpoint_inclusao_continua_inicio_fluxo(
    client_autenticado_vinculo_escola_inclusao, inclusao_alimentacao_continua
):
    assert (
        inclusao_alimentacao_continua.status == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua.uuid}/{DRE_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR


def test_url_endpoint_inclusao_continua_inicio_fluxo_erro(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_continua_dre_validar,
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{DRE_INICIO_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'inicia_fluxo' isn't available from state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_continua_dre_valida(
    client_autenticado_vinculo_dre_inclusao, inclusao_alimentacao_continua_dre_validar
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO


def test_url_endpoint_inclusao_continua_dre_valida_erro(
    client_autenticado_vinculo_dre_inclusao, inclusao_alimentacao_continua
):
    assert (
        inclusao_alimentacao_continua.status == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua.uuid}/{DRE_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_valida' isn't available from state 'RASCUNHO'."
    }


def test_url_endpoint_inclusao_continua_dre_nao_valida(
    client_autenticado_vinculo_dre_inclusao, inclusao_alimentacao_continua_dre_validar
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA
    )


def test_url_endpoint_inclusao_continua_dre_nao_valida_erro(
    client_autenticado_vinculo_dre_inclusao, inclusao_alimentacao_continua_dre_validado
):
    assert (
        inclusao_alimentacao_continua_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_dre_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validado.uuid}/{DRE_NAO_VALIDA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_nao_valida' isn't available from state 'DRE_VALIDADO'."
    }


def test_url_endpoint_inclusao_continua_codae_autoriza(
    client_autenticado_vinculo_codae_inclusao,
    inclusao_alimentacao_continua_dre_validado,
):
    assert (
        inclusao_alimentacao_continua_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validado.uuid}/{CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO


def test_url_endpoint_inclusao_continua_codae_autoriza_erro(
    client_autenticado_vinculo_codae_inclusao, inclusao_alimentacao_continua_dre_validar
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{CODAE_AUTORIZA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_autoriza_questionamento' isn't available from "
        + "state 'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_continua_codae_nega(
    client_autenticado_vinculo_codae_inclusao,
    inclusao_alimentacao_continua_dre_validado,
):
    assert (
        inclusao_alimentacao_continua_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validado.uuid}/{CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO


def test_url_endpoint_inclusao_continua_codae_nega_erro(
    client_autenticado_vinculo_codae_inclusao, inclusao_alimentacao_continua_dre_validar
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{CODAE_NEGA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_nega_questionamento' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_continua_codae_questiona(
    client_autenticado_vinculo_codae_inclusao,
    inclusao_alimentacao_continua_dre_validado,
):
    assert (
        inclusao_alimentacao_continua_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validado.uuid}/{CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO


def test_url_endpoint_inclusao_continua_codae_questiona_erro(
    client_autenticado_vinculo_codae_inclusao, inclusao_alimentacao_continua_dre_validar
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_codae_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/{CODAE_QUESTIONA_PEDIDO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_questiona' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_continua_terc_ciencia(
    client_autenticado_vinculo_terceirizada_inclusao,
    inclusao_alimentacao_continua_codae_autorizado,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        inclusao_alimentacao_continua_codae_autorizado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    response = client.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA
    )


def test_url_endpoint_inclusao_continua_terc_ciencia_erro(
    client_autenticado_vinculo_terceirizada_inclusao,
    inclusao_alimentacao_continua_dre_validar,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_dre_validar.uuid}/"
        + f"{TERCEIRIZADA_TOMOU_CIENCIA}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_toma_ciencia' isn't available from state "
        + "'DRE_A_VALIDAR'."
    }


def test_url_endpoint_inclusao_continua_terc_responde_questionamento(
    client_autenticado_vinculo_terceirizada_inclusao,
    inclusao_alimentacao_continua_codae_questionado,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    assert (
        inclusao_alimentacao_continua_codae_questionado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    )
    response = client.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_questionado.uuid}/"
        f"{TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["status"]
        == PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )
    response = client.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_questionado.uuid}/"
        f"{TERCEIRIZADA_RESPONDE_QUESTIONAMENTO}/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'terceirizada_responde_questionamento' isn't available "
        + "from state 'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO'."
    }


@freeze_time("2018-12-01")
def test_url_endpoint_inclusao_continua_escola_cancela(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_continua_codae_autorizado,
):
    assert (
        inclusao_alimentacao_continua_codae_autorizado.status
        == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    )
    data = {
        "justificativa": "cancelando parcialmente",
        "quantidades_periodo": [
            {"uuid": "6337d4a4-f2e0-475f-9400-24f2db660741", "cancelado": True},
            {"uuid": "6f16b41d-151e-4f82-a0d0-43921a9edabe", "cancelado": False},
        ],
    }
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    qtd_prd = next(
        qtd_prd
        for qtd_prd in response.json()["quantidades_periodo"]
        if qtd_prd["uuid"] == "6337d4a4-f2e0-475f-9400-24f2db660741"
    )
    assert qtd_prd["cancelado_justificativa"] == "cancelando parcialmente"
    assert qtd_prd["cancelado"] is True

    data["quantidades_periodo"][1]["cancelado"] = True
    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU

    response = client_autenticado_vinculo_escola_inclusao.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{ESCOLA_CANCELA}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Solicitação já está cancelada"
    }


def test_url_endpoint_inclusao_continua_minhas_solicitacoes(
    client_autenticado_vinculo_escola_inclusao, inclusao_alimentacao_continua
):
    assert (
        inclusao_alimentacao_continua.status == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    )
    inclusao_alimentacao_continua.criado_por = Usuario.objects.get(
        id=client_autenticado_vinculo_escola_inclusao.session["_auth_user_id"]
    )
    inclusao_alimentacao_continua.save()
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/inclusoes-alimentacao-continua/{SOLICITACOES_DO_USUARIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@freeze_time("2019-9-30")
def test_url_endpoint_inclusao_continua_solicitacoes_codae(
    client_autenticado_vinculo_codae_inclusao,
    inclusao_alimentacao_continua_dre_validado,
    escola,
):
    assert (
        inclusao_alimentacao_continua_dre_validado.status
        == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusoes-alimentacao-continua/{constants.PEDIDOS_CODAE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={escola.lote.uuid}&diretoria_regional={escola.diretoria_regional.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@freeze_time("2019-9-30")
def test_url_endpoint_inclusao_continua_solicitacoes_dre(
    client_autenticado_vinculo_dre_inclusao,
    inclusao_alimentacao_continua_dre_validar,
    escola,
):
    assert (
        inclusao_alimentacao_continua_dre_validar.status
        == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusoes-alimentacao-continua/{constants.PEDIDOS_DRE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={escola.lote.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_endpoint_inclusao_continua_marca_conferencia(
    client_autenticado_vinculo_terceirizada_inclusao,
    inclusao_alimentacao_continua_codae_autorizado,
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao

    response = client.patch(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{constants.MARCAR_CONFERIDA}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["terceirizada_conferiu_gestao"] is True


def test_url_endpoint_inclusao_continua_relatorio(
    client_autenticado, inclusao_alimentacao_continua_codae_autorizado
):
    response = client_autenticado.get(
        f"/inclusoes-alimentacao-continua/{inclusao_alimentacao_continua_codae_autorizado.uuid}/"
        f"{constants.RELATORIO}/"
    )
    id_externo = inclusao_alimentacao_continua_codae_autorizado.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="inclusao_alimentacao_continua_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_endpoint_inclusao_cei_relatorio(
    client_autenticado_vinculo_escola_cei_inclusao,
    escola_periodo_escolar_cei,
    escola_cei,
    periodo_escolar,
):
    inclusao_alimentacao = baker.make(
        InclusaoAlimentacaoDaCEI,
        rastro_escola=escola_cei,
        periodo_escolar=periodo_escolar,
    )
    response = client_autenticado_vinculo_escola_cei_inclusao.get(
        f"/inclusoes-alimentacao-da-cei/{inclusao_alimentacao.uuid}/{constants.RELATORIO}/"
    )
    id_externo = inclusao_alimentacao.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="inclusao_alimentacao_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


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


def test_terceirizada_marca_conferencia_grupo_inclusao_normal_viewset(
    client_autenticado, grupo_inclusao_alimentacao_normal
):
    checa_se_terceirizada_marcou_conferencia_na_gestao_de_alimentacao(
        client_autenticado,
        GrupoInclusaoAlimentacaoNormal,
        "grupos-inclusao-alimentacao-normal",
    )


def test_url_endpoint_inclusao_cemei(
    client_autenticado_vinculo_escola_inclusao,
    tipo_alimentacao_refeicao,
):
    data = {
        "escola": "230453bb-d6f1-4513-b638-8d6d150d1ac6",
        "dias_motivos_da_inclusao_cemei": [
            {"data": "2022-01-02", "motivo": "803f0508-2abd-4874-ad05-95a4fb29947e"}
        ],
        "quantidade_alunos_cei_da_inclusao_cemei": [
            {
                "periodo_escolar": "208f7cb4-b03a-4357-ab6d-bda078a37748",
                "quantidade_alunos": 40,
                "matriculados_quando_criado": 666,
                "faixa_etaria": "ee77f350-6af8-4928-86d6-684fbf423ff5",
            }
        ],
        "quantidade_alunos_emei_da_inclusao_cemei": [
            {
                "periodo_escolar": "208f7cb4-b03a-4357-ab6d-bda078a37748",
                "quantidade_alunos": 30,
                "matriculados_quando_criado": 46,
                "tipos_alimentacao": [tipo_alimentacao_refeicao.uuid],
            }
        ],
    }
    response = client_autenticado_vinculo_escola_inclusao.post(
        "/inclusao-alimentacao-cemei/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["criado_por"] is not None
    assert len(response_json["dias_motivos_da_inclusao_cemei"]) == 1
    assert len(response_json["quantidade_alunos_cei_da_inclusao_cemei"]) == 1
    assert len(response_json["quantidade_alunos_emei_da_inclusao_cemei"]) == 1

    response = client_autenticado_vinculo_escola_inclusao.get(
        f'/inclusao-alimentacao-cemei/{response_json["uuid"]}/'
    )
    assert response.status_code == status.HTTP_200_OK

    data["dias_motivos_da_inclusao_cemei"] = [
        {"data": "2022-01-02", "motivo": "803f0508-2abd-4874-ad05-95a4fb29947e"},
        {"data": "2022-01-03", "motivo": "803f0508-2abd-4874-ad05-95a4fb29947e"},
        {"data": "2022-01-04", "motivo": "803f0508-2abd-4874-ad05-95a4fb29947e"},
    ]
    del data["quantidade_alunos_cei_da_inclusao_cemei"]

    response = client_autenticado_vinculo_escola_inclusao.patch(
        f'/inclusao-alimentacao-cemei/{response_json["uuid"]}/',
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json["dias_motivos_da_inclusao_cemei"]) == 3
    assert len(response_json["quantidade_alunos_cei_da_inclusao_cemei"]) == 0
    assert len(response_json["quantidade_alunos_emei_da_inclusao_cemei"]) == 1

    response = client_autenticado_vinculo_escola_inclusao.get(
        f'/inclusao-alimentacao-cemei/{response_json["uuid"]}/',
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "logs" in response.json()


def test_url_endpoint_inclusao_cemei_get_permissoes(
    client_autenticado_vinculo_escola_inclusao,
    client_autenticado_vinculo_escola_cei_inclusao,
):
    data = {
        "escola": "230453bb-d6f1-4513-b638-8d6d150d1ac6",
        "dias_motivos_da_inclusao_cemei": [
            {"data": "2022-01-02", "motivo": "803f0508-2abd-4874-ad05-95a4fb29947e"}
        ],
        "quantidade_alunos_cei_da_inclusao_cemei": [
            {
                "periodo_escolar": "208f7cb4-b03a-4357-ab6d-bda078a37748",
                "quantidade_alunos": 40,
                "matriculados_quando_criado": 666,
                "faixa_etaria": "ee77f350-6af8-4928-86d6-684fbf423ff5",
            }
        ],
        "quantidade_alunos_emei_da_inclusao_cemei": [
            {
                "periodo_escolar": "208f7cb4-b03a-4357-ab6d-bda078a37748",
                "quantidade_alunos": 30,
                "matriculados_quando_criado": 46,
            }
        ],
    }
    response = client_autenticado_vinculo_escola_inclusao.post(
        "/inclusao-alimentacao-cemei/", content_type="application/json", data=data
    )
    response = client_autenticado_vinculo_escola_cei_inclusao.get(
        "/inclusao-alimentacao-cemei/", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    # só pode ver inclusoes da sua escola
    assert len(response.json()["results"]) == 0


def test_url_inclusao_cemei_delete(
    client_autenticado_vinculo_escola_inclusao, inclusao_alimentacao_cemei
):
    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusao-alimentacao-cemei/{inclusao_alimentacao_cemei.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_url_inclusao_cemei_delete_403(
    client_autenticado_vinculo_escola_inclusao, inclusao_alimentacao_cemei
):
    inclusao_alimentacao_cemei.status = (
        InclusaoDeAlimentacaoCEMEI.workflow_class.DRE_A_VALIDAR
    )
    inclusao_alimentacao_cemei.save()
    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusao-alimentacao-cemei/{inclusao_alimentacao_cemei.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }


def test_url_inclusao_cemei_dre(
    client_autenticado_vinculo_dre_inclusao, inclusao_alimentacao_cemei, escola
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        "/inclusao-alimentacao-cemei/", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    # só pode ver inclusoes da sua DRE
    assert len(response.json()["results"]) == 1

    response = client_autenticado_vinculo_dre_inclusao.get(
        "/inclusao-alimentacao-cemei/?status=DRE_A_VALIDAR",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0

    inclusao_alimentacao_cemei.status = (
        InclusaoDeAlimentacaoCEMEI.workflow_class.DRE_A_VALIDAR
    )
    inclusao_alimentacao_cemei.save()
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao-cemei/{PEDIDOS_DRE}/{SEM_FILTRO}/?lote={escola.lote.uuid}"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusao_cemei_codae(
    client_autenticado_vinculo_codae_inclusao, inclusao_alimentacao_cemei, escola
):
    inclusao_alimentacao_cemei.status = (
        InclusaoDeAlimentacaoCEMEI.workflow_class.DRE_VALIDADO
    )
    inclusao_alimentacao_cemei.save()
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusao-alimentacao-cemei/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
        f"?lote={escola.lote.uuid}&diretoria_regional={escola.diretoria_regional.uuid}"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusao_cemei_terceirizada(
    client_autenticado_vinculo_terceirizada_inclusao, inclusao_alimentacao_cemei
):
    client, user = client_autenticado_vinculo_terceirizada_inclusao
    response = client.get(
        "/inclusao-alimentacao-cemei/", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    # só pode ver inclusoes da sua TERCEIRIZADA
    assert len(response.json()["results"]) == 1


def test_url_endpoint_inclusao_cemei_relatorio(
    client_autenticado_vinculo_escola_inclusao, inclusao_alimentacao_cemei
):
    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/inclusao-alimentacao-cemei/{inclusao_alimentacao_cemei.uuid}/{constants.RELATORIO}/"
    )
    id_externo = inclusao_alimentacao_cemei.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="inclusao_alimentacao_cemei_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_url_grupos_inclusao_alimentacao_normal_codae_sem_paginacao(
    client_autenticado_vinculo_codae_inclusao, escola
):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusoes_alimentacao_continua_codae_sem_paginacao(
    client_autenticado_vinculo_codae_inclusao, escola
):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusoes-alimentacao-continua/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusoes_alimentacao_da_cei_codae_sem_paginacao(
    client_autenticado_vinculo_codae_inclusao, escola
):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusoes-alimentacao-da-cei/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusao_alimentacao_cemei_codae_sem_paginacao(
    client_autenticado_vinculo_codae_inclusao, escola
):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusao-alimentacao-cemei/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_grupos_inclusao_alimentacao_normal_dre_sem_paginacao(
    client_autenticado_vinculo_dre_inclusao, escola
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusoes_alimentacao_continua_dre_sem_paginacao(
    client_autenticado_vinculo_dre_inclusao, escola
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusoes-alimentacao-continua/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusoes_alimentacao_da_cei_dre_sem_paginacao(
    client_autenticado_vinculo_dre_inclusao, escola
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusoes-alimentacao-da-cei/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_inclusao_alimentacao_cemei_dre_sem_paginacao(
    client_autenticado_vinculo_dre_inclusao, escola
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao-cemei/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)
