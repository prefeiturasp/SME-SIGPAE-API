import datetime
import random

import pytest

from config.celery import app
from src.dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from src.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)
from src.dieta_especial.tasks import (
    cancela_dietas_ativas_automaticamente_task,
    cancela_dietas_pendente_autorizacao_task,
    processa_dietas_especiais_task,
)
from src.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from src.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
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
        self.tipo_unidade_emebs = TipoUnidadeEscolarFactory.create(iniciais="EMEBS")
        self.escola_emebs = EscolaFactory.create(
            nome="EMEBS HELEN KELLER",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emebs,
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

    def setup_dieta_aluno_mudou_escola(self):
        self.aluno_3 = AlunoFactory.create(
            codigo_eol="9999999",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_emebs,
        )
        self.solicitacao_dieta_especial_aluno_mudou_escola = (
            SolicitacaoDietaEspecialFactory.create(
                aluno=self.aluno_3,
                ativo=True,
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
                escola_destino=self.escola_emef,
                rastro_terceirizada=self.terceirizada,
            )
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial_aluno_mudou_escola.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def setup_dieta_aluno_saiu_da_rede(self):
        self.aluno_4 = AlunoFactory.create(
            codigo_eol="1111111",
            periodo_escolar=self.periodo_integral,
            escola=None,
            nao_matriculado=True,
        )
        self.solicitacao_dieta_especial_saiu_da_rede = (
            SolicitacaoDietaEspecialFactory.create(
                aluno=self.aluno_4,
                ativo=True,
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
                escola_destino=self.escola_emef,
                rastro_terceirizada=self.terceirizada,
            )
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial_saiu_da_rede.uuid,
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

    def test_cancela_dietas_ativas_automaticamente_task(self):
        app.conf.update(CELERY_ALWAYS_EAGER=True)

        self.setup_generico()
        self.setup_dieta_aluno_mudou_escola()
        self.setup_dieta_aluno_saiu_da_rede()

        assert SolicitacaoDietaEspecial.objects.count() == 2
        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO
            ).count()
            == 2
        )

        cancela_dietas_ativas_automaticamente_task()

        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.CANCELADO_ALUNO_MUDOU_ESCOLA
            ).count()
            == 1
        )
        assert (
            SolicitacaoDietaEspecial.objects.filter(
                status=SolicitacaoDietaEspecial.workflow_class.CANCELADO_ALUNO_NAO_PERTENCE_REDE
            ).count()
            == 1
        )
        assert SolicitacaoDietaEspecial.objects.filter(ativo=True).count() == 2


class TestCancelaDietasPendenteAutorizacaoTask:
    def setup_method(self):
        self.usuario = UsuarioFactory.create(id=1, nome="System Admin")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )
        self.tipo_unidade = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_origem = EscolaFactory.create(
            nome="EMEF ORIGEM",
            codigo_eol="100001",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        self.escola_destino = EscolaFactory.create(
            nome="EMEF DESTINO",
            codigo_eol="100002",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )
        self.escola_terceira = EscolaFactory.create(
            nome="EMEF TERCEIRA",
            codigo_eol="100003",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def cria_solicitacao_pendente(self, *, aluno, escola_destino, tipo_solicitacao):
        solicitacao = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            ativo=False,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR,
            escola_destino=escola_destino,
            tipo_solicitacao=tipo_solicitacao,
            rastro_escola=self.escola_origem,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=solicitacao.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        return solicitacao

    def test_cancela_dietas_pendente_autorizacao_task_quando_aluno_mudou_escola(self):
        app.conf.update(CELERY_ALWAYS_EAGER=True)
        aluno = AlunoFactory.create(
            codigo_eol="7777777",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_terceira,
        )
        solicitacao = self.cria_solicitacao_pendente(
            aluno=aluno,
            escola_destino=self.escola_destino,
            tipo_solicitacao=TIPO_SOLICITACAO_DIETA["COMUM"],
        )

        cancela_dietas_pendente_autorizacao_task()

        solicitacao.refresh_from_db()
        ultimo_log = solicitacao.logs.last()
        assert (
            solicitacao.status
            == SolicitacaoDietaEspecial.workflow_class.CANCELADO_ENCERRAMENTO_MATRICULA
        )
        assert (
            ultimo_log.status_evento
            == LogSolicitacoesUsuario.CANCELADO_ENCERRAMENTO_MATRICULA
        )
        assert ultimo_log.usuario_id == self.usuario.id

    def test_cancela_dietas_pendente_autorizacao_task_quando_aluno_nao_mudou_escola(
        self,
    ):
        app.conf.update(CELERY_ALWAYS_EAGER=True)
        aluno = AlunoFactory.create(
            codigo_eol="8888888",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_destino,
        )
        solicitacao = self.cria_solicitacao_pendente(
            aluno=aluno,
            escola_destino=self.escola_destino,
            tipo_solicitacao=TIPO_SOLICITACAO_DIETA["COMUM"],
        )
        quantidade_logs_antes = solicitacao.logs.count()

        cancela_dietas_pendente_autorizacao_task()

        solicitacao.refresh_from_db()
        assert (
            solicitacao.status
            == SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
        )
        assert solicitacao.logs.count() == quantidade_logs_antes

    def test_cancela_dietas_pendente_autorizacao_task_nao_afeta_alteracao_ue_ou_aluno_nao_matriculado(
        self,
    ):
        app.conf.update(CELERY_ALWAYS_EAGER=True)
        aluno_alteracao = AlunoFactory.create(
            codigo_eol="9999999",
            periodo_escolar=self.periodo_integral,
            escola=self.escola_terceira,
        )
        aluno_nao_matriculado = AlunoFactory.create(
            codigo_eol="1111111",
            periodo_escolar=self.periodo_integral,
            escola=None,
            nao_matriculado=True,
        )
        solicitacao_alteracao = self.cria_solicitacao_pendente(
            aluno=aluno_alteracao,
            escola_destino=self.escola_destino,
            tipo_solicitacao=TIPO_SOLICITACAO_DIETA["ALTERACAO_UE"],
        )
        solicitacao_nao_matriculado = self.cria_solicitacao_pendente(
            aluno=aluno_nao_matriculado,
            escola_destino=self.escola_destino,
            tipo_solicitacao=TIPO_SOLICITACAO_DIETA["ALUNO_NAO_MATRICULADO"],
        )
        logs_alteracao_antes = solicitacao_alteracao.logs.count()
        logs_nao_matriculado_antes = solicitacao_nao_matriculado.logs.count()

        cancela_dietas_pendente_autorizacao_task()

        solicitacao_alteracao.refresh_from_db()
        solicitacao_nao_matriculado.refresh_from_db()
        assert (
            solicitacao_alteracao.status
            == SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
        )
        assert (
            solicitacao_nao_matriculado.status
            == SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR
        )
        assert solicitacao_alteracao.logs.count() == logs_alteracao_antes
        assert solicitacao_nao_matriculado.logs.count() == logs_nao_matriculado_antes
