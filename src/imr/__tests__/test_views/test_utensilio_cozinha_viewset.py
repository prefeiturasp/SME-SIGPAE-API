import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_get_utensilios_cozinha_por_edital(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    utensilio_cozinha_factory,
    edital_utensilio_cozinha_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    utensilio_cozinha_1 = utensilio_cozinha_factory.create(nome="Abridor de latas")
    utensilio_cozinha_2 = utensilio_cozinha_factory.create(
        nome="Balde com tampa (100 litros)"
    )
    utensilio_cozinha_3 = utensilio_cozinha_factory.create(
        nome="Caixa térmica (para kit lanche e alimentação transportada em situações emergenciais)"
    )
    edital_utensilio_cozinha_factory.create(
        edital=edital,
        utensilios_cozinha=(
            utensilio_cozinha_1,
            utensilio_cozinha_2,
            utensilio_cozinha_3,
        ),
    )

    response = client.get(f"/imr/utensilios-cozinha/?edital_uuid={edital.uuid}")

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
    assert (
        any(
            utensilio_cozinha
            for utensilio_cozinha in results
            if utensilio_cozinha["nome"] == utensilio_cozinha_1.nome
        )
        is True
    )
    assert (
        any(
            utensilio_cozinha
            for utensilio_cozinha in results
            if utensilio_cozinha["nome"] == utensilio_cozinha_2.nome
        )
        is True
    )
    assert (
        any(
            utensilio_cozinha
            for utensilio_cozinha in results
            if utensilio_cozinha["nome"] == utensilio_cozinha_3.nome
        )
        is True
    )
