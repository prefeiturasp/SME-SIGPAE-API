from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from src.dados_comuns.api.paginations import DefaultPagination

from ..models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo
from .filters import TermoRecebimentoDefinitivoFilter
from .permissions import PermissaoParaCadastrarTermoRecebimentoDefinitivo
from .serializers.serializers import (
    TermoRecebimentoDefinitivoListagemSerializer,
    TermoRecebimentoDefinitivoSerializer,
)
from .serializers.serializers_create import TermoRecebimentoDefinitivoCreateSerializer


class TermoRecebimentoDefinitivoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Criação e listagem do Termo de Recebimento Definitivo.

    Endpoints:
    - ``POST /`` — Cria o termo (Salvar e Enviar).
    - ``GET /`` — Lista os termos (paginado, com filtros por produto,
      empresa, número de cronograma, status e período de cadastro).
    - ``GET /<uuid>/`` — Detalhe do termo.
    """

    lookup_field = "uuid"
    serializer_class = TermoRecebimentoDefinitivoCreateSerializer
    queryset = TermoRecebimentoDefinitivo.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarTermoRecebimentoDefinitivo,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TermoRecebimentoDefinitivoFilter
    pagination_class = DefaultPagination

    def get_queryset(self):
        """Termos ordenados por data de criação (decrescente).

        Na listagem, os relacionamentos exibidos no grid são pré-carregados
        para evitar N+1.
        """
        queryset = TermoRecebimentoDefinitivo.objects.all().order_by("-criado_em")

        if self.action == "list":
            return queryset.select_related("empresa", "contrato").prefetch_related(
                "cronogramas"
            )

        return queryset

    def get_serializer_class(self):
        """Retorna o serializer adequado conforme a ação."""
        if self.action == "list":
            return TermoRecebimentoDefinitivoListagemSerializer
        if self.action == "retrieve":
            return TermoRecebimentoDefinitivoSerializer

        return TermoRecebimentoDefinitivoCreateSerializer

    def list(self, request, *args, **kwargs):
        """
        Endpoint: GET /pos-recebimento/termos/

        """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-criado_em").distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Persiste o termo com status ``ENVIADO_FISCAIS`` e cria as linhas do
        modelo intermediário (cronograma + valor_contrato + quantidade
        total recebida) para cada cronograma do payload."""
        cronogramas = serializer.validated_data.pop("cronogramas")
        instance = serializer.save(
            criado_por=self.request.user,
            alterado_por=self.request.user,
            status=TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
        )
        for item in cronogramas:
            CronogramaTermoRecebimentoDefinitivo.objects.create(
                termo=instance,
                cronograma=item["cronograma"],
                valor_contrato=item["valor_contrato"],
                quantidade_total_recebida=item["quantidade_total_recebida"],
            )

    def create(self, request, *args, **kwargs):
        """Cria o termo (valida, persiste e retorna 201 com o serializador
        de saída)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        output_serializer = TermoRecebimentoDefinitivoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
