import datetime
from unittest.mock import MagicMock, patch

import pytest
from faker import Faker
from model_bakery import baker
from rest_framework import status

pytestmark = pytest.mark.django_db

fake = Faker("pt_BR")
Faker.seed(420)


def test_consultar_dados_aluno(client_autenticado, aluno, escola):
    response = client_autenticado.get(f"/dados-alunos-eol/{aluno.codigo_eol}/")
    assert response.status_code == status.HTTP_200_OK


class TestDadosUsuarioEOLCompletoViewSet:
    @patch("src.eol_servico.api.viewsets.UsuarioDetalheSerializer")
    @patch("src.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
    def test_retrieve_usuario_sucesso_mesma_ue(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_dre,
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

    @patch("src.eol_servico.api.viewsets.UsuarioDetalheSerializer")
    @patch("src.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
    def test_retrieve_usuario_dre_diferente_forbidden(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_dre,
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

    @patch("src.eol_servico.api.viewsets.UsuarioDetalheSerializer")
    @patch("src.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
    def test_retrieve_usuario_ue_diferente_forbidden(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_eol_response_success,
        mock_serializer_usuario_diretor_ue,
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

    @patch("src.eol_servico.api.viewsets.UsuarioDetalheSerializer")
    @patch("src.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
    def test_retrieve_usuario_nao_encontrado(
        self,
        mock_get_dados_usuario,
        mock_serializer_class,
        client_autenticado_da_escola,
        mock_serializer_usuario_codae,
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


class TestDadosServidorEOLViewSet:
    URL = "/dados-servidor-eol/{}/"
    PATCH_RF = "src.eol_servico.utils.EOLServicoSGP.get_dados_usuario"

    @staticmethod
    def _resposta(status_code=200, json_data=None):
        resposta = MagicMock()
        resposta.status_code = status_code
        resposta.json.return_value = json_data
        return resposta

    def test_encontrado(self, client_autenticado):
        with patch(
            self.PATCH_RF, return_value=self._resposta(200, {"nome": " FULANO "})
        ):
            response = client_autenticado.get(self.URL.format("1234567"))

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"rf": "1234567", "nome": "FULANO"}

    @pytest.mark.parametrize(
        "status_code,json_data",
        [(404, None), (400, None), (204, None), (200, {"nome": ""}), (200, {})],
    )
    def test_nao_encontrado(self, client_autenticado, status_code, json_data):
        with patch(self.PATCH_RF, return_value=self._resposta(status_code, json_data)):
            response = client_autenticado.get(self.URL.format("1234567"))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "RF não localizado. Verifique o número informado."
        }

    @pytest.mark.parametrize("rf", ["12a4567", "abc", "12 34", "²³"])
    def test_rf_invalido(self, client_autenticado, rf):
        with patch(self.PATCH_RF) as mock_consulta:
            response = client_autenticado.get(self.URL.format(rf))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_consulta.assert_not_called()

    @pytest.mark.parametrize(
        "mock_kwargs",
        [
            {"side_effect": ConnectionError("fora do ar")},
            {"return_value": MagicMock(status_code=500)},
            {
                "return_value": MagicMock(
                    status_code=200, json=MagicMock(side_effect=ValueError)
                )
            },
        ],
    )
    def test_servico_indisponivel(self, client_autenticado, mock_kwargs):
        with patch(self.PATCH_RF, **mock_kwargs):
            response = client_autenticado.get(self.URL.format("1234567"))

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "detail" in response.json()

    def test_nao_autenticado(self, client):
        with patch(self.PATCH_RF) as mock_consulta:
            response = client.get(self.URL.format("1234567"))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_consulta.assert_not_called()
