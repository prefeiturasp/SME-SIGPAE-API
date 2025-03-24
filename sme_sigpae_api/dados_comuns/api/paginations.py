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
    max_page_size = DEFAULT_MAX_PAGE_SIZE

    def get_paginated_response(self, data, total_dietas, data_log):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "page_size": int(self.request.GET.get("page_size", self.page_size)),
                "results": [
                    {"total_dietas": total_dietas, "data": data_log, "resultado": data}
                ],
            }
        )
