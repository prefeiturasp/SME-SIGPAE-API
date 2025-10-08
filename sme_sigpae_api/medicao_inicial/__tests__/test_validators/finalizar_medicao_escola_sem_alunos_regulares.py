import datetime

import pytest
from freezegun import freeze_time

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.medicao_inicial.validators import (
    validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares,
    validate_solicitacoes_programas_e_projetos_escola_sem_alunos_regulares,
)

pytestmark = pytest.mark.django_db


@freeze_time("2025-09-01")
class TestUseCaseFinalizaMedicaoEscolaSemAlunosRegulares:
    def _setup_core(
        self,
        periodo_escolar_factory,
        classificacao_dieta_factory,
        categoria_medicao_factory,
    ):
        self.periodo_manha = periodo_escolar_factory.create(nome="MANHA")
        self.classificacao_tipo_a = classificacao_dieta_factory.create(nome="Tipo A")
        self.categoria_medicao_dieta_tipo_a = categoria_medicao_factory.create(
            nome="DIETA ESPECIAL - TIPO A"
        )
        self.categoria_solicitacoes_alimentacao = categoria_medicao_factory.create(
            nome="SOLICITAÇÕES DE ALIMENTAÇÃO"
        )
        self.categoria_alimentacao = categoria_medicao_factory.create(
            nome="ALIMENTAÇÃO"
        )

    def _setup_escola_cmct(
        self, diretoria_regional_factory, lote_factory, escola_factory
    ):
        self.dre = diretoria_regional_factory.create()
        self.lote = lote_factory.create(diretoria_regional=self.dre)
        self.escola_cmct = escola_factory.create(
            nome="CMCT VALDYR",
            tipo_gestao__nome="TERC TOTAL",
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_usuario_escola(self, usuario_factory, vinculo_factory):
        self.usuario_escola = usuario_factory.create()
        self.vinculo_escola_diretor = vinculo_factory.create(
            usuario=self.usuario_escola,
            object_id=self.escola_cmct.id,
            instituicao=self.escola_cmct,
            perfil__nome="DIRETOR_UE",
            data_inicial="2025-09-01",
            data_final=None,
            ativo=True,
        )

    def _setup_inclusao_normal(
        self,
        grupo_inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_normal_factory,
        quantidade_por_periodo_factory,
        log_solicitacoes_usuario_factory,
    ):
        self.grupo_inclusao_alimentacao_normal = (
            grupo_inclusao_alimentacao_normal_factory.create(
                escola=self.escola_cmct,
                rastro_lote=self.lote,
                rastro_dre=self.dre,
                rastro_escola=self.escola_cmct,
                status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
            )
        )
        inclusao_alimentacao_normal_factory.create(
            data="2025-09-03",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        inclusao_alimentacao_normal_factory.create(
            data="2025-09-04",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        inclusao_alimentacao_normal_factory.create(
            data="2025-09-05",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        quantidade_por_periodo_factory.create(
            grupo_inclusao_normal=self.grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
            periodo_escolar=self.periodo_manha,
            numero_alunos=100,
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.grupo_inclusao_alimentacao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )

    def _setup_inclusao_continua(
        self,
        motivo_inclusao_continua_factory,
        inclusao_continua_factory,
        quantidade_por_periodo_factory,
        log_solicitacoes_usuario_factory,
    ):
        self.motivo_inclusao_continua = motivo_inclusao_continua_factory.create(
            nome="Programas e Projetos"
        )
        self.inclusao_continua = inclusao_continua_factory.create(
            escola=self.escola_cmct,
            motivo=self.motivo_inclusao_continua,
            rastro_escola=self.escola_cmct,
            rastro_lote=self.lote,
            rastro_dre=self.dre,
            rastro_terceirizada=self.escola_cmct.lote.terceirizada,
            data_inicial=datetime.date(2025, 9, 1),
            data_final=datetime.date(2025, 9, 30),
            status="CODAE_AUTORIZADO",
        )
        quantidade_por_periodo_factory.create(
            numero_alunos=10,
            periodo_escolar=self.periodo_manha,
            inclusao_alimentacao_continua=self.inclusao_continua,
            dias_semana=[1, 2, 3, 4, 5],
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario_escola,
        )

    def _setup_medicao_inicial(self, solicitacao_medicao_inicial_factory):
        self.solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create(
            escola=self.escola_cmct, mes="09", ano="2025"
        )

    def _setup_medicao_manha(self, medicao_factory):
        self.medicao_manha = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=self.periodo_manha,
            grupo=None,
        )

    def _setup_medicao_programas_projetos(self, medicao_factory):
        self.medicao_programas_projetos = medicao_factory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=None,
            grupo__nome="Programas e Projetos",
        )

    def _setup_logs_medicao_dieta_manha(
        self, log_quantidade_dietas_autorizadas_factory, valor_medicao_factory
    ):
        for i in range(1, 31):
            log_quantidade_dietas_autorizadas_factory.create(
                escola=self.escola_cmct,
                quantidade=10,
                classificacao=self.classificacao_tipo_a,
                periodo_escolar=None,
                data=datetime.date(2025, 9, i),
            )
            valor_medicao_factory.create(
                dia=f"{i:02d}",
                valor="10",
                nome_campo="dietas_autorizadas",
                medicao=self.medicao_manha,
                categoria_medicao=self.categoria_medicao_dieta_tipo_a,
                faixa_etaria=None,
            )

    def _setup_logs_medicao_inclusao_continua(
        self, valor_medicao_factory, dia_calendario_factory
    ):
        for i in range(1, 31):
            valor_medicao_factory.create(
                dia=f"{i:02d}",
                valor="10",
                nome_campo="numero_de_alunos",
                medicao=self.medicao_programas_projetos,
                categoria_medicao=self.categoria_alimentacao,
                faixa_etaria=None,
            )
            dia_calendario_factory.create(
                escola=self.escola_cmct, data=datetime.date(2025, 9, i), dia_letivo=True
            )

    @freeze_time("2025-09-01")
    def test_validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        classificacao_dieta_factory,
        periodo_escolar_factory,
        log_quantidade_dietas_autorizadas_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        grupo_inclusao_alimentacao_normal_factory,
        quantidade_por_periodo_factory,
        inclusao_alimentacao_normal_factory,
        log_solicitacoes_usuario_factory,
        usuario_factory,
        vinculo_factory,
    ):
        self._setup_core(
            periodo_escolar_factory,
            classificacao_dieta_factory,
            categoria_medicao_factory,
        )
        self._setup_escola_cmct(
            diretoria_regional_factory, lote_factory, escola_factory
        )
        self._setup_usuario_escola(usuario_factory, vinculo_factory)
        self._setup_inclusao_normal(
            grupo_inclusao_alimentacao_normal_factory,
            inclusao_alimentacao_normal_factory,
            quantidade_por_periodo_factory,
            log_solicitacoes_usuario_factory,
        )
        self._setup_medicao_inicial(solicitacao_medicao_inicial_factory)
        self._setup_medicao_manha(medicao_factory)
        self._setup_logs_medicao_dieta_manha(
            log_quantidade_dietas_autorizadas_factory, valor_medicao_factory
        )

        lista_erros = []
        lista_erros = validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares(
            self.solicitacao_medicao_inicial, lista_erros
        )
        assert lista_erros == [
            {
                "erro": "Restam dias a serem lançados nas dietas.",
                "periodo_escolar": "MANHA",
            }
        ]

    @freeze_time("2025-09-01")
    def test_validate_solicitacoes_programas_e_projetos_escola_sem_alunos_regulares(
        self,
        escola_factory,
        lote_factory,
        diretoria_regional_factory,
        solicitacao_medicao_inicial_factory,
        classificacao_dieta_factory,
        periodo_escolar_factory,
        valor_medicao_factory,
        medicao_factory,
        categoria_medicao_factory,
        motivo_inclusao_continua_factory,
        quantidade_por_periodo_factory,
        inclusao_alimentacao_continua_factory,
        usuario_factory,
        vinculo_factory,
        log_solicitacoes_usuario_factory,
        dia_calendario_factory,
    ):
        self._setup_core(
            periodo_escolar_factory,
            classificacao_dieta_factory,
            categoria_medicao_factory,
        )
        self._setup_escola_cmct(
            diretoria_regional_factory, lote_factory, escola_factory
        )
        self._setup_usuario_escola(usuario_factory, vinculo_factory)
        self._setup_inclusao_continua(
            motivo_inclusao_continua_factory,
            inclusao_alimentacao_continua_factory,
            quantidade_por_periodo_factory,
            log_solicitacoes_usuario_factory,
        )
        self._setup_medicao_inicial(solicitacao_medicao_inicial_factory)
        self._setup_medicao_programas_projetos(medicao_factory)
        self._setup_logs_medicao_inclusao_continua(
            valor_medicao_factory, dia_calendario_factory
        )

        lista_erros = []
        lista_erros = (
            validate_solicitacoes_programas_e_projetos_escola_sem_alunos_regulares(
                self.solicitacao_medicao_inicial, lista_erros
            )
        )
        assert lista_erros == [
            {
                "erro": "Restam dias a serem lançados nas alimentações.",
                "periodo_escolar": "Programas e Projetos",
            }
        ]
