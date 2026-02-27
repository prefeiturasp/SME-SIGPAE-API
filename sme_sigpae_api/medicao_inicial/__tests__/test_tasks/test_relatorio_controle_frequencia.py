import pytest
from unittest.mock import Mock, patch

from sme_sigpae_api.medicao_inicial.tasks import (
    exporta_relatorio_controle_frequencia_para_pdf,
)

pytestmark = pytest.mark.django_db


class TestExportaRelatorioControleFrequenciaParaPDF:

    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_relatorio_controle_frequencia_pdf")
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    def test_exporta_relatorio_sucesso(
        self,
        mock_gera_objeto,
        mock_gera_pdf,
        mock_atualiza,
        mock_logger,
    ):
        mock_obj = Mock()
        mock_gera_objeto.return_value = mock_obj
        mock_gera_pdf.return_value = b"%PDF fake content"

        query_params = {"mes_ano": "02_2026"}
        escola_uuid = "uuid-escola-teste"

        exporta_relatorio_controle_frequencia_para_pdf(
            "user_teste",
            "arquivo.pdf",
            query_params,
            escola_uuid,
        )

        mock_gera_pdf.assert_called_once_with(query_params, escola_uuid)
        mock_atualiza.assert_called_once_with(
            mock_obj,
            "arquivo.pdf",
            b"%PDF fake content",
        )

        assert mock_logger.call_count >= 2


    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download_com_erro")
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_relatorio_controle_frequencia_pdf")
    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    def test_exporta_relatorio_com_erro(
        self,
        mock_gera_objeto,
        mock_gera_pdf,
        mock_atualiza_erro,
        mock_logger,
    ):
        mock_obj = Mock()
        mock_gera_objeto.return_value = mock_obj
        mock_gera_pdf.side_effect = Exception("Erro ao gerar PDF")

        query_params = {"mes_ano": "02_2026"}
        escola_uuid = "uuid-escola-teste"

        exporta_relatorio_controle_frequencia_para_pdf(
            "user_teste",
            "arquivo.pdf",
            query_params,
            escola_uuid,
        )

        mock_atualiza_erro.assert_called_once()
        args = mock_atualiza_erro.call_args[0]

        assert args[0] == mock_obj
        assert "Erro ao gerar PDF" in args[1]
