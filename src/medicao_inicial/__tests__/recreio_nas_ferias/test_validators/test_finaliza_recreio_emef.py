import pytest
from model_bakery import baker

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    validate_lancamento_alimentacoes_medicao_recreio,
    validate_lancamento_dietas_medicao_recreio,
)

pytestmark = pytest.mark.django_db


def test_validate_lancamento_alimentacoes_medicao_recreio(solicitacao_recreio_emef):

    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_dados_nao_lancados(
    solicitacao_recreio_emef,
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="sobremesa",
        dia="17",
    )
    assert valores.count() == 2
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio(
        solicitacao_recreio_emef, lista_erros
    )
    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef):
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef, lista_erros)
    assert len(lista_erros) == 0


def test_validate_lancamento_dietas_medicao_recreio_dados_nao_lancados(
    solicitacao_recreio_emef, categoria_medicao_dieta_a_enteral_aminoacidos
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_emef,
        nome_campo="refeicao",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a_enteral_aminoacidos,
    )
    assert valores.count() == 1
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio(solicitacao_recreio_emef, lista_erros)
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias",
        }
    ]
