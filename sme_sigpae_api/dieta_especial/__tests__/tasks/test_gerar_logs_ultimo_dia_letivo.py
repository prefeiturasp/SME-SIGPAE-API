import datetime

import pytest
from freezegun import freeze_time

from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.dieta_especial.tasks import gera_logs_dietas_especiais_diariamente

pytestmark = pytest.mark.django_db


class TestUseCaseCriacaoLogsUltimoDiaLetivo:
    def _setup_generico(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
    ):
        self.periodo_manha = periodo_escolar_factory.create(nome="MANHA")
        self.periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
        self.periodo_integral = periodo_escolar_factory.create(nome="INTEGRAL")

        self.dre = diretoria_regional_factory.create(
            nome="IPIRANGA", iniciais="IP", codigo_eol="000200"
        )
        self.terceirizada = empresa_factory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = lote_factory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )

    def _setup_escola_emef(self, tipo_unidade_escolar_factory, escola_factory):
        self.tipo_unidade_emef = tipo_unidade_escolar_factory.create(iniciais="EMEF")
        self.escola_emef = escola_factory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            codigo_eol="000099",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_dias_letivos(self, dia_calendario_factory):
        for i in range(1, 31):
            dia_calendario_factory.create(
                escola=self.escola_emef,
                dia_letivo=True,
                data=datetime.date(2025, 11, i),
            )
        for i in range(1, 32):
            dia_calendario_factory.create(
                escola=self.escola_emef,
                dia_letivo=i <= 19,
                data=datetime.date(2025, 12, i),
            )

    def _setup_usuario_escola(self, usuario_factory, vinculo_factory):
        self.usuario_escola = usuario_factory.create()
        self.vinculo_escola_diretor = vinculo_factory.create(
            usuario=self.usuario_escola,
            object_id=self.escola_emef.id,
            instituicao=self.escola_emef,
            perfil__nome="DIRETOR_UE",
            data_inicial="2025-09-01",
            data_final=None,
            ativo=True,
        )

    def _setup_dietas_especiais(
        self,
        classificacao_dieta_factory,
        solicitacao_dieta_especial_factory,
        aluno_factory,
        log_solicitacoes_usuario_factory,
    ):
        classificacao_tipo_a = classificacao_dieta_factory.create(nome="Tipo A")
        classificacao_tipo_b = classificacao_dieta_factory.create(nome="Tipo B")

        self.aluno_1 = aluno_factory.create(
            escola=self.escola_emef,
            periodo_escolar=self.periodo_integral,
            data_nascimento="2021-08-02",
        )
        self._dieta_1 = solicitacao_dieta_especial_factory.create(
            aluno=self.aluno_1,
            rastro_escola=self.escola_emef,
            classificacao=classificacao_tipo_a,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )
        log = log_solicitacoes_usuario_factory.create(
            uuid_original=self._dieta_1.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )
        log.criado_em = datetime.date(2025, 11, 1)
        log.save()

        self.aluno_2 = aluno_factory.create(
            escola=self.escola_emef,
            periodo_escolar=self.periodo_manha,
            data_nascimento="2021-08-02",
        )
        self._dieta_2 = solicitacao_dieta_especial_factory.create(
            aluno=self.aluno_2,
            rastro_escola=self.escola_emef,
            classificacao=classificacao_tipo_b,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )
        log = log_solicitacoes_usuario_factory.create(
            uuid_original=self._dieta_2.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )
        log.criado_em = datetime.date(2025, 11, 1)
        log.save()

    def _setup(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        usuario_factory,
        vinculo_factory,
        classificacao_dieta_factory,
        solicitacao_dieta_especial_factory,
        aluno_factory,
        log_solicitacoes_usuario_factory,
        dia_calendario_factory,
    ):
        self._setup_generico(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
        )
        self._setup_escola_emef(tipo_unidade_escolar_factory, escola_factory)
        self._setup_dias_letivos(dia_calendario_factory)
        self._setup_usuario_escola(usuario_factory, vinculo_factory)
        self._setup_dietas_especiais(
            classificacao_dieta_factory,
            solicitacao_dieta_especial_factory,
            aluno_factory,
            log_solicitacoes_usuario_factory,
        )

    @freeze_time("2025-12-19")
    def test_gera_logs_dietas_especiais_diariamente_ultimo_dia_letivo(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        usuario_factory,
        vinculo_factory,
        classificacao_dieta_factory,
        solicitacao_dieta_especial_factory,
        aluno_factory,
        log_solicitacoes_usuario_factory,
        dia_calendario_factory,
    ):
        self._setup(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
            tipo_unidade_escolar_factory,
            escola_factory,
            usuario_factory,
            vinculo_factory,
            classificacao_dieta_factory,
            solicitacao_dieta_especial_factory,
            aluno_factory,
            log_solicitacoes_usuario_factory,
            dia_calendario_factory,
        )

        gera_logs_dietas_especiais_diariamente()

        assert LogQuantidadeDietasAutorizadas.objects.count() == 12
        assert (
            LogQuantidadeDietasAutorizadas.objects.filter(data="2025-12-18").count()
            == 6
        )
        assert (
            LogQuantidadeDietasAutorizadas.objects.filter(data="2025-12-19").count()
            == 6
        )

    @freeze_time("2025-12-18")
    def test_gera_logs_dietas_especiais_diariamente_nao_e_ultimo_dia_letivo(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        usuario_factory,
        vinculo_factory,
        classificacao_dieta_factory,
        solicitacao_dieta_especial_factory,
        aluno_factory,
        log_solicitacoes_usuario_factory,
        dia_calendario_factory,
    ):
        self._setup(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
            tipo_unidade_escolar_factory,
            escola_factory,
            usuario_factory,
            vinculo_factory,
            classificacao_dieta_factory,
            solicitacao_dieta_especial_factory,
            aluno_factory,
            log_solicitacoes_usuario_factory,
            dia_calendario_factory,
        )

        gera_logs_dietas_especiais_diariamente()

        assert LogQuantidadeDietasAutorizadas.objects.count() == 6
        assert (
            LogQuantidadeDietasAutorizadas.objects.filter(data="2025-12-17").count()
            == 6
        )
        assert (
            LogQuantidadeDietasAutorizadas.objects.filter(data="2025-12-18").count()
            == 0
        )
