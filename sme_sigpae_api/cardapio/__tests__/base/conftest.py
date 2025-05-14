import datetime

import pytest
from model_mommy import mommy


@pytest.fixture
def label_tipos_alimentacao():
    model = mommy.make("SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE")
    tipo_vegetariano = mommy.make("TipoAlimentacao", nome="Vegetariano")
    tipo_vegano = mommy.make("TipoAlimentacao", nome="Vegano")
    return model, tipo_vegetariano, tipo_vegano


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (datetime.time(10, 29), datetime.time(11, 29), True),
        (datetime.time(7, 10), datetime.time(7, 30), True),
        (datetime.time(6, 0), datetime.time(6, 10), True),
        (datetime.time(23, 30), datetime.time(23, 59), True),
        (datetime.time(20, 0), datetime.time(20, 22), True),
        (datetime.time(11, 0), datetime.time(13, 0), True),
        (datetime.time(15, 3), datetime.time(15, 21), True),
    ]
)
def horarios_combos_tipo_alimentacao_validos(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (
            datetime.time(10, 29),
            datetime.time(9, 29),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(7, 10),
            datetime.time(6, 30),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(6, 0),
            datetime.time(5, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(23, 30),
            datetime.time(22, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(20, 0),
            datetime.time(19, 22),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(11, 0),
            datetime.time(11, 0),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(15, 3),
            datetime.time(12, 21),
            "Hora Inicio não pode ser maior do que hora final",
        ),
    ]
)
def horarios_combos_tipo_alimentacao_invalidos(request):
    return request.param
