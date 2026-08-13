from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from ..models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo
from .permissions import PermissaoParaCadastrarTermoRecebimentoDefinitivo
from .serializers.serializers import TermoRecebimentoDefinitivoSerializer
from .serializers.serializers_create import TermoRecebimentoDefinitivoCreateSerializer


class TermoRecebimentoDefinitivoViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Criação do Termo de Recebimento Definitivo (Salvar e Enviar)."""

    lookup_field = "uuid"
    serializer_class = TermoRecebimentoDefinitivoCreateSerializer
    queryset = TermoRecebimentoDefinitivo.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarTermoRecebimentoDefinitivo,)

    def perform_create(self, serializer):
        cronogramas = serializer.validated_data.pop("cronogramas")
        instance = serializer.save(
            criado_por=self.request.user,
            alterado_por=self.request.user,
            status=TermoRecebimentoDefinitivo.ENVIADO,
        )
        for item in cronogramas:
            CronogramaTermoRecebimentoDefinitivo.objects.create(
                termo=instance,
                cronograma=item["cronograma"],
                valor_contrato=item["valor_contrato"],
                quantidade_total_recebida=item["quantidade_total_recebida"],
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        output_serializer = TermoRecebimentoDefinitivoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
