"""Testes para geração de relatório de medição considerando histórico de escolas."""

import datetime
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    HistoricoEscolaFactory,
    LoteFactory,
    TipoGestaoFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    SolicitacaoMedicaoInicialFactory,
)
from sme_sigpae_api.medicao_inicial.tasks import (
    gera_pdf_relatorio_solicitacao_medicao_por_escola_async,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


@freeze_time("2026-01-15")
class TestGeraRelatorioMedicaoComHistoricoEscola:
    """Testes para verificar se o relatório é gerado com o tipo correto baseado no histórico."""

    def setup_tipos_unidade(self):
        """Cria e retorna os tipos de unidade EMEI e CEMEI."""
        tipo_unidade_emei = TipoUnidadeEscolarFactory.create(iniciais="EMEI")
        tipo_unidade_cemei = TipoUnidadeEscolarFactory.create(iniciais="CEMEI")
        return tipo_unidade_emei, tipo_unidade_cemei

    def setup_escola_que_mudou_de_tipo(self):
        """
        Cria uma escola que era EMEI até 31/12/2025 e se tornou CEMEI a partir de 01/01/2026.
        """
        tipo_unidade_emei, tipo_unidade_cemei = self.setup_tipos_unidade()

        terceirizada = EmpresaFactory.create()
        diretoria_regional = DiretoriaRegionalFactory.create(
            nome="DIRETORIA REGIONAL TESTE"
        )
        lote = LoteFactory.create(
            terceirizada=terceirizada,
            diretoria_regional=diretoria_regional,
        )
        tipo_gestao = TipoGestaoFactory.create(nome="TERC TOTAL")

        # Escola atual é CEMEI
        escola = EscolaFactory.create(
            nome="ESCOLA TESTE QUE MUDOU DE TIPO",
            lote=lote,
            diretoria_regional=diretoria_regional,
            tipo_gestao=tipo_gestao,
            tipo_unidade=tipo_unidade_cemei,
            codigo_eol="999888",
        )

        # Cria histórico mostrando que era EMEI até 31/12/2025
        HistoricoEscolaFactory.create(
            escola=escola,
            nome="ESCOLA TESTE QUANDO ERA EMEI",
            tipo_unidade=tipo_unidade_emei,
            data_inicial=datetime.date(2020, 1, 1),
            data_final=datetime.date(2025, 12, 31),
        )

        return escola, tipo_unidade_emei, tipo_unidade_cemei

    def setup_solicitacoes(self, escola):
        """Cria solicitações de medição para dezembro/2025 e janeiro/2026."""
        solicitacao_dezembro = SolicitacaoMedicaoInicialFactory.create(
            escola=escola,
            mes="12",
            ano=2025,
        )
        solicitacao_janeiro = SolicitacaoMedicaoInicialFactory.create(
            escola=escola,
            mes="01",
            ano=2026,
        )
        return solicitacao_dezembro, solicitacao_janeiro

    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola"
    )
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola_cemei"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    def test_gera_relatorio_escola_era_emei_em_dezembro_2025(
        self,
        mock_logger_info,
        mock_relatorio_cemei,
        mock_relatorio_emef,
        mock_atualiza,
        mock_gera_objeto,
    ):
        """
        Testa que para uma solicitação de dezembro/2025, quando a escola era EMEI,
        o relatório gerado deve ser do tipo EMEF/EMEI (não CEI/CEMEI).
        """

        escola, tipo_emei, tipo_cemei = self.setup_escola_que_mudou_de_tipo()
        solicitacao_dezembro, _ = self.setup_solicitacoes(escola)

        mock_gera_objeto.return_value = Mock()
        mock_relatorio_emef.return_value = b"<html>RELATORIO EMEF</html>"
        nome_arquivo = "relatorio_dez_2025.pdf"

        gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
            "user", nome_arquivo, str(solicitacao_dezembro.uuid)
        )

        # Assert - Verifica que chamou o relatório correto (não CEI/CEMEI)
        # Para dezembro/2025, escola era EMEI, então deve usar relatorio_solicitacao_medicao_por_escola
        assert mock_relatorio_emef.called
        assert not mock_relatorio_cemei.called

        # Verifica que a escola é reconhecida como EMEI na data
        data_referencia = solicitacao_dezembro.data_referencia
        assert escola.eh_emei_data(data_referencia)
        assert not escola.eh_cemei_data(data_referencia)
        assert not escola.eh_cei_data(data_referencia)

    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola"
    )
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola_cemei"
    )
    @patch("sme_sigpae_api.medicao_inicial.tasks.logger.info")
    def test_gera_relatorio_escola_eh_cemei_em_janeiro_2026(
        self,
        mock_logger_info,
        mock_relatorio_cemei,
        mock_relatorio_emef,
        mock_atualiza,
        mock_gera_objeto,
    ):
        """
        Testa que para uma solicitação de janeiro/2026, quando a escola já é CEMEI,
        o relatório gerado deve ser do tipo CEMEI.
        """
        escola, tipo_emei, tipo_cemei = self.setup_escola_que_mudou_de_tipo()
        _, solicitacao_janeiro = self.setup_solicitacoes(escola)

        mock_gera_objeto.return_value = Mock()
        mock_relatorio_cemei.return_value = b"<html>RELATORIO CEMEI</html>"
        nome_arquivo = "relatorio_jan_2026.pdf"

        gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
            "user", nome_arquivo, str(solicitacao_janeiro.uuid)
        )

        # Assert - Verifica que chamou o relatório correto (CEMEI)
        # Para janeiro/2026, escola já é CEMEI
        assert mock_relatorio_cemei.called
        assert not mock_relatorio_emef.called

        # Verifica que a escola é reconhecida como CEMEI na data
        data_referencia = solicitacao_janeiro.data_referencia
        assert escola.eh_cemei_data(data_referencia)
        assert not escola.eh_emei_data(data_referencia)
        assert not escola.eh_cei_data(data_referencia)

    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola"
    )
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola_cemei"
    )
    def test_conteudo_html_dezembro_2025_tem_caracteristicas_emei(
        self,
        mock_relatorio_cemei,
        mock_relatorio_emef,
        mock_atualiza,
        mock_gera_objeto,
    ):
        """
        Testa que o conteúdo HTML gerado para dezembro/2025 contém características
        de relatório EMEI/EMEF (não CEI/CEMEI).
        """

        escola, _, _ = self.setup_escola_que_mudou_de_tipo()
        solicitacao_dezembro, _ = self.setup_solicitacoes(escola)

        mock_gera_objeto.return_value = Mock()
        html_content = b"<html><body><h1>Relatorio EMEF</h1><p>Periodo Escolar: MANHA</p></body></html>"
        mock_relatorio_emef.return_value = html_content

        gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
            "user",
            "relatorio_test.pdf",
            str(solicitacao_dezembro.uuid),
        )

        mock_relatorio_emef.assert_called_once_with(solicitacao_dezembro)

        # Verifica que o conteúdo passado para atualização contém características de EMEF
        call_args = mock_atualiza.call_args
        assert call_args is not None
        arquivo_gerado = call_args[0][2]  # terceiro argumento é o arquivo
        assert arquivo_gerado == html_content

    @patch("sme_sigpae_api.medicao_inicial.tasks.gera_objeto_na_central_download")
    @patch("sme_sigpae_api.medicao_inicial.tasks.atualiza_central_download")
    @patch(
        "sme_sigpae_api.medicao_inicial.tasks.relatorio_solicitacao_medicao_por_escola_cemei"
    )
    def test_conteudo_html_janeiro_2026_tem_caracteristicas_cemei(
        self,
        mock_relatorio_cemei,
        mock_atualiza,
        mock_gera_objeto,
    ):
        """
        Testa que o conteúdo HTML gerado para janeiro/2026 contém características
        de relatório CEMEI.
        """

        escola, _, _ = self.setup_escola_que_mudou_de_tipo()
        _, solicitacao_janeiro = self.setup_solicitacoes(escola)

        mock_gera_objeto.return_value = Mock()
        html_content = b"<html><body><h1>Relatorio CEMEI</h1><p>Infantil INTEGRAL</p><p>Faixa Etaria</p></body></html>"
        mock_relatorio_cemei.return_value = html_content

        gera_pdf_relatorio_solicitacao_medicao_por_escola_async(
            "user",
            "relatorio_test.pdf",
            str(solicitacao_janeiro.uuid),
        )

        mock_relatorio_cemei.assert_called_once_with(solicitacao_janeiro)

        # Verifica que o conteúdo passado para atualização contém características de CEMEI
        call_args = mock_atualiza.call_args
        assert call_args is not None
        arquivo_gerado = call_args[0][2]  # terceiro argumento é o arquivo
        assert arquivo_gerado == html_content

    def test_data_referencia_dezembro_2025(self):
        """Verifica que a data de referência é calculada corretamente para dezembro/2025."""
        escola, _, _ = self.setup_escola_que_mudou_de_tipo()
        solicitacao_dezembro, _ = self.setup_solicitacoes(escola)

        data_referencia = solicitacao_dezembro.data_referencia
        assert data_referencia == datetime.date(2025, 12, 1)

    def test_data_referencia_janeiro_2026(self):
        """Verifica que a data de referência é calculada corretamente para janeiro/2026."""
        escola, _, _ = self.setup_escola_que_mudou_de_tipo()
        _, solicitacao_janeiro = self.setup_solicitacoes(escola)

        data_referencia = solicitacao_janeiro.data_referencia
        assert data_referencia == datetime.date(2026, 1, 1)

    def test_historico_escola_configurado_corretamente(self):
        """Verifica que o histórico da escola está configurado corretamente."""
        escola, tipo_emei, _ = self.setup_escola_que_mudou_de_tipo()

        # Verifica que existe histórico
        assert escola.historicos_escola.exists()

        # Verifica dados do histórico
        historico = escola.historicos_escola.first()
        assert historico.tipo_unidade == tipo_emei
        assert historico.data_inicial == datetime.date(2020, 1, 1)
        assert historico.data_final == datetime.date(2025, 12, 31)
        assert "EMEI" in historico.nome

    def test_tipo_atual_escola_eh_cemei(self):
        """Verifica que o tipo atual da escola é CEMEI."""
        escola, _, tipo_cemei = self.setup_escola_que_mudou_de_tipo()

        assert escola.tipo_unidade == tipo_cemei
        assert escola.eh_cemei
