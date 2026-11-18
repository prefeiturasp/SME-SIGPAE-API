from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ...api.filters import filtrar_lotes_por_escopo
from ...api.serializers import LoteNomeSerializer, LoteSerializer, LoteSimplesSerializer
from ...api.serializers_create import LoteCreateSerializer
from ...models import Lote


class LoteViewSet(ModelViewSet):
    lookup_field = "uuid"
    serializer_class = LoteSimplesSerializer
    queryset = Lote.objects.all()

    @action(detail=False, methods=["GET"], url_path="meus-lotes-vinculados")
    def meus_lotes_vinculados(self, request):
        if request.user.tipo_usuario == "diretoriaregional":
            lotes = self.queryset.filter(
                diretoria_regional=request.user.vinculo_atual.instituicao
            )
        else:
            lotes = self.queryset.filter(
                terceirizada=request.user.vinculo_atual.instituicao
            )
        return Response({"results": LoteSerializer(lotes, many=True).data})

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LoteCreateSerializer
        return LoteSimplesSerializer

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Não é permitido excluir um Lote com escolas associadas"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LoteSimplesViewSet(ModelViewSet):
    """
    Lista lotes com a diretoria regional aninhada (uuid, nome, iniciais).

    DRE enxerga somente os lotes da própria diretoria. Terceirizada enxerga
    somente os lotes da própria empresa. Os demais perfis não são restringidos.
    """

    lookup_field = "uuid"
    serializer_class = LoteNomeSerializer
    queryset = Lote.objects.select_related(
        "diretoria_regional", "terceirizada", "tipo_gestao"
    )
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        "uuid",
        "diretoria_regional__uuid",
        "terceirizada__uuid",
        "contratos_do_lote__edital__uuid",
    )

    def get_queryset(self):
        return filtrar_lotes_por_escopo(super().get_queryset(), self.request)
