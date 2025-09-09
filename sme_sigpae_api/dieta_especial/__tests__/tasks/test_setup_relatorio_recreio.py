import datetime

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
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial


class BaseSetupRecreioNasFerias:
    def setup_generico(self):
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01",
            diretoria_regional=self.dre,
            terceirizada=self.terceirizada,
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
        self.classificacao_tipo_b = ClassificacaoDietaFactory.create(nome="Tipo B")

    def setup_alunos(self):
        self.aluno_1 = AlunoFactory.create(
            codigo_eol="1234567",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
            nome="MARIA SILVA",
        )
        self.aluno_2 = AlunoFactory.create(
            codigo_eol="7654321",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
            nome="JOÃO COSTA",
        )

    def criar_solicitacao_dieta(
        self,
        aluno,
        escola_destino,
        rastro_escola,
        classificacao,
        data_inicio,
        data_termino,
    ):
        SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            escola_destino=escola_destino,
            rastro_escola=rastro_escola,
            rastro_terceirizada=self.terceirizada,
            classificacao=classificacao,
            dieta_para_recreio_ferias=True,
            data_inicio=data_inicio,
            data_termino=data_termino,
            periodo_recreio_inicio=data_inicio,
            periodo_recreio_fim=data_termino,
        )

    def setup_solicitacoes_dieta(self):
        self.criar_solicitacao_dieta(
            aluno=self.aluno_1,
            escola_destino=self.escola_emef,
            rastro_escola=self.escola_emebs,
            classificacao=self.classificacao_tipo_a,
            data_inicio=datetime.date(2025, 8, 1),
            data_termino=datetime.date(2025, 8, 31),
        )
        self.criar_solicitacao_dieta(
            aluno=self.aluno_2,
            escola_destino=self.escola_emebs,
            rastro_escola=self.escola_emef,
            classificacao=self.classificacao_tipo_b,
            data_inicio=datetime.date(2025, 9, 1),
            data_termino=datetime.date(2025, 9, 29),
        )

    def setup(self):
        self.setup_generico()
        self.setup_classificacao_dieta()
        self.setup_escolas()
        self.setup_alunos()
        self.setup_solicitacoes_dieta()
