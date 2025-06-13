from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    LogQuantidadeDietasAutorizadasCEIFactory,
    LogQuantidadeDietasAutorizadasFactory,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LogAlunosMatriculadosFaixaEtariaDiaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class BaseSetupHistoricoDietas:
    def setup_generico(self):
        self.periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        self.periodo_tarde = PeriodoEscolarFactory.create(nome="TARDE")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")

        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
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
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
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

    def setup_faixas_etarias(self):
        FaixaEtariaFactory.create(inicio=0, fim=1)
        FaixaEtariaFactory.create(inicio=1, fim=4)
        FaixaEtariaFactory.create(inicio=4, fim=6)
        FaixaEtariaFactory.create(inicio=6, fim=7)
        self.faixa_1 = FaixaEtariaFactory.create(inicio=7, fim=12)
        self.faixa_2 = FaixaEtariaFactory.create(inicio=12, fim=48)
        FaixaEtariaFactory.create(inicio=48, fim=73)

    def setup_escola_cei(self):
        self.tipo_unidade_cei = TipoUnidadeEscolarFactory.create(iniciais="CEI DIRET")
        self.escola_cei = EscolaFactory.create(
            nome="CEI DIRET HAROLDO",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_cei,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_logs_escola_cei(self):
        for periodo_escolar in [self.periodo_integral]:
            for faixa_etaria in [self.faixa_1, self.faixa_2]:
                LogAlunosMatriculadosFaixaEtariaDiaFactory.create(
                    escola=self.escola_cei,
                    periodo_escolar=periodo_escolar,
                    quantidade=100,
                    faixa_etaria=faixa_etaria,
                    criado_em="2025-05-09",
                    data="2025-05-09",
                )
                for classificacao in [
                    self.classificacao_tipo_a,
                    self.classificacao_tipo_b,
                ]:
                    LogQuantidadeDietasAutorizadasCEIFactory.create(
                        data="2025-05-09",
                        escola=self.escola_cei,
                        periodo_escolar=periodo_escolar,
                        classificacao=classificacao,
                        faixa_etaria=faixa_etaria,
                        quantidade=5,
                    )

    def setup_escola_ceu_gestao(self):
        self.tipo_unidade_ceu_gestao = TipoUnidadeEscolarFactory.create(
            iniciais="CEU GESTAO"
        )
        self.escola_ceu_gestao = EscolaFactory.create(
            nome="CEU GESTAO 9 DE JULHO",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_ceu_gestao,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_logs_escola_ceu_gestao(self):
        for classificacao in [self.classificacao_tipo_a, self.classificacao_tipo_b]:
            LogQuantidadeDietasAutorizadasFactory.create(
                data="2025-05-09",
                escola=self.escola_ceu_gestao,
                periodo_escolar=None,
                classificacao=classificacao,
                quantidade=5,
            )

    def setup_escola_emebs(self):
        self.tipo_unidade_emebs = TipoUnidadeEscolarFactory.create(iniciais="EMEBS")
        self.escola_emebs = EscolaFactory.create(
            nome="EMEBS HELEN KELLER",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emebs,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_logs_escola_emebs(self):
        for periodo_escolar in [self.periodo_manha, self.periodo_tarde]:
            LogAlunosMatriculadosPeriodoEscolaFactory.create(
                escola=self.escola_emebs,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=100,
                criado_em="2025-05-09",
            )
            for classificacao in [self.classificacao_tipo_a, self.classificacao_tipo_b]:
                for infantil_ou_fundamental in ["INFANTIL", "FUNDAMENTAL"]:
                    LogQuantidadeDietasAutorizadasFactory.create(
                        data="2025-05-09",
                        escola=self.escola_emebs,
                        periodo_escolar=periodo_escolar,
                        classificacao=classificacao,
                        quantidade=5,
                        infantil_ou_fundamental=infantil_ou_fundamental,
                    )

    def setup_escola_cemei(self):
        self.tipo_unidade_cemei = TipoUnidadeEscolarFactory.create(iniciais="CEMEI")
        self.escola_cemei = EscolaFactory.create(
            nome="CEMEI ALZIRA",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_cemei,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_logs_escola_cemei_cei(self):
        for periodo_escolar in [self.periodo_integral]:
            for faixa_etaria in [self.faixa_1]:
                LogAlunosMatriculadosFaixaEtariaDiaFactory.create(
                    escola=self.escola_cemei,
                    periodo_escolar=periodo_escolar,
                    quantidade=100,
                    faixa_etaria=faixa_etaria,
                    criado_em="2025-05-09",
                    data="2025-05-09",
                )
                for classificacao in [
                    self.classificacao_tipo_a,
                    self.classificacao_tipo_b,
                ]:
                    LogQuantidadeDietasAutorizadasCEIFactory.create(
                        data="2025-05-09",
                        escola=self.escola_cemei,
                        periodo_escolar=periodo_escolar,
                        classificacao=classificacao,
                        faixa_etaria=faixa_etaria,
                        quantidade=5,
                    )

    def setup_logs_escola_cemei_emei(self):
        for periodo_escolar in [self.periodo_manha, self.periodo_tarde]:
            LogAlunosMatriculadosPeriodoEscolaFactory.create(
                escola=self.escola_cemei,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=100,
                criado_em="2025-05-09",
            )
            for classificacao in [self.classificacao_tipo_a, self.classificacao_tipo_b]:
                LogQuantidadeDietasAutorizadasFactory.create(
                    data="2025-05-09",
                    escola=self.escola_cemei,
                    periodo_escolar=periodo_escolar,
                    classificacao=classificacao,
                    quantidade=5,
                )

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
