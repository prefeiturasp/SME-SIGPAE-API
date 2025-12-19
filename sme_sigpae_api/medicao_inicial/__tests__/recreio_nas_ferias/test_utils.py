import datetime

import pytest

from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.utils import (
    gerar_calendario_recreio,
    gerar_dias_letivos_recreio,
)

pytestmark = pytest.mark.django_db


def test_gerar_dias_letivos_recreio_periodo_completo(recreio_nas_ferias):
    resultado = gerar_dias_letivos_recreio(
        recreio_nas_ferias.data_inicio, recreio_nas_ferias.data_fim
    )
    assert resultado == [10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 26, 29, 30]


def test_gerar_dias_letivos_recreio_periodo_somente_fins_de_semana():
    inicio = datetime.date(2025, 12, 13)
    fim = datetime.date(2025, 12, 14)
    resultado = gerar_dias_letivos_recreio(inicio, fim)
    assert resultado == []


def test_gerar_dias_letivos_recreio_periodo_unico_dia():
    data = datetime.date(2025, 12, 4)
    resultado = gerar_dias_letivos_recreio(data, data)
    assert resultado == [4]


def test_gerar_dias_letivos_recreio_periodo_cruzando_meses_exception():
    inicio = datetime.date(2025, 12, 29)
    fim = datetime.date(2026, 1, 10)
    with pytest.raises(
        ValueError, match="O início e o fim do recreio devem estar no mesmo mês."
    ):
        gerar_dias_letivos_recreio(inicio, fim)


def test_gerar_dias_letivos_recreio_mes_com_feriado():
    inicio = datetime.date(2025, 11, 1)
    fim = datetime.date(2025, 11, 30)
    resultado = gerar_dias_letivos_recreio(inicio, fim)
    assert 15 not in resultado
    assert 20 not in resultado

    inicio = datetime.date(2024, 11, 1)
    fim = datetime.date(2024, 11, 30)
    resultado = gerar_dias_letivos_recreio(inicio, fim)
    assert 15 not in resultado
    assert 20 not in resultado


def test_gerar_calendario_recreio_periodo_valido():
    inicio = datetime.date(2025, 12, 1)
    fim = datetime.date(2025, 12, 3)
    dias_letivos = [3]
    resultado = gerar_calendario_recreio(inicio, fim, dias_letivos)
    assert len(resultado) == 3

    assert resultado[0]["dia"] == "01"
    assert resultado[0]["data"] == "01/12/2025"
    assert resultado[0]["dia_letivo"] is False

    assert resultado[1]["dia"] == "02"
    assert resultado[1]["data"] == "02/12/2025"
    assert resultado[1]["dia_letivo"] is False

    assert resultado[2]["dia"] == "03"
    assert resultado[2]["data"] == "03/12/2025"
    assert resultado[2]["dia_letivo"] is True


def test_gerar_calendario_recreio_periodo_unico_dia():
    data = datetime.date(2025, 12, 4)
    dias_letivos = [4]
    resultado = gerar_calendario_recreio(data, data, dias_letivos)

    assert len(resultado) == 1
    assert resultado[0]["dia"] == "04"
    assert resultado[0]["data"] == "04/12/2025"
    assert resultado[0]["dia_letivo"] is True


def test_gerar_calendario_recreio_sem_dias_letivos():
    inicio = datetime.date(2025, 12, 1)
    fim = datetime.date(2025, 12, 10)
    dias_letivos = []
    resultado = gerar_calendario_recreio(inicio, fim, dias_letivos)
    for dia_info in resultado:
        assert dia_info["dia_letivo"] is False


def test_gerar_calendario_recreio_dias_letivos_parciais():
    inicio = datetime.date(2025, 12, 1)
    fim = datetime.date(2025, 12, 5)
    dias_letivos = [1, 4, 5]

    resultado = gerar_calendario_recreio(inicio, fim, dias_letivos)
    dias_letivos_set = set(dias_letivos)
    for dia_info in resultado:
        dia_numero = int(dia_info["dia"])
        if dia_numero in dias_letivos_set:
            assert dia_info["dia_letivo"] is True
        else:
            assert dia_info["dia_letivo"] is False


def test_gerar_calendario_recreio_periodo_invalido():
    """Testa comportamento com data final anterior à inicial"""
    inicio = datetime.date(2025, 12, 5)
    fim = datetime.date(2025, 12, 1)
    dias_letivos = [1, 2, 3, 4, 5]

    resultado = gerar_calendario_recreio(inicio, fim, dias_letivos)
    assert resultado == []


def test_gerar_calendario_recreio_estrutura_dados():
    inicio = datetime.date(2025, 12, 1)
    fim = datetime.date(2025, 12, 1)
    dias_letivos = [1]

    resultado = gerar_calendario_recreio(inicio, fim, dias_letivos)

    dia_info = resultado[0]
    assert "dia" in dia_info
    assert "data" in dia_info
    assert "dia_letivo" in dia_info

    assert isinstance(dia_info["dia"], str)
    assert isinstance(dia_info["data"], str)
    assert isinstance(dia_info["dia_letivo"], bool)
    assert len(dia_info["dia"]) == 2
    assert len(dia_info["data"]) == 10
    assert dia_info["data"][2] == "/"
    assert dia_info["data"][5] == "/"


def test_integracao_entre_funcoes():
    inicio = datetime.date(2025, 11, 1)
    fim = datetime.date(2025, 11, 30)
    dias_letivos = gerar_dias_letivos_recreio(inicio, fim)
    calendario = gerar_calendario_recreio(inicio, fim, dias_letivos)

    for dia_info in calendario:
        dia_numero = int(dia_info["dia"])
        if dia_info["dia_letivo"]:
            assert dia_numero in dias_letivos
        else:
            assert dia_numero not in dias_letivos
