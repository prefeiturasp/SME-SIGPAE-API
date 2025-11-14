from rest_framework import viewsets, status
from rest_framework.response import Response
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias
from .serializers import RecreioNasFeriasSerializer


class RecreioNasFeriasViewSet(viewsets.ModelViewSet):
    queryset = RecreioNasFerias.objects.all().prefetch_related(
        'unidades_participantes',
        'unidades_participantes__tipos_alimentacao'
    )
    serializer_class = RecreioNasFeriasSerializer
    lookup_field = 'uuid'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
