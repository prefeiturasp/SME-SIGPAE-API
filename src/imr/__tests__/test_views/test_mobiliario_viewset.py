import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_get_mobiliarios_por_edital(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    mobiliario_factory,
    edital_mobiliario_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    mobiliario_1 = mobiliario_factory.create(nome="Mesa de apoio inox")
    mobiliario_2 = mobiliario_factory.create(nome="Mesa de apoio madeira")
    mobiliario_3 = mobiliario_factory.create(nome="Outros")
    edital_mobiliario_factory.create(
        edital=edital, mobiliarios=(mobiliario_1, mobiliario_2, mobiliario_3)
    )

    response = client.get(f"/imr/mobiliarios/?edital_uuid={edital.uuid}")

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
    assert (
        any(
            mobiliario
            for mobiliario in results
            if mobiliario["nome"] == mobiliario_1.nome
        )
        is True
    )
    assert (
        any(
            mobiliario
            for mobiliario in results
            if mobiliario["nome"] == mobiliario_2.nome
        )
        is True
    )
    assert (
        any(
            mobiliario
            for mobiliario in results
            if mobiliario["nome"] == mobiliario_3.nome
        )
        is True
    )
