"""Viewsets da API do submódulo base de pré-recebimento."""

from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.api.paginations import DefaultPagination
from src.dados_comuns.permissions import (
    PermissaoParaCadastrarVisualizarUnidadesMedida,
    PermissaoParaVisualizarUnidadesMedida,
)
from src.pre_recebimento.base.api.filters import (
    UnidadeMedidaFilter,
)
from src.pre_recebimento.base.api.serializers.serializer_create import (
    UnidadeMedidaCreateSerializer,
)
from src.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSerialzer,
    UnidadeMedidaSimplesSerializer,
)
from src.pre_recebimento.base.models import (
    UnidadeMedida,
)


class UnidadeMedidaViewset(viewsets.ModelViewSet):
    """Viewset de unidades de medida.

    Exposto em ``/unidades-medida-logistica/``, com CRUD completo. A
    permissão ``PermissaoParaCadastrarVisualizarUnidadesMedida`` restringe
    o acesso a usuários da CODAE com perfis ``DILOG_QUALIDADE``,
    ``DILOG_CRONOGRAMA`` ou ``COORDENADOR_CODAE_DILOG_LOGISTICA``.
    """

    lookup_field = "uuid"
    queryset = UnidadeMedida.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarVisualizarUnidadesMedida,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UnidadeMedidaFilter

    def get_serializer_class(self):
        """Retorna o serializer conforme a ação.

        ``retrieve`` e ``list`` usam o serializer de leitura
        (``UnidadeMedidaSerialzer``); as demais ações usam o serializer de
        criação (``UnidadeMedidaCreateSerializer``), que valida a
        capitalização de nome e abreviação.
        """
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
        """Lista os pares ``nome``/``abreviacao`` de todas as unidades.

        Endpoint ``GET /unidades-medida-logistica/lista-nomes-abreviacoes/``,
        acessível também aos perfis ``ADMINISTRADOR_EMPRESA`` e
        ``USUARIO_EMPRESA`` (via ``PermissaoParaVisualizarUnidadesMedida``).
        Usado para popular seletores no frontend.
        """
        unidades_medida = self.get_queryset()
        serializer = UnidadeMedidaSimplesSerializer(unidades_medida, many=True)
        response = {"results": serializer.data}
        return Response(response)
