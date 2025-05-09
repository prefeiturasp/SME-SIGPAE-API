import pytest

from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    LogQuantidadeDietasAutorizadasFactory,
)
from sme_sigpae_api.dieta_especial.tasks import (
    gera_xlsx_relatorio_historico_dietas_especiais_async,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_vinculo_codae_gestao_alimentacao_dieta")
class GeraXlsxRelatorioHistoricoDietasEspeciaisAsyncTest:
    def setup_generico(self):
        self.periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        self.periodo_tarde = PeriodoEscolarFactory.create(nome="TARDE")

        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )

    def setup_classificacoes_dieta(self):
        self.classificacao_tipo_a = ClassificacaoDietaFactory.create(nome="Tipo A")
        self.classificacao_tipo_b = ClassificacaoDietaFactory.create(nome="Tipo B")

    def setup_escola_emef(self):
        self.tipo_unidade_emef = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF PERICLES",
            codigo_eol="100000",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
        )

    def setup_logs_escola_emef(self):
        for periodo_escolar in [self.periodo_manha, self.periodo_tarde]:
            LogAlunosMatriculadosPeriodoEscolaFactory.create(
                escola=self.escola_emef,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=100,
                criado_em="2025-05-09",
            )
            for classificacao in [self.classificacao_tipo_a, self.classificacao_tipo_b]:
                LogQuantidadeDietasAutorizadasFactory.create(
                    data="2025-05-09",
                    escola=self.escola_emef,
                    periodo_escolar=periodo_escolar,
                    classificacao=classificacao,
                    quantidade=5,
                )

    def setUp(self):
        self.setup_generico()
        self.setup_classificacoes_dieta()
        self.setup_escola_emef()
        self.setup_logs_escola_emef()

    def test_gera_xlsx_historico_dietas_especiais(
        self, client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    ):
        client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
        nome_arquivo = "relatorio_historico_dietas_especiais.xlsx"
        data = {"lote": str(self.lote.uuid), "data": "09/05/2025"}
        gera_xlsx_relatorio_historico_dietas_especiais_async(user, nome_arquivo, data)
