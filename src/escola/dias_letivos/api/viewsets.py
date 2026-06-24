from typing import Any

from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ....dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    ViewSetActionPermissionMixin,
)
from ..models import DiaLetivoSIGPAE
from .filters import DiaLetivoFilter
from .serializers import DiaLetivoCreateSerializer, DiaLetivoSerializer


class DiaLetivoViewSet(
    ViewSetActionPermissionMixin, ListModelMixin, CreateModelMixin, GenericViewSet
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

    def get_serializer_class(self):
        """Retorna o serializador adequado conforme a ação.

        Para a ação ``list`` utiliza DiaLetivoSerializer; para as
        demais ações utiliza DiaLetivoCreateSerializer.
        """
        if self.action == "list":
            return DiaLetivoSerializer
        return DiaLetivoCreateSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria novos dias letivos a partir de recorrências e retorna HTTP 201.

        Valida os dados da requisição e, em caso de sucesso, retorna
        apenas o status code sem corpo de resposta.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
