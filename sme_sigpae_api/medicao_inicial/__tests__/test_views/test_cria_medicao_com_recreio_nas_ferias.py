import pytest
from freezegun import freeze_time


@freeze_time("2025-12-08")
@pytest.mark.usefixtures("client_autenticado_da_escola", "escola")
class TestUseCaseCriaMedicaoInicialComRecreioNasFerias:
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
