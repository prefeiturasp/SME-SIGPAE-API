import pytest
from freezegun import freeze_time
from rest_framework import status

from src.medicao_inicial.models import SolicitacaoMedicaoInicial


@pytest.fixture
def setup_medicao_com_recreio(
    escola,
    tipo_contagem_alimentacao_factory,
    tipo_alimentacao_factory,
    categoria_alimentacao_factory,
    recreio_nas_ferias_factory,
    recreio_nas_ferias_unidade_participante_factory,
    recreio_nas_ferias_unidade_tipo_alimentacao_factory,
):
    """
    Monta o cenárioc completo do Recreio nas Férias:
    - Tipos de contagem
    - Tipos de alimentação
    - Categorias
    - Recreio nas Férias 2026
    - Unidade participante
    - Tipos de alimentação por categoria
    """

    class Contexto:
        pass

    contexto = Contexto()

    # Tipo contagem
    contexto.tipo_contagem = tipo_contagem_alimentacao_factory.create(nome="Catraca")

    # Tipos alimentação
    contexto.refeicao = tipo_alimentacao_factory.create(nome="Refeição")
    contexto.lanche = tipo_alimentacao_factory.create(nome="Lanche")
    contexto.sobremesa = tipo_alimentacao_factory.create(nome="Sobremesa")

    # Categorias
    contexto.inscritos = categoria_alimentacao_factory.create(nome="Inscritos")
    contexto.colaboradores = categoria_alimentacao_factory.create(nome="Colaboradores")

    # Recreio
    contexto.recreio = recreio_nas_ferias_factory.create(
        data_inicio="2026-01-07",
        data_fim="2026-01-23",
        titulo="Recreio nas Férias - Jan 2026",
    )

    # Unidade participante
    contexto.recreio_ue = recreio_nas_ferias_unidade_participante_factory.create(
        unidade_educacional=escola,
        lote=escola.lote,
        recreio_nas_ferias=contexto.recreio,
        num_inscritos=100,
        num_colaboradores=100,
        liberar_medicao=True,
    )

    # Tipos alimentação × categorias
    for tipo in [contexto.refeicao, contexto.lanche, contexto.sobremesa]:
        for categoria in [contexto.inscritos, contexto.colaboradores]:
            recreio_nas_ferias_unidade_tipo_alimentacao_factory.create(
                recreio_ferias_unidade=contexto.recreio_ue,
                tipo_alimentacao=tipo,
                categoria=categoria,
            )

    return contexto


@freeze_time("2025-12-08")
@pytest.mark.usefixtures(
    "client_autenticado_da_escola", "escola", "setup_medicao_com_recreio"
)
class TestUseCaseCriaMedicaoInicialComRecreioNasFerias:

    def test_cria_medicao_com_recreio_nas_ferias(
        self,
        client_autenticado_da_escola,
        escola,
        setup_medicao_com_recreio,
    ):
        contexto = setup_medicao_com_recreio

        data_create = {
            "ano": "2026",
            "mes": "01",
            "escola": str(escola.uuid),
            "responsaveis": [{"nome": "Fulano da Silva", "rf": "1234567"}],
            "tipo_contagem_alimentacoes": [str(contexto.tipo_contagem.uuid)],
            "recreio_nas_ferias": str(contexto.recreio.uuid),
        }

        response = client_autenticado_da_escola.post(
            "/medicao-inicial/solicitacao-medicao-inicial/",
            content_type="application/json",
            data=data_create,
        )

        assert response.status_code == status.HTTP_201_CREATED
        smi = SolicitacaoMedicaoInicial.objects.get()
        assert smi.recreio_nas_ferias == contexto.recreio

    def test_erro_medicao_com_recreio_nas_ferias_nao_esta_liberada(
        self,
        client_autenticado_da_escola,
        escola,
        setup_medicao_com_recreio,
    ):
        contexto = setup_medicao_com_recreio
        contexto.recreio_ue.liberar_medicao = False
        contexto.recreio_ue.save()

        data_create = {
            "ano": "2026",
            "mes": "01",
            "escola": str(escola.uuid),
            "responsaveis": [{"nome": "Fulano da Silva", "rf": "1234567"}],
            "tipo_contagem_alimentacoes": [str(contexto.tipo_contagem.uuid)],
            "recreio_nas_ferias": str(contexto.recreio.uuid),
        }

        response = client_autenticado_da_escola.post(
            "/medicao-inicial/solicitacao-medicao-inicial/",
            content_type="application/json",
            data=data_create,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "recreio_nas_ferias": ["A medição não está liberada para esta escola"]
        }

    def test_erro_medicao_com_recreio_nas_ferias_escola_nao_e_participante(
        self,
        client_autenticado_da_escola,
        escola,
        setup_medicao_com_recreio,
    ):
        contexto = setup_medicao_com_recreio
        contexto.recreio_ue.delete()

        data_create = {
            "ano": "2026",
            "mes": "01",
            "escola": str(escola.uuid),
            "responsaveis": [{"nome": "Fulano da Silva", "rf": "1234567"}],
            "tipo_contagem_alimentacoes": [str(contexto.tipo_contagem.uuid)],
            "recreio_nas_ferias": str(contexto.recreio.uuid),
        }

        response = client_autenticado_da_escola.post(
            "/medicao-inicial/solicitacao-medicao-inicial/",
            content_type="application/json",
            data=data_create,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "recreio_nas_ferias": ["A medição não está liberada para esta escola"]
        }

    def test_retrieve_retorna_apenas_unidade_da_escola_da_solicitacao(
        self,
        client_autenticado_diretoria_regional,
        escola,
        escola_factory,
        recreio_nas_ferias_unidade_participante_factory,
        solicitacao_medicao_inicial_factory,
        setup_medicao_com_recreio,
    ):
        contexto = setup_medicao_com_recreio
        outra_escola = escola_factory.create(
            diretoria_regional=escola.diretoria_regional,
        )

        contexto.recreio_ue.liberar_medicao = True
        contexto.recreio_ue.save()

        recreio_nas_ferias_unidade_participante_factory.create(
            unidade_educacional=outra_escola,
            lote=outra_escola.lote,
            recreio_nas_ferias=contexto.recreio,
            num_inscritos=50,
            num_colaboradores=10,
            liberar_medicao=True,
        )

        solicitacao = solicitacao_medicao_inicial_factory.create(
            escola=escola,
            recreio_nas_ferias=contexto.recreio,
            mes="03",
            ano="2026",
        )

        response = client_autenticado_diretoria_regional.get(
            f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/",
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["recreio_nas_ferias"]["unidades_participantes"]) == 1
        assert response.json()["recreio_nas_ferias"]["unidades_participantes"][0][
            "unidade_educacional"
        ]["uuid"] == str(escola.uuid)
