from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action

from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaCadastrarVisualizarUnidadesMedida,
    PermissaoParaVisualizarUnidadesMedida,

)
from sme_sigpae_api.pre_recebimento.base.api.filters import (
    UnidadeMedidaFilter,
)
from sme_sigpae_api.pre_recebimento.base.api.serializers.serializer_create import (
    UnidadeMedidaCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSerialzer,
    UnidadeMedidaSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.base.models import (
    UnidadeMedida,
)

from sme_sigpae_api.dados_comuns.api.paginations import DefaultPagination


class UnidadeMedidaViewset(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = UnidadeMedida.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarVisualizarUnidadesMedida,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UnidadeMedidaFilter

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return UnidadeMedidaSerialzer
        return UnidadeMedidaCreateSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-nomes-abreviacoes",
        permission_classes=(PermissaoParaVisualizarUnidadesMedida,),
    )
    def listar_nomes_abreviacoes(self, request):
        unidades_medida = self.get_queryset()
        serializer = UnidadeMedidaSimplesSerializer(unidades_medida, many=True)
        response = {"results": serializer.data}
        return Response(response)
