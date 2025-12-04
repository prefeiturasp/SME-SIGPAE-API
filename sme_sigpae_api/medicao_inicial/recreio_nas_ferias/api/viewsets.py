from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.response import Response

from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.api.filters import (
    RecreioNasFeriasFilter,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.api.serializers import (
    RecreioNasFeriasCreateSerializer,
    RecreioNasFeriasSerializer,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias


class RecreioNasFeriasViewSet(viewsets.ModelViewSet):
    queryset = RecreioNasFerias.objects.all().prefetch_related(
        "unidades_participantes__lote__diretoria_regional",
        "unidades_participantes__lote",
        "unidades_participantes__unidade_educacional",
        "unidades_participantes__tipos_alimentacao__tipo_alimentacao",
        "unidades_participantes__tipos_alimentacao__categoria",
    )
    serializer_class = RecreioNasFeriasSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecreioNasFeriasFilter
    lookup_field = "uuid"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecreioNasFeriasCreateSerializer
        return RecreioNasFeriasSerializer

    def get_queryset(self):
        if self.request.user.tipo_usuario == "escola":
            escola = self.request.user.vinculo_atual.instituicao
            queryset = self.queryset.filter(
                unidades_participantes__unidade_educacional__uuid=escola.uuid
            )
            return self.filter_queryset(queryset)
        return self.filter_queryset(self.queryset)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
