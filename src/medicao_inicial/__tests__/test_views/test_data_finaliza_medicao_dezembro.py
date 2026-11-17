import datetime

import pytest
from rest_framework import status

from src.medicao_inicial.models import DataFinalizaMedicaoDezembro

pytestmark = pytest.mark.django_db

URL = "/medicao-inicial/data-finaliza-medicao-dezembro/"


def test_retorna_data_para_finalizar_medicao_dezembro_para_escola(
    client_autenticado_da_escola,
):
    DataFinalizaMedicaoDezembro.objects.filter(pk=1).update(
        data=datetime.date(2026, 12, 15)
    )

    response = client_autenticado_da_escola.get(URL, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == "15/12/2026"


def test_retorna_data_nula_para_finalizar_medicao_dezembro_para_escola(
    client_autenticado_da_escola,
):
    DataFinalizaMedicaoDezembro.objects.filter(pk=1).update(data=None)

    response = client_autenticado_da_escola.get(URL, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] is None


def test_nao_permite_acesso_de_usuario_que_nao_e_escola(
    client_autenticado_coordenador_codae,
):
    response = client_autenticado_coordenador_codae.get(
        URL, content_type="application/json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
