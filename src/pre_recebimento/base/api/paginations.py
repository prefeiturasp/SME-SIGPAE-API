"""Paginação da API do submódulo base de pré-recebimento."""

from rest_framework.pagination import PageNumberPagination


class PreRecebimentoPagination(PageNumberPagination):
    """Paginação padrão das listagens de pré-recebimento.

    Página com 10 registros, tamanho configurável via ``page_size`` e
    máximo de 100 registros por página.
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
