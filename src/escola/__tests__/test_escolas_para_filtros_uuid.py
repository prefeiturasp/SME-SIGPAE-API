import pytest
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.parametrize("rota", ["periodos-escolares", "tipos-alimentacao"])
@pytest.mark.parametrize(
    "uuid",
    ["uuid-invalido", "00000000-0000-0000-0000-000000000000"],
)
def test_escolas_para_filtros_rejeita_uuid_invalido_ou_inexistente(
    client_autenticado_da_escola, rota, uuid
):
    response = client_autenticado_da_escola.get(
        f"/escolas-para-filtros/{uuid}/{rota}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
