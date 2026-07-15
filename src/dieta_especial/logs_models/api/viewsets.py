from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from src.dieta_especial.logs_models.api.filters import (
    LogQuantidadeDietasEspeciaisFilter,
    LogQuantidadeDietasRecreioNasFeriasFilter,
)
from src.dieta_especial.logs_models.api.serializers import (
    LogQuantidadeDietasAutorizadasCEISerializer,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEISerializer,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasSerializer,
    LogQuantidadeDietasAutorizadasSerializer,
)
from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
)


class LogQuantidadeDietasAutorizadasViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = LogQuantidadeDietasAutorizadasSerializer
    queryset = LogQuantidadeDietasAutorizadas.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasEspeciaisFilter
    pagination_class = None


class LogQuantidadeDietasAutorizadasCEIViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = LogQuantidadeDietasAutorizadasCEISerializer
    queryset = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        faixa_etaria__isnull=False
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasEspeciaisFilter
    pagination_class = None


class LogQuantidadeDietasAutorizadasRecreioNasFeriasViewSet(
    mixins.ListModelMixin, GenericViewSet
):
    serializer_class = LogQuantidadeDietasAutorizadasRecreioNasFeriasSerializer
    queryset = LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasRecreioNasFeriasFilter
    pagination_class = None


class LogQuantidadeDietasAutorizadasRecreioNasFeriasCEIViewSet(
    mixins.ListModelMixin, GenericViewSet
):
    serializer_class = LogQuantidadeDietasAutorizadasRecreioNasFeriasCEISerializer
    queryset = LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LogQuantidadeDietasRecreioNasFeriasFilter
    pagination_class = None
