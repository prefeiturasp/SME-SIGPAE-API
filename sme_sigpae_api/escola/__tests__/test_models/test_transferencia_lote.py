import datetime

import pytest
from freezegun import freeze_time

from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
)
from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunosMatriculadosPeriodoEscolaFactory,
    DiretoriaRegionalFactory,
    EscolaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.inclusao_alimentacao.fixtures.factories.base_factory import (
    InclusaoAlimentacaoContinuaFactory,
    MotivoInclusaoContinuaFactory,
    QuantidadePorPeriodoFactory,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


@freeze_time("2025-05-09")
class TestUseCaseTransferenciaLotes:
    def setup_escola(self):
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="ORIGINAL LTDA")
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

    def setup_terceirizada_nova(self):
        self.terceirizada_nova = EmpresaFactory.create(nome_fantasia="NOVA LTDA")

    def setup_usuario(self):
        self.usuario = UsuarioFactory.create(email="system@admin.com")

    def setup_periodos_escolares(self):
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        LogAlunosMatriculadosPeriodoEscolaFactory.create(
            escola=self.escola_emef,
            periodo_escolar=self.periodo_integral,
            quantidade_alunos=100,
            tipo_turma="REGULAR",
        )
        AlunosMatriculadosPeriodoEscolaFactory.create(
            escola=self.escola_emef,
            periodo_escolar=self.periodo_integral,
            quantidade_alunos=100,
            tipo_turma="REGULAR",
        )

        self.periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        LogAlunosMatriculadosPeriodoEscolaFactory.create(
            escola=self.escola_emef,
            periodo_escolar=self.periodo_manha,
            quantidade_alunos=100,
            tipo_turma="REGULAR",
        )
        assert self.escola_emef.periodos_escolares().count() == 2

    def setup_tipos_alimentacao(self):
        self.tipo_alimentacao_refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        self.tipo_alimentacao_lanche = TipoAlimentacaoFactory.create(nome="Lanche")

    def setup_motivos_inclusao_continua(self):
        self.motivo_programas_projetos = MotivoInclusaoContinuaFactory.create(
            nome="Programas e Projetos"
        )

    def setup_inclusao_continua_programas_projetos(self):
        self.inclusao_continua = InclusaoAlimentacaoContinuaFactory.create(
            escola=self.escola_emef,
            rastro_escola=self.escola_emef,
            rastro_lote=self.escola_emef.lote,
            rastro_dre=self.escola_emef.lote.diretoria_regional,
            rastro_terceirizada=self.escola_emef.lote.terceirizada,
            data_inicial="2025-05-01",
            data_final="2025-05-31",
            status="CODAE_AUTORIZADO",
            motivo=self.motivo_programas_projetos,
        )
        QuantidadePorPeriodoFactory.create(
            inclusao_alimentacao_continua=self.inclusao_continua,
            periodo_escolar=self.periodo_integral,
            tipos_alimentacao=[
                self.tipo_alimentacao_lanche,
                self.tipo_alimentacao_refeicao,
            ],
            grupo_inclusao_normal=None,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            criado_em=datetime.datetime.now(),
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            criado_em=datetime.datetime.now(),
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            criado_em=datetime.datetime.now(),
            usuario=self.usuario,
        )

    def setup_testes(self):
        self.setup_escola()
        self.setup_terceirizada_nova()
        self.setup_usuario()
        self.setup_periodos_escolares()
        self.setup_tipos_alimentacao()

    def setup_inclusao_continua(self):
        self.setup_motivos_inclusao_continua()
        self.setup_inclusao_continua_programas_projetos()

    def test_transferir_lote_inclusao_continua_data_aprovada_pos_transferencia(self):
        self.setup_testes()
        self.setup_inclusao_continua()

        data_virada = datetime.date(2025, 5, 15)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_inclusoes_continuas(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        ultimo_dia_terceirizada_antiga = datetime.date(2025, 5, 14)

        inclusoes_continuas = (
            self.lote.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote.all()
        )
        assert inclusoes_continuas.count() == 2

        inclusao_original = inclusoes_continuas.get(uuid=self.inclusao_continua.uuid)
        assert inclusao_original.data_final == ultimo_dia_terceirizada_antiga
        assert inclusao_original.rastro_terceirizada == self.terceirizada

        inclusao_copia = inclusoes_continuas.exclude(
            uuid=self.inclusao_continua.uuid
        ).get()
        assert inclusao_copia.rastro_terceirizada == self.terceirizada_nova
        assert inclusao_copia.quantidades_periodo.count() == 1
        assert inclusao_copia.quantidades_periodo.get().tipos_alimentacao.count() == 2
        assert inclusao_copia.motivo == self.motivo_programas_projetos
        assert inclusao_copia.data_inicial == data_virada
        assert inclusao_copia.data_final == datetime.date(2025, 5, 31)
        assert inclusao_copia.logs.count() == 3
