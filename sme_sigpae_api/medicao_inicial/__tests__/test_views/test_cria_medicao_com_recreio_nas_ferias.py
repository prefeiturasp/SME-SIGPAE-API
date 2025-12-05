import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial


@freeze_time("2025-12-08")
@pytest.mark.usefixtures("client_autenticado_da_escola", "escola")
class TestUseCaseCriaMedicaoInicialComRecreioNasFerias:
    def _setup_tipos_contagem_alimentacao(self, tipo_contagem_alimentacao_factory):
        self.tipo_contagem_alimentacao_catraca = (
            tipo_contagem_alimentacao_factory.create(nome="Catraca")
        )

    def _setup_tipos_alimentacao(self, tipo_alimentacao_factory):
        self.tipo_alimentacao_refeicao = tipo_alimentacao_factory.create(
            nome="Refeição"
        )
        self.tipo_alimentacao_lanche = tipo_alimentacao_factory.create(nome="Lanche")
        self.tipo_alimentacao_sobremesa = tipo_alimentacao_factory.create(
            nome="Sobremesa"
        )

    def _setup_categorias_alimentacao(self, categoria_alimentacao_factory):
        self.categoria_alimentacao_inscritos = categoria_alimentacao_factory.create(
            nome="Inscritos"
        )
        self.categoria_alimentacao_colaboradores = categoria_alimentacao_factory.create(
            nome="Colaboradores"
        )

    def _setup_recreio_nas_ferias_jan_26(
        self,
        escola,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
    ):
        self.recreio_nas_ferias = recreio_nas_ferias_factory.create(
            data_inicio="2026-01-07",
            data_fim="2026-01-23",
            titulo="Recreio nas Férias - Jan 2026",
        )
        self.recreio_nas_ferias_ue_participante = (
            recreio_nas_ferias_unidade_participante_factory.create(
                unidade_educacional=escola,
                lote=escola.lote,
                recreio_nas_ferias=self.recreio_nas_ferias,
                num_inscritos=100,
                num_colaboradores=100,
                liberar_medicao=True,
            )
        )

        for tipo_alimentacao in [
            self.tipo_alimentacao_refeicao,
            self.tipo_alimentacao_lanche,
            self.tipo_alimentacao_sobremesa,
        ]:
            for categoria in [
                self.categoria_alimentacao_inscritos,
                self.categoria_alimentacao_colaboradores,
            ]:
                recreio_nas_ferias_unidade_tipo_alimentacao_factory.create(
                    recreio_ferias_unidade=self.recreio_nas_ferias_ue_participante,
                    tipo_alimentacao=tipo_alimentacao,
                    categoria=categoria,
                )

    def _setup(
        self,
        escola,
        tipo_contagem_alimentacao_factory,
        tipo_alimentacao_factory,
        categoria_alimentacao_factory,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
    ):
        self._setup_tipos_contagem_alimentacao(tipo_contagem_alimentacao_factory)
        self._setup_tipos_alimentacao(tipo_alimentacao_factory)
        self._setup_categorias_alimentacao(categoria_alimentacao_factory)
        self._setup_recreio_nas_ferias_jan_26(
            escola,
            recreio_nas_ferias_factory,
            recreio_nas_ferias_unidade_participante_factory,
            recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        )

    def test_cria_medicao_com_recreio_nas_ferias(
        self,
        client_autenticado_da_escola,
        escola,
        tipo_contagem_alimentacao_factory,
        tipo_alimentacao_factory,
        categoria_alimentacao_factory,
        recreio_nas_ferias_factory,
        recreio_nas_ferias_unidade_participante_factory,
        recreio_nas_ferias_unidade_tipo_alimentacao_factory,
    ):
        self._setup(
            escola,
            tipo_contagem_alimentacao_factory,
            tipo_alimentacao_factory,
            categoria_alimentacao_factory,
            recreio_nas_ferias_factory,
            recreio_nas_ferias_unidade_participante_factory,
            recreio_nas_ferias_unidade_tipo_alimentacao_factory,
        )
        data_create = {
            "ano": "2026",
            "mes": "01",
            "escola": str(escola.uuid),
            "responsaveis": [{"nome": "Fulano da Silva", "rf": "1234567"}],
            "tipo_contagem_alimentacoes": [
                str(self.tipo_contagem_alimentacao_catraca.uuid)
            ],
            "recreio_nas_ferias": str(self.recreio_nas_ferias.uuid),
        }
        response = client_autenticado_da_escola.post(
            "/medicao-inicial/solicitacao-medicao-inicial/",
            content_type="application/json",
            data=data_create,
        )
        assert response.status_code == status.HTTP_201_CREATED
        solicitacao_medicao_inicial = SolicitacaoMedicaoInicial.objects.get()
        assert solicitacao_medicao_inicial.recreio_nas_ferias == self.recreio_nas_ferias
