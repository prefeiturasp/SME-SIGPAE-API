import datetime
import logging
import pytest
from freezegun import freeze_time

from celery import shared_task
from django.db.models import Q
from collections import Counter

from sme_sigpae_api.dieta_especial.tasks.logs import (
    gera_logs_dietas_recreio_ferias_diariamente,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoGestaoFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    MotivoAlteracaoUEFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.tasks.utils.logs import (
    gera_logs_dietas_recreio_ferias_escolas_cei,
    gera_logs_dietas_recreio_ferias_escolas_comuns,
    gera_logs_dietas_recreio_ferias_parte_sem_faixa_cemei,
)

from sme_sigpae_api.escola.models import Aluno
from sme_sigpae_api.dieta_especial.models import (
    SolicitacaoDietaEspecial,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
)


pytestmark = [
    pytest.mark.django_db(transaction=True, reset_sequences=True)
]


class TestLogsRecreioNasFerias:
    def setup_method(self):
        self.tipo_gestao_terc = TipoGestaoFactory.create(nome="TERC TOTAL")

        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01",
            diretoria_regional=self.dre,
            terceirizada=self.terceirizada,
        )

        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")

        self.classificacao_tipo_a = ClassificacaoDietaFactory.create(nome="Tipo A")
        self.classificacao_tipo_b = ClassificacaoDietaFactory.create(nome="Tipo B")

        self.motivo_recreio = MotivoAlteracaoUEFactory.create(
            nome="Dieta Especial - Recreio nas Férias"
        )

        self.faixa_0_a_11m = FaixaEtariaFactory.create(
            inicio=0, fim=12, ativo=True
        )
        self.faixa_1a_a_1a11m = FaixaEtariaFactory.create(
            inicio=12, fim=24, ativo=True
        )
        self.faixa_2a_a_3a11m = FaixaEtariaFactory.create(
            inicio=24, fim=48, ativo=True
        )
        self.faixa_4a_a_5a11m = FaixaEtariaFactory.create(
            inicio=48, fim=72, ativo=True
        )


    def setup_escola_emef(self):
        tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF TESTE",
            tipo_gestao=self.tipo_gestao_terc,
            tipo_unidade=tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        return self.escola_emef

    def setup_escola_cei(self):
        tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="CEI")
        self.escola_cei = EscolaFactory.create(
            nome="CEI TESTE",
            tipo_gestao=self.tipo_gestao_terc,
            tipo_unidade=tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        return self.escola_cei

    def setup_escola_cemei(self):
        tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="CEMEI")
        self.escola_cemei = EscolaFactory.create(
            nome="CEMEI TESTE",
            tipo_gestao=self.tipo_gestao_terc,
            tipo_unidade=tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        return self.escola_cemei

    def setup_escola_emebs(self):
        tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="EMEBS")
        self.escola_emebs = EscolaFactory.create(
            nome="EMEBS TESTE",
            tipo_gestao=self.tipo_gestao_terc,
            tipo_unidade=tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        return self.escola_emebs

    def criar_dieta_recreio_comum(self, aluno, classificacao):
        return SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            escola_destino=aluno.escola,
            classificacao=classificacao,
            tipo_solicitacao="COMUM",
            motivo_alteracao_ue=self.motivo_recreio,
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )

    def criar_dieta_recreio_nao_matriculado(
        self, escola, classificacao, data_nascimento
    ):
        aluno = AlunoFactory.create(
            escola=None,
            nao_matriculado=True,
            data_nascimento=data_nascimento,
            periodo_escolar=None,
        )
        return SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            escola_destino=escola,
            classificacao=classificacao,
            tipo_solicitacao="ALUNO_NAO_MATRICULADO",
            dieta_para_recreio_ferias=True,
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )

    @freeze_time("2025-01-15")
    def test_logs_escola_emef_recreio_ferias(self):
        escola = self.setup_escola_emef()

        for i in range(3):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2015, 1, 1),
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        for i in range(2):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2015, 1, 1),
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_b)

        dietas = SolicitacaoDietaEspecial.objects.filter(escola_destino=escola)
        data_log = datetime.date(2025, 1, 15)

        logs = gera_logs_dietas_recreio_ferias_escolas_comuns(
            escola, dietas, data_log
        )

        assert len(logs) == 2

        log_tipo_a = [l for l in logs if l.classificacao == self.classificacao_tipo_a][0]
        log_tipo_b = [l for l in logs if l.classificacao == self.classificacao_tipo_b][0]

        assert log_tipo_a.quantidade == 3
        assert log_tipo_b.quantidade == 2
        assert log_tipo_a.escola == escola
        assert log_tipo_b.escola == escola

    @freeze_time("2025-01-15")
    def test_logs_escola_cei_recreio_ferias(self):
        escola = self.setup_escola_cei()

        for _ in range(2):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2024, 7, 15),
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        for _ in range(3):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2023, 7, 15),
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        dietas = SolicitacaoDietaEspecial.objects.filter(escola_destino=escola)
        data_log = datetime.date(2025, 1, 15)

        logs = gera_logs_dietas_recreio_ferias_escolas_cei(escola, dietas, data_log)
        logs_tipo_a = [l for l in logs if l.classificacao == self.classificacao_tipo_a]

        total = sum(l.quantidade for l in logs_tipo_a)
        assert total == 5

    @freeze_time("2025-01-15")
    def test_logs_escola_cemei_recreio_ferias(self):
        escola = self.setup_escola_cemei()

        # Alunos matriculados ciclo CEI (até 3a11m)
        for _ in range(2):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2023, 1, 15),  # ~2 anos
                ciclo=Aluno.CICLO_ALUNO_CEI,  # numérico = 1
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        # Alunos matriculados ciclo EMEI (>= 4 anos)
        for _ in range(3):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2020, 1, 15),  # ~5 anos
                ciclo=Aluno.CICLO_ALUNO_EMEI,  # numérico = 2
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        # Aluno não matriculado com 2 anos (vai para CEI)
        self.criar_dieta_recreio_nao_matriculado(
            escola,
            self.classificacao_tipo_a,
            datetime.date(2023, 1, 15),
        )

        # Aluno não matriculado com 5 anos (vai para EMEI)
        self.criar_dieta_recreio_nao_matriculado(
            escola,
            self.classificacao_tipo_a,
            datetime.date(2020, 1, 15),
        )

        dietas = SolicitacaoDietaEspecial.objects.filter(escola_destino=escola)
        data_log = datetime.date(2025, 1, 15)

        # Parte CEI (com faixa etária)
        logs_cei = gera_logs_dietas_recreio_ferias_escolas_cei(escola, dietas, data_log)

        # Parte EMEI (sem faixa etária)
        logs_emei = gera_logs_dietas_recreio_ferias_parte_sem_faixa_cemei(
            escola, dietas, data_log
        )

        logs_cei_tipo_a = [
            l for l in logs_cei if l.classificacao == self.classificacao_tipo_a
        ]
        total_cei = sum(l.quantidade for l in logs_cei_tipo_a)
        assert total_cei == 3  # 2 matriculados + 1 não matriculado

        logs_emei_tipo_a = [
            l for l in logs_emei if l.classificacao == self.classificacao_tipo_a
        ]
        assert len(logs_emei_tipo_a) == 1
        assert logs_emei_tipo_a[0].quantidade == 4  # 3 matriculados + 1 não matriculado

    @freeze_time("2025-01-15")
    def test_logs_escola_emebs_recreio_ferias(self):
        from sme_sigpae_api.escola.models import Aluno

        escola = self.setup_escola_emebs()

        for _ in range(2):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2020, 1, 1),
                etapa=Aluno.ETAPA_INFANTIL,
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        for _ in range(3):
            aluno = AlunoFactory.create(
                escola=escola,
                periodo_escolar=self.periodo_integral,
                data_nascimento=datetime.date(2015, 1, 1),
                etapa=20,
            )
            self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        dietas = SolicitacaoDietaEspecial.objects.filter(escola_destino=escola)
        data_log = datetime.date(2025, 1, 15)

        logs = gera_logs_dietas_recreio_ferias_escolas_comuns(
            escola, dietas, data_log
        )

        assert all(l.escola == escola for l in logs)
        logs_tipo_a = [
            l for l in logs if l.classificacao == self.classificacao_tipo_a
        ]
        assert len(logs_tipo_a) == 1
        assert logs_tipo_a[0].quantidade == 5

    @freeze_time("2025-01-15")
    def test_nao_gera_logs_fora_janeiro_julho(self):

        with freeze_time("2025-03-15"):
            gera_logs_dietas_recreio_ferias_diariamente()
            assert (
                LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.count() == 0
            )
            assert (
                LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI.objects.count()
                == 0
            )

    @freeze_time("2025-01-15")
    def test_nao_gera_logs_para_escolas_nao_terc_total(self):
        tipo_gestao_direta = TipoGestaoFactory.create(nome="DIRETA")
        tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="EMEF")

        escola_direta = EscolaFactory.create(
            nome="EMEF DIRETA",
            tipo_gestao=tipo_gestao_direta,
            tipo_unidade=tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

        aluno = AlunoFactory.create(
            escola=escola_direta,
            periodo_escolar=self.periodo_integral,
        )
        self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        logs_antes = LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.count()
        logs_cei_antes = LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI.objects.count()

        gera_logs_dietas_recreio_ferias_diariamente()

        logs_depois = LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.count()
        logs_cei_depois = LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI.objects.count()

        assert logs_antes == logs_depois
        assert logs_cei_antes == logs_cei_depois

    @freeze_time("2025-01-15")
    def test_logs_quantidade_zero_para_classificacoes_sem_dietas(self):
        escola = self.setup_escola_emef()

        aluno = AlunoFactory.create(
            escola=escola,
            periodo_escolar=self.periodo_integral,
        )
        self.criar_dieta_recreio_comum(aluno, self.classificacao_tipo_a)

        dietas = SolicitacaoDietaEspecial.objects.filter(escola_destino=escola)
        data_log = datetime.date(2025, 1, 15)

        logs = gera_logs_dietas_recreio_ferias_escolas_comuns(
            escola, dietas, data_log
        )

        log_tipo_b = [l for l in logs if l.classificacao == self.classificacao_tipo_b]
        assert len(log_tipo_b) == 1
        assert log_tipo_b[0].quantidade == 0
