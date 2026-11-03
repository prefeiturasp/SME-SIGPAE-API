from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from ..models import EscolaAberta
from .serializers import EscolaAbertaCreateSerializer, EscolaAbertaReadSerializer


class EscolaAbertaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,  # adiciona PUT
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"

    def get_queryset(self):
        return EscolaAberta.objects.prefetch_related(
            "unidades_participantes__unidade_educacional",
            "unidades_participantes__tipos_alimentacao",
            "unidades_participantes__lote__diretoria_regional",
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EscolaAbertaCreateSerializer
        return EscolaAbertaReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        data = EscolaAbertaReadSerializer(
            self.get_queryset().get(pk=instance.pk),
            context=self.get_serializer_context(),
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        data = EscolaAbertaReadSerializer(
            self.get_queryset().get(pk=instance.pk),
            context=self.get_serializer_context(),
        ).data
        return Response(data, status=status.HTTP_200_OK)
