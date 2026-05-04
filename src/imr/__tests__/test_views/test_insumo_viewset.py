import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_get_insumos_por_edital(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    insumo_factory,
    edital_insumo_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    insumo_1 = insumo_factory.create(nome="Balde plástico")
    insumo_2 = insumo_factory.create(nome="Borrifador plástico")
    insumo_3 = insumo_factory.create(
        nome="Escova para higienização de frascos de mamadeiras e acessórios"
    )
    edital_insumo_factory.create(edital=edital, insumos=(insumo_1, insumo_2, insumo_3))

    response = client.get(f"/imr/insumos/?edital_uuid={edital.uuid}")

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
    assert any(insumo for insumo in results if insumo["nome"] == insumo_1.nome) is True
    assert any(insumo for insumo in results if insumo["nome"] == insumo_2.nome) is True
    assert any(insumo for insumo in results if insumo["nome"] == insumo_3.nome) is True
