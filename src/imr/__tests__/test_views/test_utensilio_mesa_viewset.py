import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_get_utensilios_mesa_por_edital(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    utensilio_mesa_factory,
    edital_utensilio_mesa_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    utensilio_mesa_1 = utensilio_mesa_factory.create(
        nome="Caneca com alça em polipropileno"
    )
    utensilio_mesa_2 = utensilio_mesa_factory.create(nome="Mamadeira e seu bico 240ml")
    utensilio_mesa_3 = utensilio_mesa_factory.create(
        nome="Copo de vidro para oferta de leite materno"
    )
    edital_utensilio_mesa_factory.create(
        edital=edital,
        utensilios_mesa=(utensilio_mesa_1, utensilio_mesa_2, utensilio_mesa_3),
    )

    response = client.get(f"/imr/utensilios-mesa/?edital_uuid={edital.uuid}")

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
    assert (
        any(
            utensilio_mesa
            for utensilio_mesa in results
            if utensilio_mesa["nome"] == utensilio_mesa_1.nome
        )
        is True
    )
    assert (
        any(
            utensilio_mesa
            for utensilio_mesa in results
            if utensilio_mesa["nome"] == utensilio_mesa_2.nome
        )
        is True
    )
    assert (
        any(
            utensilio_mesa
            for utensilio_mesa in results
            if utensilio_mesa["nome"] == utensilio_mesa_3.nome
        )
        is True
    )
