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
    FaixaEtariaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.inclusao_alimentacao.fixtures.factories.base_factory import (
    DiasMotivosInclusaoDeAlimentacaoCEIFactory,
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoContinuaFactory,
    InclusaoAlimentacaoDaCEIFactory,
    InclusaoAlimentacaoNormalFactory,
    MotivoInclusaoContinuaFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory,
    QuantidadePorPeriodoFactory,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoDaCEI,
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
    def _setup_dre_terc_lote(self):
        self.dre = DiretoriaRegionalFactory.create(nome="IPIRANGA", iniciais="IP")
        self.terceirizada = EmpresaFactory.create(nome_fantasia="ORIGINAL LTDA")
        self.lote = LoteFactory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )

    def _setup_escola(self):
        self.tipo_unidade_emef = TipoUnidadeEscolarFactory.create(iniciais="EMEF")
        self.escola_emef = EscolaFactory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_escola_cei(self):
        self.tipo_unidade_cei_diret = TipoUnidadeEscolarFactory.create(
            iniciais="CEI DIRET"
        )
        self.escola_cei = EscolaFactory.create(
            nome="CEI DIRET GERALDA",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_cei_diret,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_terceirizada_nova(self):
        self.terceirizada_nova = EmpresaFactory.create(nome_fantasia="NOVA LTDA")

    def _setup_usuario(self):
        self.usuario = UsuarioFactory.create(email="system@admin.com")

    def _setup_periodos_escolares(self):
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

    def _setup_tipos_alimentacao(self):
        self.tipo_alimentacao_refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        self.tipo_alimentacao_lanche = TipoAlimentacaoFactory.create(nome="Lanche")

    def _setup_motivos_inclusao_continua(self):
        self.motivo_programas_projetos = MotivoInclusaoContinuaFactory.create(
            nome="Programas e Projetos"
        )

    def _setup_inclusao_continua_programas_projetos(self):
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

    def _setup_testes(self):
        self._setup_dre_terc_lote()
        self._setup_escola()
        self._setup_escola_cei()
        self._setup_terceirizada_nova()
        self._setup_usuario()
        self._setup_periodos_escolares()
        self._setup_tipos_alimentacao()

    def _setup_inclusao_continua(self):
        self._setup_motivos_inclusao_continua()
        self._setup_inclusao_continua_programas_projetos()

    def _setup_inclusao_normal(
        self,
    ):
        self.grupo_inclusao_alimentacao_normal = (
            GrupoInclusaoAlimentacaoNormalFactory.create(
                escola=self.escola_emef,
                rastro_lote=self.lote,
                rastro_dre=self.dre,
                rastro_escola=self.escola_emef,
                rastro_terceirizada=self.terceirizada,
                status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            )
        )
        InclusaoAlimentacaoNormalFactory.create(
            data="2025-05-03",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        InclusaoAlimentacaoNormalFactory.create(
            data="2025-05-13",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        InclusaoAlimentacaoNormalFactory.create(
            data="2025-05-23",
            grupo_inclusao=self.grupo_inclusao_alimentacao_normal,
        )
        QuantidadePorPeriodoFactory.create(
            grupo_inclusao_normal=self.grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
            periodo_escolar=self.periodo_manha,
            numero_alunos=100,
            tipos_alimentacao=[self.tipo_alimentacao_lanche],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.grupo_inclusao_alimentacao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.grupo_inclusao_alimentacao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.grupo_inclusao_alimentacao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def _setup_faixas_etarias(self):
        self.faixa_etaria_1 = FaixaEtariaFactory.create(inicio=0, fim=1)
        self.faixa_etaria_2 = FaixaEtariaFactory.create(inicio=1, fim=4)

    def _setup_inclusao_cei(self):
        self.inclusao_alimentacao_da_cei = InclusaoAlimentacaoDaCEIFactory.create(
            escola=self.escola_cei,
            rastro_dre=self.escola_cei.diretoria_regional,
            rastro_lote=self.escola_cei.lote,
            rastro_terceirizada=self.terceirizada,
            status=InclusaoAlimentacaoDaCEI.workflow_class.CODAE_AUTORIZADO,
        )
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory.create(
            inclusao_alimentacao_da_cei=self.inclusao_alimentacao_da_cei,
            faixa_etaria=self.faixa_etaria_1,
            periodo=self.periodo_integral,
            quantidade_alunos=10,
        )
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory.create(
            inclusao_alimentacao_da_cei=self.inclusao_alimentacao_da_cei,
            faixa_etaria=self.faixa_etaria_2,
            periodo=self.periodo_integral,
            quantidade_alunos=20,
        )
        DiasMotivosInclusaoDeAlimentacaoCEIFactory.create(
            inclusao_cei=self.inclusao_alimentacao_da_cei, data="2025-05-03"
        )
        DiasMotivosInclusaoDeAlimentacaoCEIFactory.create(
            inclusao_cei=self.inclusao_alimentacao_da_cei, data="2025-05-13"
        )
        DiasMotivosInclusaoDeAlimentacaoCEIFactory.create(
            inclusao_cei=self.inclusao_alimentacao_da_cei, data="2025-05-23"
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_da_cei.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_da_cei.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_da_cei.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def test_transferir_lote_inclusao_continua_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_inclusao_continua()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_inclusoes_continuas(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        ultimo_dia_terceirizada_antiga = datetime.date(2025, 5, 12)

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

    def test_transferir_lote_inclusao_normal_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_inclusao_normal()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_inclusoes_normais(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        inclusoes_normais = (
            self.lote.inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote.all()
        )
        assert inclusoes_normais.count() == 2

        inclusao_original = inclusoes_normais.get(
            uuid=self.grupo_inclusao_alimentacao_normal.uuid
        )
        assert inclusao_original.inclusoes.count() == 1
        datas_original = list(
            inclusao_original.inclusoes.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 3) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        inclusao_copia = inclusoes_normais.exclude(
            uuid=self.grupo_inclusao_alimentacao_normal.uuid
        ).get()
        assert inclusao_copia.rastro_terceirizada == self.terceirizada_nova
        assert inclusao_copia.quantidades_periodo.count() == 1
        assert inclusao_copia.quantidades_periodo.get().tipos_alimentacao.count() == 1
        assert inclusao_copia.inclusoes.count() == 2
        datas_copia = list(inclusao_copia.inclusoes.values_list("data", flat=True))
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 23) in datas_copia
        assert inclusao_copia.logs.count() == 3

    def test_transferir_lote_inclusao_cei_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_faixas_etarias()
        self._setup_inclusao_cei()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_inclusoes_cei(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        inclusoes_cei = (
            self.lote.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote.all()
        )
        assert inclusoes_cei.count() == 2

        inclusao_original = inclusoes_cei.get(
            uuid=self.inclusao_alimentacao_da_cei.uuid
        )
        assert inclusao_original.dias_motivos_da_inclusao_cei.count() == 1
        datas_original = list(
            inclusao_original.dias_motivos_da_inclusao_cei.values_list(
                "data", flat=True
            )
        )
        assert datetime.date(2025, 5, 3) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        inclusao_copia = inclusoes_cei.exclude(
            uuid=self.inclusao_alimentacao_da_cei.uuid
        ).get()
        assert inclusao_copia.rastro_terceirizada == self.terceirizada_nova
        assert inclusao_copia.quantidade_alunos_da_inclusao.count() == 2
        assert (
            inclusao_copia.quantidade_alunos_da_inclusao.first().faixa_etaria
            is not None
        )
        assert inclusao_copia.dias_motivos_da_inclusao_cei.count() == 2
        datas_copia = list(
            inclusao_copia.dias_motivos_da_inclusao_cei.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 23) in datas_copia
        assert inclusao_copia.logs.count() == 3
