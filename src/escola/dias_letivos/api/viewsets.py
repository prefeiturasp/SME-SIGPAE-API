from typing import Any
from datetime import date

from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ....dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    ViewSetActionPermissionMixin,
)
from ..models import DiaLetivoSIGPAE
from .filters import DiaLetivoFilter
from .serializers import DiaLetivoSerializer, DiaLetivoDetailSerializer
from .serializers_create import DiaLetivoCreateSerializer, DiaLetivoUpdateSerializer


class DiaLetivoViewSet(
    ViewSetActionPermissionMixin, ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet
):
    """ViewSet para criação e listagem de dias letivos no SIGPAE.

    Permite criação (POST) e listagem (GET). O acesso é restrito a
    usuários com permissão de CODAE Gestão de Alimentação.

    A ação de listagem suporta filtros obrigatórios por mês e ano,
    e retorna os resultados sem paginação.
    """

    permission_action_classes = {
        "create": [UsuarioCODAEGestaoAlimentacao],
        "list": [UsuarioCODAEGestaoAlimentacao],
        "retrieve": [UsuarioCODAEGestaoAlimentacao],
        "update": [UsuarioCODAEGestaoAlimentacao],
        "partial_update": [UsuarioCODAEGestaoAlimentacao],
        "destroy": [UsuarioCODAEGestaoAlimentacao],
    }
    queryset = DiaLetivoSIGPAE.objects.prefetch_related(
        "lotes__contratos_do_lote__edital",
        "tipos_unidade_escolar",
        "periodos_escolares",
        "escolas",
    ).all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DiaLetivoFilter
    pagination_class = None
    lookup_field = "uuid"

    def get_serializer_class(self):
        """Retorna o serializador adequado conforme a ação.

        Para a ação ``list`` utiliza DiaLetivoSerializer; para as
        demais ações utiliza DiaLetivoCreateSerializer.
        """
        if self.action == "list":
            return DiaLetivoSerializer
        if self.action == "retrieve":
            return DiaLetivoDetailSerializer
        if self.action in ("update", "partial_update"):
            return DiaLetivoUpdateSerializer
        return DiaLetivoCreateSerializer

    def filter_queryset(self, queryset):
        if self.action == "list":
            return super().filter_queryset(queryset)
        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria novos dias letivos a partir de recorrências e retorna HTTP 201.

        Valida os dados da requisição e, em caso de sucesso, retorna
        apenas o status code sem corpo de resposta.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.instance = instance
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = DiaLetivoDetailSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.data < date.today():
            return Response(
                {
                    "detail": (
                        f"Não é permitido excluir um dia letivo cuja data já passou "
                        f"({instance.data.strftime('%d/%m/%Y')})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
