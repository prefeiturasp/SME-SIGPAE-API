import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_get_equipamentos_por_edital(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    edital_factory,
    equipamento_factory,
    edital_equipamento_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    edital = edital_factory.create(numero="78/SME/2016")
    equipamento_1 = equipamento_factory.create(nome="Balança eletrônica de precisão")
    equipamento_2 = equipamento_factory.create(
        nome="Fogão elétrico com 2 queimadores (para lactário)"
    )
    equipamento_3 = equipamento_factory.create(
        nome="Refrigerador industrial com 4 portas"
    )
    edital_equipamento_factory.create(
        edital=edital, equipamentos=(equipamento_1, equipamento_2, equipamento_3)
    )

    response = client.get(f"/imr/equipamentos/?edital_uuid={edital.uuid}")

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 3
    assert (
        any(
            equipamento
            for equipamento in results
            if equipamento["nome"] == equipamento_1.nome
        )
        is True
    )
    assert (
        any(
            equipamento
            for equipamento in results
            if equipamento["nome"] == equipamento_2.nome
        )
        is True
    )
    assert (
        any(
            equipamento
            for equipamento in results
            if equipamento["nome"] == equipamento_3.nome
        )
        is True
    )
