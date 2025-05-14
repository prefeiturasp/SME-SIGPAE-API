import datetime

import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    QuantidadePorPeriodoSuspensaoAlimentacao,
)


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 5), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 10), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 20), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 25), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 31), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 3), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 4), datetime.date(2019, 12, 31)),
    ]
)
def suspensao_alimentacao_parametros_mes(request):
    return request.param


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 4)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 5)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 6)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 7)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 8)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 9)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 10)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 11)),
    ]
)
def suspensao_alimentacao_parametros_semana(request):
    return request.param


@pytest.fixture
def quantidade_por_periodo_suspensao_alimentacao():
    return mommy.make(QuantidadePorPeriodoSuspensaoAlimentacao, numero_alunos=100)
