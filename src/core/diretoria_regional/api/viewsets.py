from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from src.terceirizada.models import Terceirizada

from ...api.serializers import (
    DiretoriaRegionalCompletaSerializer,
    DiretoriaRegionalLookUpSerializer,
    DiretoriaRegionalSimplissimaSerializer,
)
from ...models import DiretoriaRegional


class DiretoriaRegionalViewSet(ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = DiretoriaRegional.objects.all()
    serializer_class = DiretoriaRegionalCompletaSerializer


class DiretoriaRegionalSimplissimaViewSet(ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    lookup_field = "uuid"
    queryset = DiretoriaRegional.objects.all()
    serializer_class = DiretoriaRegionalSimplissimaSerializer

    def get_queryset(self):
        usuario = self.request.user

        if usuario.vinculo_atual and isinstance(
            usuario.vinculo_atual.instituicao, Terceirizada
        ):
            terceirizada = usuario.vinculo_atual.instituicao

            return DiretoriaRegional.objects.filter(
                lotes__terceirizada=terceirizada,
                lotes__contratos_do_lote__encerrado=False,
                lotes__contratos_do_lote__edital__uuid__in=terceirizada.editais,
            ).distinct()

        return DiretoriaRegional.objects.all()

    @action(detail=False, methods=["GET"], url_path="lista-completa")
    def lista_completa(self, request):
        response = {
            "results": DiretoriaRegionalLookUpSerializer(
                self.get_queryset(), many=True
            ).data
        }
        return Response(response)
