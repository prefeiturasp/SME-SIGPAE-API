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
from sme_sigpae_api.kit_lanche.fixtures.factories.base_factory import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsaFactory,
    SolicitacaoKitLancheCEIAvulsaFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.base_factory import (
    GrupoMedicaoFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    SolicitacaoMedicaoInicialFactory,
)
from sme_sigpae_api.medicao_inicial.models import GrupoMedicao
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_da_escola_cei", "escola_cei")
class TestUseCaseFinalizaMedicaoSemLancamentosCEI:
    def setup_usuario(self):
        self.usuario = UsuarioFactory.create(email="system@admin.com")

    def setup_periodos_escolares(self):
        self.periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")

    def setup_tipos_alimentacao(self):
        self.tipo_alimentacao_refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        self.tipo_alimentacao_lanche = TipoAlimentacaoFactory.create(nome="Lanche")

    def setup_medicao_inicial(self, escola_cei):
        self.solicitacao_medicao_inicial = SolicitacaoMedicaoInicialFactory.create(
            escola=escola_cei, mes="05", ano="2025"
        )

    def get_or_create_grupo(self, nome):
        try:
            return GrupoMedicao.objects.get(nome=nome)
        except GrupoMedicao.DoesNotExist:
            return GrupoMedicaoFactory.create(nome=nome)

    def setup_grupos_medicao(self):
        self.grupo_solicitacoes_alimentacao = self.get_or_create_grupo(
            "Solicitações de Alimentação"
        )

    def setup_kit_lanche(self, escola_cei):
        self.kit_lanche = SolicitacaoKitLancheCEIAvulsaFactory.create(
            solicitacao_kit_lanche__data="2025-05-15",
            escola=escola_cei,
            rastro_escola=escola_cei,
            rastro_lote=escola_cei.lote,
            rastro_dre=escola_cei.lote.diretoria_regional,
            rastro_terceirizada=escola_cei.lote.terceirizada,
            status="CODAE_AUTORIZADO",
        )
        FaixaEtariaSolicitacaoKitLancheCEIAvulsaFactory.create(
            solicitacao_kit_lanche_avulsa=self.kit_lanche
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
        self.setup_grupos_medicao()
        self.setup_medicao_inicial(escola)

    def test_finaliza_medicao_sem_lancamentos_erro_solicitacoes_alimentacao(
        self, client_autenticado_da_escola_cei, escola_cei
    ):
        self.setup_testes(escola_cei)
        self.setup_kit_lanche(escola_cei)
        data_update = {
            "escola": str(escola_cei.uuid),
            "com_ocorrencias": False,
            "finaliza_medicao": True,
            "justificativa_sem_lancamentos": "sem aula nesse mês.",
        }
        response = client_autenticado_da_escola_cei.patch(
            f"/medicao-inicial/solicitacao-medicao-inicial/{self.solicitacao_medicao_inicial.uuid}/",
            content_type="application/json",
            data=json.dumps(data_update),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Existem solicitações de alimentações no período. Não é possível finalizar sem lançamentos.",
            }
        ]
