import datetime

import pytest

from src.medicao_inicial.models import ValorMedicao
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cei_cci_cips import (
    indexar_logs_dieta_autorizadas_por_data,
    retorna_valor_para_log_dieta_autorizada_cei,
    validate_lancamento_alimentacoes_medicao_recreio_cei,
    validate_lancamento_dietas_medicao_recreio_cei,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    agrupar_tipos_alimentacao_por_categoria,
)

pytestmark = pytest.mark.django_db


def test_validate_lancamento_alimentacoes_medicao_recreio_cei(solicitacao_recreio_cei):

    lista_erros = []
    validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_recreio_cei_dados_nao_lancados(
    solicitacao_recreio_cei, categoria_medicao
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao,
    )
    assert valores.count() == 9
    valores.delete()
    lista_erros = []

    lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
        solicitacao_recreio_cei,
        lista_erros,
    )

    assert len(lista_erros) == 2
    erros_esperados = [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Colaboradores",
        },
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "Recreio nas Férias",
        },
    ]

    for esperado in erros_esperados:
        assert esperado in lista_erros, f"Elemento {esperado} não encontrado"


def test_validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei):
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei, lista_erros)
    assert len(lista_erros) == 0


def test_validate_lancamento_dietas_medicao_recreio_cei_dados_nao_lancados(
    solicitacao_recreio_cei, categoria_medicao_dieta_a
):
    valores = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao_recreio_cei,
        nome_campo="frequencia",
        dia="17",
        categoria_medicao=categoria_medicao_dieta_a,
    )
    assert valores.count() == 8
    valores.delete()
    assert valores.count() == 0
    lista_erros = []
    validate_lancamento_dietas_medicao_recreio_cei(solicitacao_recreio_cei, lista_erros)
    assert len(lista_erros) == 1
    assert lista_erros == [
        {
            "erro": "Restam dias a serem lançados nas dietas.",
            "periodo_escolar": "Recreio nas Férias",
        }
    ]


def test_agrupar_tipos_alimentacao_por_categoria(solicitacao_recreio_cei):
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )

    resultado = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    assert resultado == {
        "Colaboradores": ["Refeição", "Sobremesa"],
        "Inscritos": ["Refeição", "Sobremesa", "Lanche", "Lanche 4h", "Almoço"],
    }


def test_retorna_valor_para_log_dieta_autorizada_cei(
    solicitacao_recreio_cei, categoria_medicao_dieta_a, faixas_etarias_ativas
):
    escola = solicitacao_recreio_cei.escola
    recreio = solicitacao_recreio_cei.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)
    data = datetime.date(2025, 12, 10)
    resultado = retorna_valor_para_log_dieta_autorizada_cei(
        categoria_medicao_dieta_a, logs_por_dia, data, faixas_etarias_ativas[1]
    )

    assert resultado == 3
