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
    permission_action_classes = {
        "create": [UsuarioCODAEGestaoAlimentacao],
    }
    serializer_class = DiaLetivoCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
