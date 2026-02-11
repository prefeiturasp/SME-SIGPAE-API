import datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    GrupoUnidadeEscolarFactory,
    HistoricoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoGestaoFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.base_factory import (
    CategoriaMedicaoFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    SolicitacaoMedicaoInicialFactory,
)
from sme_sigpae_api.medicao_inicial.tasks import gera_pdf_relatorio_unificado_async
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(
        username="user_teste",
        password="password",
        email="user_teste@admin.com",
        registro_funcional="123456",
    )


@freeze_time("2026-02-15")
class TestGeraRelatorioUnificado:
    """Testes para verificar a geração do relatório unificado de medições iniciais."""

    def setup_tipos_unidade_e_grupo(self):
        tipo_unidade_emei = TipoUnidadeEscolarFactory.create(iniciais="EMEI")
        tipo_unidade_cemei = TipoUnidadeEscolarFactory.create(iniciais="CEMEI")

        grupo_unidade_escolar = GrupoUnidadeEscolarFactory.create(nome="CEMEI")
        grupo_unidade_escolar.tipos_unidades.add(tipo_unidade_cemei)

        return tipo_unidade_emei, tipo_unidade_cemei, grupo_unidade_escolar

    def setup_infraestrutura_comum(self):
        terceirizada = EmpresaFactory.create()
        diretoria_regional = DiretoriaRegionalFactory.create(
            nome="DIRETORIA REGIONAL TESTE"
        )
        lote = LoteFactory.create(
            terceirizada=terceirizada,
            diretoria_regional=diretoria_regional,
        )
        tipo_gestao = TipoGestaoFactory.create(nome="TERC TOTAL")

        return diretoria_regional, lote, tipo_gestao

    def setup_escola_com_historico(
        self,
        tipo_unidade_emei,
        tipo_unidade_cemei,
        lote,
        diretoria_regional,
        tipo_gestao,
    ):
        """
        Cria uma escola que era EMEI até 31/12/2025 e se tornou CEMEI a partir de 01/01/2026.
        """
        # Escola atual é CEMEI
        escola = EscolaFactory.create(
            nome="CEMEI ESCOLA COM HISTORICO",
            lote=lote,
            diretoria_regional=diretoria_regional,
            tipo_gestao=tipo_gestao,
            tipo_unidade=tipo_unidade_cemei,
            codigo_eol="100001",
        )

        HistoricoEscolaFactory.create(
            escola=escola,
            nome="EMEI ESCOLA QUANDO ERA EMEI",
            tipo_unidade=tipo_unidade_emei,
            data_inicial=datetime.date(2020, 1, 1),
            data_final=datetime.date(2025, 12, 31),
        )

        return escola

    def setup_escola_sem_historico(
        self, tipo_unidade_cemei, lote, diretoria_regional, tipo_gestao
    ):
        """
        Cria uma escola CEMEI sem histórico de mudança de tipo.
        """
        escola = EscolaFactory.create(
            nome="CEMEI ESCOLA SEM HISTORICO",
            lote=lote,
            diretoria_regional=diretoria_regional,
            tipo_gestao=tipo_gestao,
            tipo_unidade=tipo_unidade_cemei,
            codigo_eol="100002",
        )

        return escola

    def setup_solicitacoes(
        self, escola_com_historico, escola_sem_historico, periodo_escolar
    ):
        """Cria solicitações de medição para janeiro/2026 para ambas as escolas."""
        solicitacao_com_historico = SolicitacaoMedicaoInicialFactory.create(
            escola=escola_com_historico,
            mes="01",
            ano=2026,
            status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )

        solicitacao_sem_historico = SolicitacaoMedicaoInicialFactory.create(
            escola=escola_sem_historico,
            mes="01",
            ano=2026,
            status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )

        return solicitacao_com_historico, solicitacao_sem_historico

    def setup_medicoes_basicas(
        self, solicitacao_com_historico, solicitacao_sem_historico, periodo_escolar
    ):
        """Cria medições básicas para as solicitações."""
        categoria_medicao = CategoriaMedicaoFactory.create(nome="ALIMENTAÇÃO")

        medicao_com_historico = baker.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao_com_historico,
            periodo_escolar=periodo_escolar,
            grupo=None,
        )

        medicao_sem_historico = baker.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao_sem_historico,
            periodo_escolar=periodo_escolar,
            grupo=None,
        )

        return medicao_com_historico, medicao_sem_historico, categoria_medicao

    @patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola_cemei"
    )
    def test_gera_relatorio_unificado_com_sucesso(self, mock_relatorio_cemei, usuario):
        """
        Testa que o relatório unificado é gerado com sucesso para duas solicitações:
        - Uma com escola que tem HistoricoEscola no mês da solicitação
        - Outra sem HistoricoEscola

        Valida o conteúdo HTML gerado com asserts específicos para cada escola.
        """
        tipo_emei, tipo_cemei, grupo = self.setup_tipos_unidade_e_grupo()
        dre, lote, tipo_gestao = self.setup_infraestrutura_comum()

        escola_com_historico = self.setup_escola_com_historico(
            tipo_emei, tipo_cemei, lote, dre, tipo_gestao
        )
        escola_sem_historico = self.setup_escola_sem_historico(
            tipo_cemei, lote, dre, tipo_gestao
        )

        periodo_escolar = PeriodoEscolarFactory.create(nome="INTEGRAL")

        solicitacao_com_historico, solicitacao_sem_historico = self.setup_solicitacoes(
            escola_com_historico, escola_sem_historico, periodo_escolar
        )
        self.setup_medicoes_basicas(
            solicitacao_com_historico, solicitacao_sem_historico, periodo_escolar
        )

        html_strings_captured = []

        def capture_html(solicitacao):
            html_string = f"""
            <html>
                <body>
                    <h1>{solicitacao.escola.nome}</h1>
                    <p>Código EOL: {solicitacao.escola.codigo_eol}</p>
                    <p>Período: {solicitacao.mes}/{solicitacao.ano}</p>
                    <p>Mês: JANEIRO</p>
                    <p>Período Escolar: INTEGRAL</p>
                </body>
            </html>
            """
            html_strings_captured.append(html_string)
            # Retorna um PDF válido fake
            from pypdf import PdfWriter

            buffer = BytesIO()
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(buffer)
            return buffer.getvalue()

        mock_relatorio_cemei.side_effect = capture_html

        nome_arquivo = "relatorio_unificado_teste.pdf"

        ids_solicitacoes = [
            solicitacao_com_historico.uuid,
            solicitacao_sem_historico.uuid,
        ]
        tipos_de_unidade = ["CEMEI"]

        gera_pdf_relatorio_unificado_async(
            user=usuario.get_username(),
            nome_arquivo=nome_arquivo,
            ids_solicitacoes=ids_solicitacoes,
            tipos_de_unidade=tipos_de_unidade,
        )

        assert (
            mock_relatorio_cemei.call_count == 2
        ), "Deve gerar 2 PDFs (um para cada escola)"

        registro = CentralDeDownload.objects.get(identificador=nome_arquivo)
        assert registro.status == CentralDeDownload.STATUS_CONCLUIDO
        assert registro.arquivo is not None

        html_com_historico = html_strings_captured[0]

        assert (
            "CEMEI ESCOLA COM HISTORICO" in html_com_historico
        ), "Nome atual da escola deve estar presente"
        assert (
            "100001" in html_com_historico
        ), "Código EOL da escola deve estar presente"
        assert (
            "01/2026" in html_com_historico or "JANEIRO" in html_com_historico.upper()
        ), "Mês/Ano da medição deve estar presente"
        assert (
            "INTEGRAL" in html_com_historico.upper()
        ), "Período escolar deve estar presente no relatório"

        html_sem_historico = html_strings_captured[1]

        assert (
            "CEMEI ESCOLA SEM HISTORICO" in html_sem_historico
        ), "Nome da escola sem histórico deve estar presente"
        assert (
            "100002" in html_sem_historico
        ), "Código EOL da escola sem histórico deve estar presente"
        assert (
            "01/2026" in html_sem_historico or "JANEIRO" in html_sem_historico.upper()
        ), "Mês/Ano da medição deve estar presente"
        assert (
            "INTEGRAL" in html_sem_historico.upper()
        ), "Período escolar deve estar presente no relatório"

    @patch("sme_sigpae_api.relatorios.relatorios.html_to_pdf_file")
    def test_escola_com_historico_usa_tipo_correto(self, mock_html_to_pdf):
        """
        Verifica que a escola com histórico usa o tipo de unidade correto
        baseado na data de referência da medição.
        """
        tipo_emei, tipo_cemei, grupo = self.setup_tipos_unidade_e_grupo()
        dre, lote, tipo_gestao = self.setup_infraestrutura_comum()

        escola_com_historico = self.setup_escola_com_historico(
            tipo_emei, tipo_cemei, lote, dre, tipo_gestao
        )

        PeriodoEscolarFactory.create(nome="INTEGRAL")

        # Solicitação de janeiro/2026 (quando já é CEMEI)
        solicitacao_janeiro = SolicitacaoMedicaoInicialFactory.create(
            escola=escola_com_historico,
            mes="01",
            ano=2026,
            status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )

        # Verifica que em janeiro/2026 a escola é CEMEI
        data_referencia = solicitacao_janeiro.data_referencia
        assert escola_com_historico.eh_cemei_data(
            data_referencia
        ), "Em janeiro/2026, a escola deve ser CEMEI"

        # Solicitação de dezembro/2025 (quando ainda era EMEI)
        solicitacao_dezembro = SolicitacaoMedicaoInicialFactory.create(
            escola=escola_com_historico,
            mes="12",
            ano=2025,
            status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )

        # Verifica que em dezembro/2025 a escola era EMEI
        data_referencia_dez = solicitacao_dezembro.data_referencia
        assert escola_com_historico.eh_emei_data(
            data_referencia_dez
        ), "Em dezembro/2025, a escola deve ser EMEI"

    def test_historico_escola_valores_corretos(self):
        """
        Testa que o HistoricoEscola tem os valores corretos configurados.
        """

        tipo_emei, tipo_cemei, grupo = self.setup_tipos_unidade_e_grupo()
        dre, lote, tipo_gestao = self.setup_infraestrutura_comum()

        escola_com_historico = self.setup_escola_com_historico(
            tipo_emei, tipo_cemei, lote, dre, tipo_gestao
        )

        assert (
            escola_com_historico.historicos_escola.exists()
        ), "Escola deve ter histórico"

        historico = escola_com_historico.historicos_escola.first()
        assert (
            historico.tipo_unidade == tipo_emei
        ), "Tipo de unidade no histórico deve ser EMEI"
        assert historico.data_inicial == datetime.date(
            2020, 1, 1
        ), "Data inicial deve estar correta"
        assert historico.data_final == datetime.date(
            2025, 12, 31
        ), "Data final deve ser 31/12/2025"
        assert "EMEI" in historico.nome, "Nome do histórico deve conter EMEI"

    def test_escola_sem_historico_nao_tem_registros(self):
        """
        Verifica que a escola sem histórico não tem registros de HistoricoEscola.
        """
        tipo_emei, tipo_cemei, grupo = self.setup_tipos_unidade_e_grupo()
        dre, lote, tipo_gestao = self.setup_infraestrutura_comum()

        escola_sem_historico = self.setup_escola_sem_historico(
            tipo_cemei, lote, dre, tipo_gestao
        )

        assert (
            not escola_sem_historico.historicos_escola.exists()
        ), "Escola sem histórico não deve ter registros de HistoricoEscola"
        assert (
            escola_sem_historico.tipo_unidade == tipo_cemei
        ), "Tipo da escola deve ser CEMEI"
