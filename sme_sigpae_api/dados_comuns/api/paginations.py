from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
DEFAULT_MAX_PAGE_SIZE = 100


class CustomPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = 5
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "page_size": int(self.request.GET.get("page_size", self.page_size)),
                "results": data,
            }
        )


class DownloadPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"


class DefaultPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = DEFAULT_MAX_PAGE_SIZE


class HistoricoDietasPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    max_page_size = DEFAULT_PAGE_SIZE

    def get_page_size(self, request):
        """
        Retorna o tamanho da página a ser utilizado na paginação com base no parâmetro 'page_size' fornecido na requisição.
        """
        page_size = request.query_params.get("page_size", self.page_size)
        try:
            page_size = int(page_size)
        except (TypeError, ValueError):
            page_size = self.max_page_size

        return min(page_size, self.max_page_size)

    def get_paginated_response(self, data, total_dietas, data_log):
        page_size = self.request.GET.get("page_size", self.page_size)
        try:
            page_size = int(page_size)
        except (TypeError, ValueError):
            page_size = self.page_size
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "page_size": page_size,
                "total_dietas": total_dietas,
                "data": data_log,
                "results": data,
            }
        )
