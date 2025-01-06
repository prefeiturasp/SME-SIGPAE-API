from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PerfilPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def get_cargo_eol(response: Response):
    if response.status_code != status.HTTP_200_OK:
        return None
    dados = response.json()
    if not dados.get("cargos"):
        return None
    return dados.get("cargos")[0]["descricaoCargo"]
