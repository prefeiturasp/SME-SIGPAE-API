from django_filters import rest_framework as filters
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from ...api.serializers import SubprefeituraSerializer, SubprefeituraSerializerSimples
from ...models import Subprefeitura
from ...subprefeitura.api.filters import SubprefeituraFilter


class SubprefeituraViewSet(ReadOnlyModelViewSet):
    """
    Lista subprefeituras.

    ``diretoria_regional__uuid`` e ``diretoria_regional__uuid[]`` filtram pelo
    vínculo já existente com a diretoria regional. Várias DREs não duplicam a
    subprefeitura. Sem o parâmetro, a lista permanece completa.
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "uuid"
    queryset = Subprefeitura.objects.prefetch_related("diretoria_regional")
    serializer_class = SubprefeituraSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SubprefeituraFilter

    @action(detail=False, methods=["get"], url_path="lista-completa")
    def lista_completa(self, request):
        response = {
            "results": SubprefeituraSerializerSimples(
                self.get_queryset(), many=True
            ).data
        }
        return Response(response)
