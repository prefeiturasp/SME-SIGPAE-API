import datetime

import pytest
from faker import Faker
from model_bakery import baker
from rest_framework import status
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.django_db

fake = Faker("pt_BR")
Faker.seed(420)


def test_consultar_dados_aluno(client_autenticado, aluno, escola):
    response = client_autenticado.get(f"/dados-alunos-eol/{aluno.codigo_eol}/")
    assert response.status_code == status.HTTP_200_OK


class TestDadosUsuarioEOLCompletoViewSet:
    @patch('sme_sigpae_api.eol_servico.api.viewsets.UsuarioDetalheSerializer')
    @patch('sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario')
    def test_retrieve_usuario_sucesso_mesma_ue(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_dre
    ):
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = mock_eol_response_success
        mock_get_dados_usuario.return_value = mock_response

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = mock_serializer_usuario_dre
        mock_serializer_class.return_value = mock_serializer_instance

        registro_funcional = "9876543"
        response = client_autenticado_da_escola.get(
            f"/dados-usuario-eol-completo/{registro_funcional}/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["nome"] == "João da Silva"


    @patch('sme_sigpae_api.eol_servico.api.viewsets.UsuarioDetalheSerializer')
    @patch('sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario')
    def test_retrieve_usuario_dre_diferente_forbidden(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_dre
    ):
        mock_eol_response_success["cargos"][0]["codigoUnidade"] = "999999"

        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = mock_eol_response_success
        mock_get_dados_usuario.return_value = mock_response

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = mock_serializer_usuario_dre
        mock_serializer_class.return_value = mock_serializer_instance

        registro_funcional = "9876543"
        response = client_autenticado_da_escola.get(
            f"/dados-usuario-eol-completo/{registro_funcional}/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "RF não pertence a uma unidade de sua DRE"


    @patch('sme_sigpae_api.eol_servico.api.viewsets.UsuarioDetalheSerializer')
    @patch('sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario')
    def test_retrieve_usuario_ue_diferente_forbidden(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_diretor_ue
    ):
        mock_eol_response_success["cargos"][0]["codigoUnidade"] = "999999"

        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = mock_eol_response_success
        mock_get_dados_usuario.return_value = mock_response

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = mock_serializer_usuario_diretor_ue
        mock_serializer_class.return_value = mock_serializer_instance

        registro_funcional = "9876543"
        response = client_autenticado_da_escola.get(
            f"/dados-usuario-eol-completo/{registro_funcional}/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "RF não pertence à Unidade Educacional"

    @patch('sme_sigpae_api.eol_servico.api.viewsets.UsuarioDetalheSerializer')
    @patch('sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario')
    def test_retrieve_usuario_nao_encontrado(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_serializer_usuario_codae
    ):
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_get_dados_usuario.return_value = mock_response

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = mock_serializer_usuario_codae
        mock_serializer_class.return_value = mock_serializer_instance

        registro_funcional = "0000000"
        response = client_autenticado_da_escola.get(
            f"/dados-usuario-eol-completo/{registro_funcional}/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Usuário não encontrado" in response.data["detail"]
