import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)


@pytest.fixture(
    params=[
        # data_create , data_update
        (datetime.date(2019, 10, 17), datetime.date(2019, 10, 18)),
    ]
)
def suspensao_alimentacao_cei_params(request):
    motivo = baker.make(
        "cardapio.MotivoSuspensao",
        nome="outro",
        uuid="478b09e1-4c14-4e50-a446-fbc0af727a08",
    )

    data_create, data_update = request.param
    return motivo, data_create, data_update


@pytest.fixture
def suspensao_alimentacao_de_cei(escola):
    motivo = baker.make(MotivoSuspensao, nome="Suspensão de aula")
    periodos_escolares = baker.make("escola.PeriodoEscolar", _quantity=2)
    return baker.make(
        SuspensaoAlimentacaoDaCEI,
        escola=escola,
        motivo=motivo,
        periodos_escolares=periodos_escolares,
        data=datetime.date(2020, 4, 20),
    )
