import json

import pytest
from freezegun.api import freeze_time
from openpyxl import load_workbook
from PyPDF4 import PdfFileReader

from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.dieta_especial.tasks import (
    gera_pdf_relatorio_historico_dietas_especiais_async,
)

from .test_setup_relatorio_historico import BaseSetupHistoricoDietas

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_vinculo_codae_gestao_alimentacao_dieta")
@freeze_time("2025-05-09")
class TestGeraPDFRelatorioHistoricoDietasEspeciaisAsync(BaseSetupHistoricoDietas):
    def setup(self):
        self.setup_generico()
        self.setup_classificacoes_dieta()
        self.setup_escola_emef()
        self.setup_logs_escola_emef()
        self.setup_faixas_etarias()
        self.setup_escola_cei()
        self.setup_logs_escola_cei()
        self.setup_escola_ceu_gestao()
        self.setup_logs_escola_ceu_gestao()
        self.setup_escola_emebs()
        self.setup_logs_escola_emebs()
        self.setup_escola_cemei()
        self.setup_logs_escola_cemei_cei()
        self.setup_logs_escola_cemei_emei()

    def test_gera_pdf_historico_dietas_especiais(
        self, client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    ):
        self.setup()
        client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
        nome_arquivo = "relatorio_historico_dietas_especiais.pdf"
        data = json.dumps({"lote": str(self.lote.uuid), "data": "09/05/2025"})
        gera_pdf_relatorio_historico_dietas_especiais_async(user, nome_arquivo, data)

        central_download = CentralDeDownload.objects.get()
        assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO

        reader = PdfFileReader(central_download.arquivo.path)
        page = reader.pages[0]
        conteudo_pdf_pagina_1 = page.extractText()

        esperados_cabecalho = [
            "Total de Dietas Autorizadas em",
            "09/05/2025",
            "para as unidades da DRE",
            "IPIRANGA",
            "LOTE 01",
            "Manhã",
            "Integral",
            "Tarde",
            "120",
        ]

        esperados_tabela = [
            "IP - LOTE",
            "EMEBS HELEN",
            "KELLER",
            "Alunos do Infantil (4 a 6 anos)",
        ]

        for texto in esperados_cabecalho:
            assert (
                texto in conteudo_pdf_pagina_1
            ), f"Texto do cabeçalho não encontrado: {texto}"

        for texto in esperados_tabela:
            assert (
                texto in conteudo_pdf_pagina_1
            ), f"Texto da tabela não encontrado: {texto}"

    def test_gera_pdf_historico_dietas_especiais_periodo_param(
        self, client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    ):
        self.setup()
        client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
        nome_arquivo = "relatorio_historico_dietas_especiais.xlsx"
        data = json.dumps(
            {
                "lote": str(self.lote.uuid),
                "data": "09/05/2025",
                "periodos_escolares_selecionadas[]": str(self.periodo_integral.uuid),
            }
        )
        gera_pdf_relatorio_historico_dietas_especiais_async(user, nome_arquivo, data)

        central_download = CentralDeDownload.objects.get()
        assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO

        reader = PdfFileReader(central_download.arquivo.path)
        page = reader.pages[0]
        conteudo_pdf_pagina_1 = page.extractText()

        assert "Manhã" not in conteudo_pdf_pagina_1
        assert "Tarde" not in conteudo_pdf_pagina_1
        assert "Integral" in conteudo_pdf_pagina_1
