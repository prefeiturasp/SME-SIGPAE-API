from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ....dados_comuns.permissions import (
    UsuarioCODAEGestaoAlimentacao,
    ViewSetActionPermissionMixin,
)
from .serializers import DiaLetivoCreateSerializer


class DiaLetivoViewSet(ViewSetActionPermissionMixin, CreateModelMixin, GenericViewSet):
    """ViewSet para criação de dias letivos no SIGPAE.

    Permite apenas a ação de criação (POST). O acesso é restrito a
    usuários com permissão de CODAE Gestão de Alimentação.
    """

    permission_action_classes = {
        "create": [UsuarioCODAEGestaoAlimentacao],
    }
    serializer_class = DiaLetivoCreateSerializer

    def create(self, request, *args, **kwargs):
        """Cria novos dias letivos a partir de recorrências e retorna HTTP 201.

        Valida os dados da requisição e, em caso de sucesso, retorna
        apenas o status code sem corpo de resposta.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
