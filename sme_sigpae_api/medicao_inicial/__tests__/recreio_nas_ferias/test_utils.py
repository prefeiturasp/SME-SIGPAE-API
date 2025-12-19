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
