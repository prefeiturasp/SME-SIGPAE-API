from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from sme_sigpae_api.dados_comuns.utils import ordena_queryset_por_ultimo_log
from sme_sigpae_api.produto.api.dashboard.utils import (
    filtrar_query_params,
    retorna_produtos_homologados,
    trata_parcialmente_homologados_ou_suspensos,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    HomologacaoProdutoPainelGerencialSerializer,
)
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.produto.utils import DashboardPagination


class HomologacaoProdutoDashboardViewSet(ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HomologacaoProdutoPainelGerencialSerializer
    queryset = HomologacaoProduto.objects.all()
    pagination_class = DashboardPagination

    @action(
        detail=False,
        methods=["GET"],
        url_path="homologados",
        pagination_class=DashboardPagination,
    )
    def dashboard_homologados(self, request):
        query_set = self.get_queryset()
        query_set = filtrar_query_params(request, query_set)
        query_set = trata_parcialmente_homologados_ou_suspensos(
            request, query_set, vinculo_suspenso=False
        )
        query_set = retorna_produtos_homologados(query_set)
        lista = ordena_queryset_por_ultimo_log(query_set)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_HOMOLOGADO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="nao-homologados",
        pagination_class=DashboardPagination,
    )
    def dashboard_nao_homologados(self, request):
        query_set = self.get_queryset().filter(
            status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO
        )
        query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
        lista = ordena_queryset_por_ultimo_log(query_set)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_NAO_HOMOLOGADO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="suspensos",
        pagination_class=DashboardPagination,
    )
    def dashboard_suspensos(self, request):
        query_set = self.get_queryset().exclude(
            status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO
        )
        query_set = filtrar_query_params(request, query_set, filtra_por_edital=True)
        query_set = trata_parcialmente_homologados_ou_suspensos(
            request, query_set, vinculo_suspenso=True
        )
        lista = ordena_queryset_por_ultimo_log(query_set)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_SUSPENDEU"}, many=True
        )
        return self.get_paginated_response(serializer.data)
