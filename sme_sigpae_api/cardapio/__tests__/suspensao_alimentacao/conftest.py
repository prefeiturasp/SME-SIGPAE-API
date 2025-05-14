import datetime

import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers import (
    SuspensaoAlimentacaoSerializer,
)
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


@pytest.fixture
def suspensao_alimentacao_serializer(suspensao_alimentacao):
    return SuspensaoAlimentacaoSerializer(suspensao_alimentacao)


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de, data para
        (
            datetime.date(2019, 12, 25),
            datetime.date(2020, 1, 10),
        ),  # deve ser no ano corrente
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 20),
        ),  # nao pode ser no passado
        (
            datetime.date(2019, 10, 17),
            datetime.date(2019, 12, 20),
        ),  # nao pode ter mais de 60 dias de intervalo
        (
            datetime.date(2019, 10, 31),
            datetime.date(2019, 10, 15),
        ),  # data de nao pode ser maior que data para
    ]
)
def grupo_suspensao_alimentacao_params(request):
    return request.param
