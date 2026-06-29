from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.permissions import (
    UsuarioEhDilogQualidade,
    ViewSetActionPermissionMixin,
)
from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaMensalAssinadoSerializer,
)
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocumentoDeRecebimentoParaAjusteSaldoSerializer,
)
from src.recebimento.ajuste_saldo_laudo.api.serializers.serializer_create import (
    AjusteSaldoCreateSerializer,
)
from src.recebimento.ajuste_saldo_laudo.api.serializers.serializers import (
    AjusteSaldoListagemSerializer,
)
from src.recebimento.ajuste_saldo_laudo.models import (
    AjusteSaldo,
)
from src.recebimento.ajuste_saldo_laudo.api.filters import (
    AjusteSaldoFilter,
)

from ....dados_comuns.api.paginations import DefaultPagination


class AjusteSaldoModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = AjusteSaldo.objects.all()
    serializer_class = AjusteSaldoListagemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AjusteSaldoFilter
    pagination_class = DefaultPagination
    permission_classes = (UsuarioEhDilogQualidade,)
    permission_action_classes = {
        "cronogramas_mensal_com_documentos": [UsuarioEhDilogQualidade],
        "documentos_do_cronograma": [UsuarioEhDilogQualidade],
    }

    def get_queryset(self):
      return (
        AjusteSaldo.objects.select_related(
          "documento_recebimento",
          "documento_recebimento__cronograma",
          "documento_recebimento__cronograma__empresa",
          "documento_recebimento__cronograma__ficha_tecnica__produto",
        )
        .order_by("-criado_em")
      )

    def create(self, request):
        """
        Endpoint: POST /ajuste-saldo-laudo/

        Cria um novo ajuste de Saldo de Laudo
        """
        print(request.data)
        serializer = AjusteSaldoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        """
        Endpoint: GET /ajuste-saldo-laudo/

        Retorna a lista de ajustes de saldo de laudo
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="cronogramas-mensal-com-documentos",
        url_name="cronogramas_mensal_com_documentos",
    )
    def cronogramas_mensal_com_documentos(self, request):
        """
        Endpoint: GET /ajuste-saldo-laudo/cronogramas-mensal-com-documentos/

        Retorna lista de cronogramas mensais
        """
        cronogramas = Cronograma.objects.filter(
            documentos_de_recebimento__isnull=False
        ).order_by("-alterado_em")

        serializer = CronogramaMensalAssinadoSerializer(cronogramas, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="documentos-do-cronograma",
        url_name="documentos_do_cronograma",
    )
    def documentos_do_cronograma(self, request):
        """
        Endpoint: GET /ajuste-saldo-laudo/documentos-do-cronograma/

        Retorna lista de documentos de um cronograma a partir do seu uuid
        """
        cronograma_uuid = request.query_params.get("cronograma_uuid")
        if not cronograma_uuid:
            return Response(
                {"detail": "UUID do cronograma é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cronograma = Cronograma.objects.filter(uuid=cronograma_uuid).first()
        if not cronograma:
            return Response(
                {"detail": "Cronograma não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        documentos = cronograma.documentos_de_recebimento.all()
        print(documentos)

        serializer = DocumentoDeRecebimentoParaAjusteSaldoSerializer(
            documentos, many=True
        )
        return Response(serializer.data)
