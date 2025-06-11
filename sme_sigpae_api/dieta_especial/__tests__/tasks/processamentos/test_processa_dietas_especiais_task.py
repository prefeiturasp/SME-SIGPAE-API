import datetime
import random

import pytest

from config.celery import app
from sme_sigpae_api.dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.dieta_especial.tasks import processa_dietas_especiais_task
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


def test_processa_dietas_especiais_task(
    usuario_com_pk, solicitacoes_processa_dieta_especial
):
    solicitacoes = SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=datetime.date.today(),
        ativo=False,
        status__in=[
            SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            SolicitacaoDietaEspecial.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )
    assert solicitacoes.count() == 3
    assert (
        solicitacoes.filter(
            tipo_solicitacao=TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE")
        ).count()
        == 2
    )

    processa_dietas_especiais_task()

    solicitacoes = SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=datetime.date.today(),
        status__in=[
            SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            SolicitacaoDietaEspecial.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            SolicitacaoDietaEspecial.workflow_class.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )
    assert solicitacoes.filter(ativo=True).count() == 2
    assert solicitacoes.filter(ativo=False).count() == 2


class TestProcessaDietasEspeciaisTask:
    def setup_generico(self):
        self.usuario = UsuarioFactory.create(id=1, nome="System Admin")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )
        self.tipo_unidade_emef = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def setup_dieta_em_vigencia(self):
        self.aluno_1 = AlunoFactory.create(
            codigo_eol="7777777",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
        )
        self.solicitacao_dieta_especial_em_vigencia = (
            SolicitacaoDietaEspecialFactory.create(
                aluno=self.aluno_1,
                ativo=True,
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            )
        )
        data_inicio = datetime.date.today() - datetime.timedelta(days=1)
        data_termino = datetime.date.today() + datetime.timedelta(days=1)
        self.solicitacao_dieta_especial_em_vigencia.data_inicio = data_inicio
        self.solicitacao_dieta_especial_em_vigencia.data_termino = data_termino
        self.solicitacao_dieta_especial_em_vigencia.save()
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial_em_vigencia.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def setup_dieta_vigencia_finalizada(self):
        self.aluno_2 = AlunoFactory.create(
            codigo_eol="8888888",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emef,
        )
        self.setup_dieta_vigencia_finalizada = SolicitacaoDietaEspecialFactory.create(
            aluno=self.aluno_2,
            ativo=True,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
        )
        data_inicio = datetime.date.today() - datetime.timedelta(days=2)
        data_termino = datetime.date.today() - datetime.timedelta(days=1)
        self.setup_dieta_vigencia_finalizada.data_inicio = data_inicio
        self.setup_dieta_vigencia_finalizada.data_termino = data_termino
        self.setup_dieta_vigencia_finalizada.save()
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.setup_dieta_vigencia_finalizada.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def test_processa_dietas_especiais_task(self):
        app.conf.update(CELERY_ALWAYS_EAGER=True)

        self.setup_generico()
        self.setup_dieta_em_vigencia()
        self.setup_dieta_vigencia_finalizada()

        assert SolicitacaoDietaEspecial.objects.count() == 2
        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
            ).count()
            == 2
        )

        processa_dietas_especiais_task()

        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
            ).count()
            == 1
        )
        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA
            ).count()
            == 1
        )
        assert SolicitacaoDietaEspecial.objects.filter(ativo=True).count() == 2
