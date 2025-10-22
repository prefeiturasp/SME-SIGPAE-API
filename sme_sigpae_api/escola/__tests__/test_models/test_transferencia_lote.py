import datetime

import pytest
from freezegun import freeze_time

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory import (
    AlteracaoCardapioFactory,
    DataIntervaloAlteracaoCardapioFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarFactory,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.fixtures.factories.alteracao_tipo_alimentacao_cemei_factory import (
    AlteracaoCardapioCEMEIFactory,
    DataIntervaloAlteracaoCardapioCEMEIFactory,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEIFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
)
from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.fixtures.factories.suspensao_alimentacao_factory import (
    GrupoSuspensaoAlimentacaoFactory,
    QuantidadePorPeriodoSuspensaoAlimentacaoFactory,
    SuspensaoAlimentacaoFactory,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
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
    DiasMotivosInclusaoDeAlimentacaoCEMEIFactory,
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoContinuaFactory,
    InclusaoAlimentacaoDaCEIFactory,
    InclusaoAlimentacaoNormalFactory,
    InclusaoDeAlimentacaoCEMEIFactory,
    MotivoInclusaoContinuaFactory,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory,
    QuantidadePorPeriodoFactory,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
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

    def _setup_escola_cemei(self):
        self.tipo_unidade_cemei = TipoUnidadeEscolarFactory.create(iniciais="CEMEI")
        self.escola_cemei = EscolaFactory.create(
            nome="CEMEI PELEGRINI",
            tipo_gestao__nome="TERC TOTAL",
            tipo_unidade=self.tipo_unidade_cemei,
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
        self.tipo_alimentacao_lanche_emergencial = TipoAlimentacaoFactory.create(
            nome="Lanche Emergencial"
        )

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
        self._setup_escola_cemei()
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

    def _setup_inclusao_cemei(self):
        self.inclusao_alimentacao_cemei = InclusaoDeAlimentacaoCEMEIFactory.create(
            escola=self.escola_cemei,
            rastro_escola=self.escola_cemei,
            rastro_lote=self.escola_cemei.lote,
            rastro_dre=self.escola_cemei.diretoria_regional,
            rastro_terceirizada=self.terceirizada,
            status=InclusaoDeAlimentacaoCEMEI.workflow_class.CODAE_AUTORIZADO,
        )
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=self.inclusao_alimentacao_cemei,
            faixa_etaria=self.faixa_etaria_1,
            matriculados_quando_criado=10,
            quantidade_alunos=10,
            periodo_escolar=self.periodo_integral,
        )
        QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=self.inclusao_alimentacao_cemei,
            matriculados_quando_criado=20,
            quantidade_alunos=20,
            periodo_escolar=self.periodo_manha,
            tipos_alimentacao=[self.tipo_alimentacao_refeicao],
        )
        DiasMotivosInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=self.inclusao_alimentacao_cemei,
            data="2025-05-03",
        )
        DiasMotivosInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=self.inclusao_alimentacao_cemei,
            data="2025-05-13",
        )
        DiasMotivosInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=self.inclusao_alimentacao_cemei,
            data="2025-05-23",
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_alimentacao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def _setup_alteracao_normal(self):
        self.alteracao_normal = AlteracaoCardapioFactory.create(
            escola=self.escola_emef,
            rastro_escola=self.escola_emef,
            rastro_dre=self.escola_emef.diretoria_regional,
            rastro_lote=self.escola_emef.lote,
            rastro_terceirizada=self.terceirizada,
            motivo__nome="Lanche Emergencial",
            data_inicial="2025-05-10",
            data_final="2025-05-17",
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
        )
        for dia in ["10", "11", "12", "13", "14", "15", "16", "17"]:
            DataIntervaloAlteracaoCardapioFactory.create(
                alteracao_cardapio=self.alteracao_normal,
                data=f"2025-05-{dia}",
            )
        SubstituicaoAlimentacaoNoPeriodoEscolarFactory.create(
            alteracao_cardapio=self.alteracao_normal,
            periodo_escolar=self.periodo_manha,
            tipos_alimentacao_de=[
                self.tipo_alimentacao_lanche,
                self.tipo_alimentacao_refeicao,
            ],
            tipos_alimentacao_para=[self.tipo_alimentacao_lanche_emergencial],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_normal.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def _setup_alteracao_cemei(self):
        self.alteracao_cemei = AlteracaoCardapioCEMEIFactory.create(
            escola=self.escola_cemei,
            rastro_escola=self.escola_cemei,
            rastro_dre=self.escola_cemei.diretoria_regional,
            rastro_lote=self.escola_cemei.lote,
            rastro_terceirizada=self.terceirizada,
            motivo__nome="Lanche Emergencial",
            data_inicial="2025-05-10",
            data_final="2025-05-17",
            status=AlteracaoCardapioCEMEI.workflow_class.CODAE_AUTORIZADO,
        )
        for dia in ["10", "11", "12", "13", "14", "15", "16", "17"]:
            DataIntervaloAlteracaoCardapioCEMEIFactory.create(
                alteracao_cardapio_cemei=self.alteracao_cemei,
                data=f"2025-05-{dia}",
            )
        self.substituicao_cemei_cei = (
            SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory.create(
                alteracao_cardapio=self.alteracao_cemei,
                periodo_escolar=self.periodo_manha,
                tipos_alimentacao_de=[
                    self.tipo_alimentacao_lanche,
                    self.tipo_alimentacao_refeicao,
                ],
                tipos_alimentacao_para=[self.tipo_alimentacao_lanche_emergencial],
            )
        )
        FaixaEtariaSubstituicaoAlimentacaoCEMEICEIFactory.create(
            substituicao_alimentacao=self.substituicao_cemei_cei,
            faixa_etaria=self.faixa_etaria_1,
            quantidade=100,
            matriculados_quando_criado=100,
        )
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory.create(
            alteracao_cardapio=self.alteracao_cemei,
            periodo_escolar=self.periodo_manha,
            tipos_alimentacao_de=[
                self.tipo_alimentacao_lanche,
                self.tipo_alimentacao_refeicao,
            ],
            tipos_alimentacao_para=[self.tipo_alimentacao_lanche_emergencial],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
            usuario=self.usuario,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_cemei.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=self.usuario,
        )

    def _setup_suspensao_normal(
        self,
    ):
        self.grupo_suspensao = GrupoSuspensaoAlimentacaoFactory.create(
            escola=self.escola_emef,
            rastro_lote=self.lote,
            rastro_dre=self.dre,
            rastro_escola=self.escola_emef,
            rastro_terceirizada=self.terceirizada,
            status=GrupoSuspensaoAlimentacao.workflow_class.INFORMADO,
        )
        SuspensaoAlimentacaoFactory.create(
            data="2025-05-03",
            grupo_suspensao=self.grupo_suspensao,
        )
        SuspensaoAlimentacaoFactory.create(
            data="2025-05-13",
            grupo_suspensao=self.grupo_suspensao,
        )
        SuspensaoAlimentacaoFactory.create(
            data="2025-05-23",
            grupo_suspensao=self.grupo_suspensao,
        )
        QuantidadePorPeriodoSuspensaoAlimentacaoFactory.create(
            grupo_suspensao=self.grupo_suspensao,
            periodo_escolar=self.periodo_manha,
            numero_alunos=100,
            tipos_alimentacao=[self.tipo_alimentacao_lanche],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.grupo_suspensao.uuid,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
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

    def test_transferir_lote_inclusao_cemei_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_faixas_etarias()
        self._setup_inclusao_cemei()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_inclusoes_cemei(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        inclusoes_cemei = (
            self.lote.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.all()
        )
        assert inclusoes_cemei.count() == 2

        inclusao_original = inclusoes_cemei.get(
            uuid=self.inclusao_alimentacao_cemei.uuid
        )
        assert inclusao_original.dias_motivos_da_inclusao_cemei.count() == 1
        datas_original = list(
            inclusao_original.dias_motivos_da_inclusao_cemei.values_list(
                "data", flat=True
            )
        )
        assert datetime.date(2025, 5, 3) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        inclusao_copia = inclusoes_cemei.exclude(
            uuid=self.inclusao_alimentacao_cemei.uuid
        ).get()
        assert inclusao_copia.rastro_terceirizada == self.terceirizada_nova
        assert inclusao_copia.quantidade_alunos_cei_da_inclusao_cemei.count() == 1
        assert (
            inclusao_copia.quantidade_alunos_cei_da_inclusao_cemei.get().faixa_etaria
            is not None
        )
        assert inclusao_copia.quantidade_alunos_emei_da_inclusao_cemei.count() == 1
        assert (
            inclusao_copia.quantidade_alunos_emei_da_inclusao_cemei.get().tipos_alimentacao.count()
            == 1
        )
        assert inclusao_copia.dias_motivos_da_inclusao_cemei.count() == 2
        datas_copia = list(
            inclusao_copia.dias_motivos_da_inclusao_cemei.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 23) in datas_copia
        assert inclusao_copia.logs.count() == 3

    def test_transferir_lote_alteracao_normal_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_alteracao_normal()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_alteracoes_normais(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        alteracoes_normais = self.lote.cardapio_alteracaocardapio_rastro_lote.all()
        assert alteracoes_normais.count() == 2

        alteracao_original = alteracoes_normais.get(uuid=self.alteracao_normal.uuid)
        assert alteracao_original.datas_intervalo.count() == 3  # 10, 11, 12
        datas_original = list(
            alteracao_original.datas_intervalo.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 10) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        ultimo_dia_terceirizada_antiga = datetime.date(2025, 5, 12)
        assert alteracao_original.data_final == ultimo_dia_terceirizada_antiga
        assert alteracao_original.rastro_terceirizada == self.terceirizada

        alteracao_copia = alteracoes_normais.exclude(
            uuid=self.alteracao_normal.uuid
        ).get()
        assert alteracao_copia.rastro_terceirizada == self.terceirizada_nova
        assert alteracao_copia.substituicoes_periodo_escolar.count() == 1
        assert (
            alteracao_copia.substituicoes_periodo_escolar.get().tipos_alimentacao_de.count()
            == 2
        )
        assert (
            alteracao_copia.substituicoes_periodo_escolar.get().tipos_alimentacao_para.count()
            == 1
        )
        assert alteracao_copia.datas_intervalo.count() == 5  # 13 pra frente
        datas_copia = list(
            alteracao_copia.datas_intervalo.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 17) in datas_copia
        assert alteracao_copia.logs.count() == 3

    def test_transferir_lote_alteracao_cemei_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_faixas_etarias()
        self._setup_alteracao_cemei()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_alteracoes_cemei(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        alteracoes_cemei = self.lote.cardapio_alteracaocardapiocemei_rastro_lote.all()
        assert alteracoes_cemei.count() == 2

        alteracao_original = alteracoes_cemei.get(uuid=self.alteracao_cemei.uuid)
        assert alteracao_original.datas_intervalo.count() == 3  # 10, 11, 12
        datas_original = list(
            alteracao_original.datas_intervalo.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 10) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        ultimo_dia_terceirizada_antiga = datetime.date(2025, 5, 12)
        assert alteracao_original.data_final == ultimo_dia_terceirizada_antiga
        assert alteracao_original.rastro_terceirizada == self.terceirizada

        alteracao_copia = alteracoes_cemei.exclude(uuid=self.alteracao_cemei.uuid).get()
        assert alteracao_copia.rastro_terceirizada == self.terceirizada_nova

        assert alteracao_copia.substituicoes_cemei_cei_periodo_escolar.count() == 1
        substituicao_cemei_cei = (
            alteracao_copia.substituicoes_cemei_cei_periodo_escolar.get()
        )
        assert substituicao_cemei_cei.faixas_etarias.count() == 1
        assert substituicao_cemei_cei.faixas_etarias.get().faixa_etaria is not None
        assert (
            substituicao_cemei_cei.faixas_etarias.get().matriculados_quando_criado
            == 100
        )
        assert substituicao_cemei_cei.tipos_alimentacao_de.count() == 2
        assert substituicao_cemei_cei.tipos_alimentacao_para.count() == 1

        assert alteracao_copia.substituicoes_cemei_emei_periodo_escolar.count() == 1
        assert (
            alteracao_copia.substituicoes_cemei_emei_periodo_escolar.get().tipos_alimentacao_de.count()
            == 2
        )
        assert (
            alteracao_copia.substituicoes_cemei_emei_periodo_escolar.get().tipos_alimentacao_para.count()
            == 1
        )

        assert alteracao_copia.datas_intervalo.count() == 5  # 13 pra frente
        datas_copia = list(
            alteracao_copia.datas_intervalo.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 17) in datas_copia
        assert alteracao_copia.logs.count() == 3

    def test_transferir_lote_suspensao_normal_data_aprovada_pos_transferencia(self):
        self._setup_testes()
        self._setup_suspensao_normal()

        data_virada = datetime.date(2025, 5, 13)
        terceirizada_pre_transferencia = self.terceirizada
        terceirizada_nova = self.terceirizada_nova

        self.lote._transferir_lote_lida_com_suspensoes_normais(
            data_virada, terceirizada_pre_transferencia, terceirizada_nova
        )

        suspensoes_normais = (
            self.lote.cardapio_gruposuspensaoalimentacao_rastro_lote.all()
        )
        assert suspensoes_normais.count() == 2

        suspensao_original = suspensoes_normais.get(uuid=self.grupo_suspensao.uuid)
        assert suspensao_original.suspensoes_alimentacao.count() == 1
        datas_original = list(
            suspensao_original.suspensoes_alimentacao.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 3) in datas_original
        assert datetime.date(2025, 5, 13) not in datas_original

        suspensao_copia = suspensoes_normais.exclude(
            uuid=self.grupo_suspensao.uuid
        ).get()
        assert suspensao_copia.rastro_terceirizada == self.terceirizada_nova
        assert suspensao_copia.quantidades_por_periodo.count() == 1
        assert (
            suspensao_copia.quantidades_por_periodo.get().tipos_alimentacao.count() == 1
        )
        assert suspensao_copia.suspensoes_alimentacao.count() == 2
        datas_copia = list(
            suspensao_copia.suspensoes_alimentacao.values_list("data", flat=True)
        )
        assert datetime.date(2025, 5, 13) in datas_copia
        assert datetime.date(2025, 5, 23) in datas_copia
        assert suspensao_copia.logs.count() == 1
