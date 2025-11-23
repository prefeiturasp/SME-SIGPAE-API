from rest_framework import viewsets, status
from rest_framework.response import Response
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias
from .serializers import RecreioNasFeriasSerializer
from django.db import transaction


class RecreioNasFeriasViewSet(viewsets.ModelViewSet):
    queryset = RecreioNasFerias.objects.all().prefetch_related(
        'unidades_participantes__lote__diretoria_regional',
        'unidades_participantes__lote',
        'unidades_participantes__unidade_educacional',
        'unidades_participantes__tipos_alimentacao__tipo_alimentacao',
        'unidades_participantes__tipos_alimentacao__categoria'
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
