from unittest import TestCase
from unittest.mock import MagicMock, patch

from sme_sigpae_api.paineis_consolidados.api.serializers import (
    SolicitacoesExportXLSXSerializer,
)


class TestSolicitacoesExportXLSXSerializer(TestCase):
    def setUp(self):
        self.serializer = SolicitacoesExportXLSXSerializer()
        self.mock_obj = MagicMock()
        self.mock_model_obj = MagicMock()

    @patch("sme_sigpae_api.paineis_consolidados.api.serializers.get_dias_inclusao")
    def test_observacoes_cancelado(self, mock_get_dias_inclusao):
        self.mock_obj.tipo_doc = "INC_ALIMENTA"
        self.mock_obj.get_raw_model.objects.get.return_value = self.mock_model_obj
        self.mock_obj.uuid = "2936a934-a3fd-442e-9f0c-75309748a1bc"

        dias_mock = [MagicMock(cancelado=False), MagicMock(cancelado=False)]
        mock_get_dias_inclusao.return_value = dias_mock
        self.mock_model_obj.status = "ESCOLA_CANCELOU"
        result = self.serializer.get_observacoes(self.mock_obj)
        self.assertEqual(result, "cancelado, cancelado")

    @patch("sme_sigpae_api.paineis_consolidados.api.serializers.get_dias_inclusao")
    def test_observacoes_misto(self, mock_get_dias_inclusao):
        self.mock_obj.tipo_doc = "ALT_CARDAPIO"
        self.mock_obj.get_raw_model.objects.get.return_value = self.mock_model_obj
        self.mock_obj.uuid = "2936a934-a3fd-442e-9f0c-75309748a1bc"

        dias_mock = [
            MagicMock(cancelado=True),
            MagicMock(cancelado=False),
            MagicMock(cancelado=True),
        ]
        mock_get_dias_inclusao.return_value = dias_mock
        self.mock_model_obj.existe_dia_cancelado = True
        result = self.serializer.get_observacoes(self.mock_obj)
        self.assertEqual(result, "cancelado, autorizado, cancelado")

    def test_observacoes_observacao(self):
        self.mock_obj.get_raw_model.objects.get.return_value = self.mock_model_obj
        self.mock_obj.uuid = "2936a934-a3fd-442e-9f0c-75309748a1bc"
        self.mock_model_obj.observacao = "<p>Teste de observação</p>"

        with patch(
            "sme_sigpae_api.paineis_consolidados.api.serializers.remove_tags_html_from_string",
            return_value="Teste de observação limpa",
        ):
            result = self.serializer.get_observacoes(self.mock_obj)
        self.assertEqual(result, "Teste de observação limpa")

    def test_observacoes_observacoes(self):
        self.mock_obj.get_raw_model.objects.get.return_value = self.mock_model_obj
        self.mock_obj.uuid = "2936a934-a3fd-442e-9f0c-75309748a1bc"
        self.mock_model_obj.observacoes = "<p>Outra observação</p>"

        with patch(
            "sme_sigpae_api.paineis_consolidados.api.serializers.remove_tags_html_from_string",
            return_value="Outra observação limpa",
        ):
            result = self.serializer.get_observacoes(self.mock_obj)
        self.assertEqual(result, "Outra observação limpa")
