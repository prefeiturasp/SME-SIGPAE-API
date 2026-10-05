import pytest
from rest_framework import status

from src.escola.models import Escola


pytestmark = pytest.mark.django_db


def test_escola_simplissima_retorna_detalhe_por_uuid(
    client_autenticado_da_escola, escola
):
    response = client_autenticado_da_escola.get(
        f"/escolas-simplissima/{escola.uuid}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)
    assert response.json()["uuid"] == str(escola.uuid)
    assert response.json()["codigo_eol"] == escola.codigo_eol


def test_escola_simplissima_preserva_consulta_por_dre(
    client_autenticado_da_escola, diretoria_regional
):
    response = client_autenticado_da_escola.get(
        f"/escolas-simplissima/{diretoria_regional.uuid}/"
    )

    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert isinstance(dados, list)
    esperadas = set(
        str(uuid)
        for uuid in Escola.objects.filter(
            diretoria_regional=diretoria_regional
        ).values_list("uuid", flat=True)
    )
    assert esperadas
    assert {escola["uuid"] for escola in dados} == esperadas


def test_escola_simplissima_preserva_lista_vazia_para_dre_inexistente(
    client_autenticado_da_escola,
):
    response = client_autenticado_da_escola.get(
        "/escolas-simplissima/00000000-0000-0000-0000-000000000000/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_escola_simplissima_rejeita_uuid_malformado(
    client_autenticado_da_escola,
):
    response = client_autenticado_da_escola.get(
        "/escolas-simplissima/uuid-invalido/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
