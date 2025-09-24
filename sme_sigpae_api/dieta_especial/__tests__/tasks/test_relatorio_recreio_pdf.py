import pytest
from freezegun.api import freeze_time
from pdfminer.high_level import extract_text

from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.dieta_especial.tasks import (
    gera_pdf_relatorio_recreio_nas_ferias_async,
)

from .test_setup_relatorio_recreio import BaseSetupRecreioNasFerias

pytestmark = pytest.mark.django_db


def resgata_conteudo_pdf():
    central_download = CentralDeDownload.objects.get()
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    return extract_text(central_download.arquivo.path, page_numbers=[0])


@pytest.mark.usefixtures("client_autenticado_vinculo_codae_gestao_alimentacao_dieta")
@freeze_time("2025-08-25")
class TestGeraPDFRelatorioRecreioNasFeriasAsync(BaseSetupRecreioNasFerias):
    def test_gera_dicionario_relatorio_recreio(self):
        self.setup()
        solicitacoes = SolicitacaoDietaEspecial.objects.filter(
            dieta_para_recreio_ferias=True
        )
        dados = [
            {
                "codigo_eol_aluno": "1234567",
                "nome_aluno": "MARIA SILVA",
                "nome_escola": "EMEBS HELEN KELLER",
                "escola_destino": "EMEF PERICLES",
                "data_inicio": "01/08/2025",
                "data_fim": "31/08/2025",
                "classificacao": "Tipo A",
                "alergias_intolerancias": "--",
            },
            {
                "codigo_eol_aluno": "7654321",
                "nome_aluno": "JOÃO COSTA",
                "nome_escola": "EMEF PERICLES",
                "escola_destino": "EMEBS HELEN KELLER",
                "data_inicio": "01/09/2025",
                "data_fim": "29/09/2025",
                "classificacao": "Tipo B",
                "alergias_intolerancias": "--",
            },
        ]

        from sme_sigpae_api.dieta_especial.tasks.utils.relatorio_recreio_nas_ferias import (
            gera_dicionario_relatorio_recreio,
        )

        resultado = gera_dicionario_relatorio_recreio(solicitacoes)
        assert resultado == dados

    def test_gera_pdf_relatorio_recreio_nas_ferias(
        self, client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    ):
        self.setup()
        client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
        gera_pdf_relatorio_recreio_nas_ferias_async(
            user, "relatorio_recreio_nas_ferias.pdf", {"lote": self.lote.uuid}
        )
        conteudo_pdf = resgata_conteudo_pdf()

        esperados_cabecalho = [
            "Total de Dietas Autorizadas",
            "25/08/2025",
            "IP",
            "LOTE 01",
        ]

        esperados_tabela = [
            "EMEF PERICLES",
            "MARIA SILVA",
            "Tipo A",
            "01/08/2025",
            "31/08/2025",
        ]

        for texto in esperados_cabecalho:
            assert texto in conteudo_pdf, f"Texto do cabeçalho não encontrado: {texto}"

        for texto in esperados_tabela:
            assert texto in conteudo_pdf, f"Texto da tabela não encontrado: {texto}"

    def test_gera_pdf_historico_dietas_especiais_periodo_param(
        self, client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    ):
        self.setup()
        client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
        gera_pdf_relatorio_recreio_nas_ferias_async(
            user,
            "relatorio_recreio_nas_ferias.pdf",
            {"lote": self.lote.uuid, "data_inicio": "01/09/2025"},
        )
        conteudo_pdf = resgata_conteudo_pdf()
        assert "LOTE 01" in conteudo_pdf
        assert "MARIA SILVA" not in conteudo_pdf
        assert "Tipo A" not in conteudo_pdf
        assert "31/08/2025" not in conteudo_pdf
