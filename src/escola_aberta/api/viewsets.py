import datetime
import uuid

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import EscolaAberta
from ..services import obter_unidade_escola_aberta_por_mes_ano
from .serializers import (
    EscolaAbertaCreateSerializer,
    EscolaAbertaPorEscolaSerializer,
    EscolaAbertaReadSerializer,
)


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

    @action(detail=False, methods=["GET"], url_path="por-escola")
    def por_escola(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        mes = request.query_params.get("mes")
        ano = request.query_params.get("ano")

        if not all([escola_uuid, mes, ano]):
            return Response(
                {"detail": "Parâmetros obrigatórios: escola_uuid, mes e ano"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            escola_uuid = uuid.UUID(escola_uuid)
            mes = int(mes)
            ano = int(ano)
            datetime.date(ano, mes, 1)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Parâmetros escola_uuid, mes ou ano inválidos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unidade = obter_unidade_escola_aberta_por_mes_ano(escola_uuid, mes, ano)
        if not unidade:
            return Response({"possui_cadastro": False}, status=status.HTTP_200_OK)

        return Response(
            {
                "possui_cadastro": True,
                "cadastro": EscolaAbertaPorEscolaSerializer(unidade).data,
            },
            status=status.HTTP_200_OK,
        )
