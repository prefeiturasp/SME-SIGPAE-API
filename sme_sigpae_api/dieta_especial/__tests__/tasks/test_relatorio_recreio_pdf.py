import pytest
from freezegun.api import freeze_time
from PyPDF4 import PdfFileReader

from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.dieta_especial.tasks import (
    gera_pdf_relatorio_recreio_nas_ferias_async,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


def resgata_conteudo_pdf():
    central_download = CentralDeDownload.objects.get()
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    reader = PdfFileReader(central_download.arquivo.path)
    page = reader.pages[0]
    return page.extractText()


class BaseSetupRecreioNasFerias:
    def setup_generico(self):
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )

    def setup_escolas(self):
        self.tipo_unidade_emef = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        self.tipo_unidade_emebs = TipoUnidadeEscolarFactory.create(iniciais="EMEBS")
        self.escola_emebs = EscolaFactory.create(
            nome="EMEBS HELEN KELLER",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emebs,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_classificacao_dieta(self):
        self.classificacao_tipo_a = ClassificacaoDietaFactory.create(nome="Tipo A")

    def setup_aluno(self):
        self.aluno = AlunoFactory.create(
            codigo_eol="1234567",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
            nome="MARIA SILVA",
        )

    def setup_solicitacao_dieta(self):
        SolicitacaoDietaEspecialFactory.create(
            aluno=self.aluno,
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            escola_destino=self.escola_emef,
            rastro_escola=self.escola_emebs,
            rastro_terceirizada=self.terceirizada,
            classificacao=self.classificacao_tipo_a,
            dieta_para_recreio_ferias=True,
            data_inicio="2025-08-01",
            data_termino="2025-08-31",
            periodo_recreio_inicio="2025-08-01",
            periodo_recreio_fim="2025-08-31",
        )


@pytest.mark.usefixtures("client_autenticado_vinculo_codae_gestao_alimentacao_dieta")
@freeze_time("2025-08-25")
class TestGeraPDFRelatorioRecreioNasFeriasAsync(BaseSetupRecreioNasFerias):
    def setup(self):
        self.setup_generico()
        self.setup_classificacao_dieta()
        self.setup_escolas()
        self.setup_aluno()
        self.setup_solicitacao_dieta()

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
            }
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
        assert "EMEF PERICLES" not in conteudo_pdf
        assert "Tipo A" not in conteudo_pdf
        assert "31/08/2025" not in conteudo_pdf
