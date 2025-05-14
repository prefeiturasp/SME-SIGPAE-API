import datetime

import pytest
from model_mommy import mommy


@pytest.fixture(
    params=[
        # data_create , data_update
        (datetime.date(2019, 10, 17), datetime.date(2019, 10, 18)),
    ]
)
def suspensao_alimentacao_cei_params(request):
    motivo = mommy.make(
        "cardapio.MotivoSuspensao",
        nome="outro",
        uuid="478b09e1-4c14-4e50-a446-fbc0af727a08",
    )

    data_create, data_update = request.param
    return motivo, data_create, data_update
