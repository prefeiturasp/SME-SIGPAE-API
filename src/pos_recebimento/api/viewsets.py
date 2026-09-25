from django.db.models import Prefetch, Q
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.api.paginations import DefaultPagination
from src.pre_recebimento.cronograma_entrega.models import Cronograma

from ..models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo
from .filters import TermoRecebimentoDefinitivoFilter
from .permissions import (
    PermissaoParaCadastrarTermoRecebimentoDefinitivo,
    PermissaoParaVisualizarTermoRecebimentoDefinitivo,
    usuario_vinculado_a_empresa_fornecedor,
)
from .serializers.serializers import (
    TermoRecebimentoDefinitivoListagemSerializer,
    TermoRecebimentoDefinitivoPainelAssinaturaSerializer,
    TermoRecebimentoDefinitivoSerializer,
)
from .serializers.serializers_create import TermoRecebimentoDefinitivoCreateSerializer


class TermoRecebimentoDefinitivoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Criação e listagem do Termo de Recebimento Definitivo.

    Endpoints:
    - ``POST /`` — Cria o termo (Salvar e Enviar).
    - ``GET /`` — Lista os termos (paginado, com filtros por produto,
      empresa, número de cronograma, status e período de cadastro).
    - ``GET /<uuid>/`` — Detalhe do termo.
    - ``GET /pendentes-assinatura/`` — Painel do fiscal: termos a assinar.
    - ``GET /assinados/`` — Painel do fiscal: termos já assinados.
    """

    lookup_field = "uuid"
    serializer_class = TermoRecebimentoDefinitivoCreateSerializer
    queryset = TermoRecebimentoDefinitivo.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarTermoRecebimentoDefinitivo,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TermoRecebimentoDefinitivoFilter
    pagination_class = DefaultPagination

    ACTIONS_PAINEL_ASSINATURA = ("pendentes_assinatura", "assinados")

    def get_queryset(self):
        """Termos ordenados por data de criação (decrescente).

        Usuários vinculados a empresa fornecedora veem apenas os termos
        da própria empresa com status do fluxo de envio (exibidos como
        "Recebido") ou ``ASSINADO_FORNECEDOR`` (exibido como "Assinado").
        Na listagem, os relacionamentos exibidos no grid são
        pré-carregados para evitar N+1.
        """
        queryset = TermoRecebimentoDefinitivo.objects.all().order_by("-criado_em")

        if usuario_vinculado_a_empresa_fornecedor(self.request.user):
            queryset = queryset.filter(
                empresa=self.request.user.vinculo_atual.instituicao,
                status__in=[
                    *TermoRecebimentoDefinitivo.STATUS_RECEBIDO_FORNECEDOR,
                    TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR,
                ],
            )

        if self.action in ("list", *self.ACTIONS_PAINEL_ASSINATURA):
            return queryset.select_related("empresa", "contrato").prefetch_related(
                Prefetch(
                    "cronogramas",
                    queryset=Cronograma.objects.select_related(
                        "ficha_tecnica__produto"
                    ),
                )
            )

        return queryset

    def get_permissions(self):
        """Visualização é liberada para mais perfis do que o cadastro."""
        if self.action in ("list", "retrieve", *self.ACTIONS_PAINEL_ASSINATURA):
            return [PermissaoParaVisualizarTermoRecebimentoDefinitivo()]

        return [PermissaoParaCadastrarTermoRecebimentoDefinitivo()]

    def get_serializer_class(self):
        """Retorna o serializer adequado conforme a ação."""
        if self.action == "list":
            return TermoRecebimentoDefinitivoListagemSerializer
        if self.action == "retrieve":
            return TermoRecebimentoDefinitivoSerializer
        if self.action in self.ACTIONS_PAINEL_ASSINATURA:
            return TermoRecebimentoDefinitivoPainelAssinaturaSerializer

        return TermoRecebimentoDefinitivoCreateSerializer

    def list(self, request, *args, **kwargs):
        """
        Endpoint: GET /pos-recebimento/termos/

        """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by("-criado_em").distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _termos_do_fiscal(self, request, status_termo):
        """Resposta paginada do painel de assinaturas do fiscal.

        Termos no status informado em que o usuário da requisição é um dos
        três fiscais, já com os filtros do painel (``numero_contrato``,
        ``nome_produto`` e ``nome_empresa``) aplicados.
        """
        usuario = request.user

        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(status=status_termo)
            .filter(Q(fiscal_1=usuario) | Q(fiscal_2=usuario) | Q(fiscal_3=usuario))
            .order_by("-criado_em")
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="pendentes-assinatura",
        url_name="pendentes_assinatura",
    )
    def pendentes_assinatura(self, request):
        """Termos aguardando a assinatura do fiscal logado.

        Endpoint: ``GET /pos-recebimento/termos/pendentes-assinatura/``
        """
        return self._termos_do_fiscal(
            request, TermoRecebimentoDefinitivo.ENVIADO_FISCAIS
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="assinados",
        url_name="assinados",
    )
    def assinados(self, request):
        """Termos já assinados pelo fornecedor, dos quais o usuário logado
        é fiscal.

        Endpoint: ``GET /pos-recebimento/termos/assinados/``
        """
        return self._termos_do_fiscal(
            request, TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR
        )

    def perform_create(self, serializer):
        """Persiste o termo com status ``ENVIADO_FISCAIS`` e cria as linhas do
        modelo intermediário (cronograma + quantidade total recebida) para
        cada cronograma do payload."""
        cronogramas = serializer.validated_data.pop("cronogramas")
        instance = serializer.save(
            criado_por=self.request.user,
            alterado_por=self.request.user,
            status=TermoRecebimentoDefinitivo.ENVIADO_FISCAIS,
        )
        for item in cronogramas:
            CronogramaTermoRecebimentoDefinitivo.objects.create(
                termo=instance,
                cronograma=item["cronograma"],
                quantidade_total_recebida=item["quantidade_total_recebida"],
            )

    def create(self, request, *args, **kwargs):
        """Cria o termo (valida, persiste e retorna 201 com o serializador
        de saída)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        output_serializer = TermoRecebimentoDefinitivoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
