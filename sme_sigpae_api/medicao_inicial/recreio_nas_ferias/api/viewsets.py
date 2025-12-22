from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.api.filters import (
    RecreioNasFeriasFilter,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.api.serializers import (
    RecreioNasFeriasCreateSerializer,
    RecreioNasFeriasSerializer,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.utils import (
    gerar_calendario_recreio,
    gerar_dias_letivos_recreio,
)


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
            return self.filter_queryset(queryset).distinct()
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

    @action(detail=False, url_path="dias-letivos", methods=["get"])
    def dias_letivos(self, request):
        solictacao_uuid = request.query_params.get("solictacao_uuid")
        if not solictacao_uuid:
            return Response(
                dict(
                    detail="É necessário informar o UUID da solicitação da medição de recreio nas férias"
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            recreio = RecreioNasFerias.objects.get(
                solicitacoes_medicao_inicial__uuid=solictacao_uuid
            )
        except RecreioNasFerias.DoesNotExist:
            return Response(
                dict(detail="Essa medição não contém recreio nas férias"),
                status=status.HTTP_404_NOT_FOUND,
            )
        inicio_recreio = recreio.data_inicio
        fim_recreio = recreio.data_fim
        try:
            dias_letivos_filtrados = gerar_dias_letivos_recreio(
                inicio_recreio, fim_recreio
            )
        except ValueError as exc:
            return Response(
                dict(detail=str(exc)),
                status=status.HTTP_400_BAD_REQUEST,
            )
        calendario = gerar_calendario_recreio(
            inicio_recreio, fim_recreio, dias_letivos_filtrados
        )

        return Response(calendario, status=status.HTTP_200_OK)
