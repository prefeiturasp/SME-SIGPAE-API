import datetime
import json

import pytest
from rest_framework import status

from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
)
from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    PeriodoEscolarFactory,
)
from sme_sigpae_api.inclusao_alimentacao.fixtures.factories.base_factory import (
    InclusaoAlimentacaoContinuaFactory,
    MotivoInclusaoContinuaFactory,
    QuantidadePorPeriodoFactory,
)
from sme_sigpae_api.kit_lanche.fixtures.factories.base_factory import (
    SolicitacaoKitLancheAvulsaFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.base_factory import (
    GrupoMedicaoFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    MedicaoFactory,
    SolicitacaoMedicaoInicialFactory,
    ValorMedicaoFactory,
)
from sme_sigpae_api.medicao_inicial.models import GrupoMedicao
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_da_escola", "escola")
class TestUseCaseFinalizaMedicaoSemLancamentos:
    def setup_usuario(self):
        self.usuario = UsuarioFactory.create(email="system@admin.com")

    def setup_periodos_escolares(self):
        self.periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")

    def setup_tipos_alimentacao(self):
        self.tipo_alimentacao_refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        self.tipo_alimentacao_lanche = TipoAlimentacaoFactory.create(nome="Lanche")

    def setup_motivos_inclusao_continua(self):
        self.motivo_programas_projetos = MotivoInclusaoContinuaFactory.create(
            nome="Programas e Projetos"
        )
        self.motivo_etec = MotivoInclusaoContinuaFactory.create(nome="ETEC")

    def setup_inclusao_continua_programas_projetos(self, escola):
        self.inclusao_continua = InclusaoAlimentacaoContinuaFactory.create(
            escola=escola,
            rastro_escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.lote.diretoria_regional,
            rastro_terceirizada=escola.lote.terceirizada,
            data_inicial="2025-05-01",
            data_final="2025-05-31",
            status="CODAE_AUTORIZADO",
            motivo=self.motivo_programas_projetos,
        )
        QuantidadePorPeriodoFactory.create(
            inclusao_alimentacao_continua=self.inclusao_continua,
            periodo_escolar=self.periodo_integral,
            grupo_inclusao_normal=None,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            criado_em=datetime.datetime.now(),
            usuario=self.usuario,
        )

    def setup_medicao_inicial(self, escola):
        self.solicitacao_medicao_inicial = SolicitacaoMedicaoInicialFactory.create(
            escola=escola, mes="05", ano="2025"
        )

    def get_or_create_grupo(self, nome):
        try:
            return GrupoMedicao.objects.get(nome=nome)
        except GrupoMedicao.DoesNotExist:
            return GrupoMedicaoFactory.create(nome=nome)

    def setup_grupos_medicao(self):
        self.grupo_programas_projetos = self.get_or_create_grupo("Programas e Projetos")
        self.grupo_solicitacoes_alimentacao = self.get_or_create_grupo(
            "Solicitações de Alimentação"
        )

    def setup_medicao_programas_projetos_com_observacao(self):
        self.medicao = MedicaoFactory.create(
            solicitacao_medicao_inicial=self.solicitacao_medicao_inicial,
            periodo_escolar=None,
            grupo=self.grupo_programas_projetos,
        )
        ValorMedicaoFactory.create(
            medicao=self.medicao,
            nome_campo="observacoes",
            dia="02",
            valor="Não tem aula nesse mês.",
        )

    def setup_kit_lanche(self, escola):
        self.kit_lanche = SolicitacaoKitLancheAvulsaFactory.create(
            solicitacao_kit_lanche__data="2025-05-15",
            escola=escola,
            rastro_escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.lote.diretoria_regional,
            rastro_terceirizada=escola.lote.terceirizada,
            quantidade_alunos=100,
            status="CODAE_AUTORIZADO",
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.kit_lanche.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            criado_em=datetime.datetime.now(),
            usuario=self.usuario,
        )

    def setup_testes(self, escola):
        self.setup_usuario()
        self.setup_periodos_escolares()
        self.setup_tipos_alimentacao()
        self.setup_motivos_inclusao_continua()
        self.setup_grupos_medicao()
        self.setup_inclusao_continua_programas_projetos(escola)
        self.setup_medicao_inicial(escola)

    def test_finaliza_medicao_sem_lancamentos_erro_programas_e_projetos(
        self, client_autenticado_da_escola, escola
    ):
        self.setup_testes(escola)
        data_update = {
            "escola": str(escola.uuid),
            "com_ocorrencias": False,
            "finaliza_medicao": True,
            "justificativa_sem_lancamentos": "sem aula nesse mês.",
        }
        response = client_autenticado_da_escola.patch(
            f"/medicao-inicial/solicitacao-medicao-inicial/{self.solicitacao_medicao_inicial.uuid}/",
            content_type="application/json",
            data=json.dumps(data_update),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                "periodo_escolar": "Programas e Projetos",
                "erro": "Existem solicitações de alimentações no período, adicione ao menos uma justificativa para finalizar",
            }
        ]

    def test_finaliza_medicao_sem_lancamentos_programas_e_projetos_possui_observacoes(
        self, client_autenticado_da_escola, escola
    ):
        self.setup_testes(escola)
        self.setup_medicao_programas_projetos_com_observacao()
        data_update = {
            "escola": str(escola.uuid),
            "com_ocorrencias": False,
            "finaliza_medicao": True,
            "justificativa_sem_lancamentos": "sem aula nesse mês.",
        }
        response = client_autenticado_da_escola.patch(
            f"/medicao-inicial/solicitacao-medicao-inicial/{self.solicitacao_medicao_inicial.uuid}/",
            content_type="application/json",
            data=json.dumps(data_update),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_finaliza_medicao_sem_lancamentos_erro_kit_lanche_nao_pode_finalizar(
        self, client_autenticado_da_escola, escola
    ):
        self.setup_testes(escola)
        self.setup_kit_lanche(escola)
        data_update = {
            "escola": str(escola.uuid),
            "com_ocorrencias": False,
            "finaliza_medicao": True,
            "justificativa_sem_lancamentos": "sem aula nesse mês.",
        }
        response = client_autenticado_da_escola.patch(
            f"/medicao-inicial/solicitacao-medicao-inicial/{self.solicitacao_medicao_inicial.uuid}/",
            content_type="application/json",
            data=json.dumps(data_update),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Existem solicitações de alimentações no período. Não é possível finalizar sem lançamentos.",
            },
            {
                "periodo_escolar": "Programas e Projetos",
                "erro": "Existem solicitações de alimentações no período, adicione ao menos uma justificativa para finalizar",
            },
        ]
