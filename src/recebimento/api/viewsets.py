"""Viewsets da API do módulo de recebimento."""

from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from src.dados_comuns.helpers_autenticidade import (
    verificar_autenticidade_usuario,
)
from src.dados_comuns.permissions import PermissaoParaVisualizarRelatorioCronograma
from src.relatorios.relatorios import get_pdf_ficha_recebimento

from ...dados_comuns.api.paginations import DefaultPagination
from ...pre_recebimento.cronograma_entrega.models import Cronograma
from ..models import (
    FichaDeRecebimento,
    QuestaoConferencia,
    QuestoesPorProduto,
    ReposicaoCronogramaFichaRecebimento,
)
from .filters import FichaRecebimentoFilter, QuestoesPorProdutoFilter
from .permissions import (
    PermissaoParaCadastrarFichaRecebimento,
    PermissaoParaVisualizarFichaRecebimento,
    PermissaoParaVisualizarQuestoesConferencia,
)
from .serializers.serializers import (
    FichaDeRecebimentoDetalharSerializer,
    FichaDeRecebimentoSerializer,
    QuestaoConferenciaSerializer,
    QuestaoConferenciaSimplesSerializer,
    QuestoesPorProdutoDetalheSerializer,
    QuestoesPorProdutoSerializer,
    QuestoesPorProdutoSimplesSerializer,
    ReposicaoCronogramaFichaRecebimentoSerializer,
)
from .serializers.serializers_create import (
    FichaDeRecebimentoCreateSerializer,
    FichaDeRecebimentoCreateSerializerSaldoZero,
    FichaDeRecebimentoRascunhoSerializer,
    FichaDeRecebimentoReposicaoSerializer,
    QuestoesPorProdutoCreateSerializer,
)


class QuestoesConferenciaModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset de leitura das questões de conferência.

    Exposto em ``/questoes-conferencia/``, restrito ao perfil
    ``DILOG_QUALIDADE``. A listagem agrupa as questões por tipo de
    embalagem (primárias e secundárias).
    """

    lookup_field = "uuid"
    queryset = QuestaoConferencia.objects.order_by("posicao")
    permission_classes = (PermissaoParaVisualizarQuestoesConferencia,)
    serializer_class = QuestaoConferenciaSerializer

    def list(self, request, *args, **kwargs):
        """Lista as questões agrupadas por tipo de embalagem.

        Retorna ``{"results": {"primarias": [...], "secundarias": [...]}}``,
        com as questões ordenadas por posição.
        """
        qs = self.get_queryset()
        primarias = qs.filter(
            tipo_questao__contains=QuestaoConferencia.TIPO_QUESTAO_PRIMARIA
        )
        secundarias = qs.filter(
            tipo_questao__contains=QuestaoConferencia.TIPO_QUESTAO_SECUNDARIA
        )

        return Response(
            {
                "results": {
                    "primarias": QuestaoConferenciaSerializer(
                        primarias, many=True
                    ).data,
                    "secundarias": QuestaoConferenciaSerializer(
                        secundarias, many=True
                    ).data,
                }
            }
        )

    @action(detail=False, methods=["GET"], url_path="lista-simples-questoes")
    def lista_simples_questoes(self, request):
        """Lista as questões distintas de forma simples.

        Endpoint ``GET /questoes-conferencia/lista-simples-questoes/``.
        Retorna ``uuid`` e ``questao`` das questões, sem repetições e
        ordenadas pelo texto.
        """
        questoes = self.get_queryset().order_by("questao").distinct("questao")
        serializer = QuestaoConferenciaSimplesSerializer(questoes, many=True).data
        response = {"results": serializer}
        return Response(response)


class QuestoesPorProdutoModelViewSet(viewsets.ModelViewSet):
    """Viewset das questões por produto.

    Exposto em ``/questoes-por-produto/``, restrito ao perfil
    ``DILOG_QUALIDADE``. Vincula as questões de conferência à ficha
    técnica de cada produto.
    """

    lookup_field = "uuid"
    queryset = QuestoesPorProduto.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarQuestoesConferencia,)
    serializer_class = QuestoesPorProdutoSerializer
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = QuestoesPorProdutoFilter

    def get_serializer_class(self):
        """Retorna o serializer conforme a ação.

        ``list`` usa ``QuestoesPorProdutoSerializer`` e ``retrieve`` usa
        ``QuestoesPorProdutoSimplesSerializer``; as demais ações usam
        ``QuestoesPorProdutoCreateSerializer``.
        """
        return {
            "list": QuestoesPorProdutoSerializer,
            "retrieve": QuestoesPorProdutoSimplesSerializer,
        }.get(self.action, QuestoesPorProdutoCreateSerializer)

    def _get_cronograma(self, cronograma_uuid):
        """Busca o cronograma pelo uuid, tratando erros de validação.

        Args:
            cronograma_uuid: UUID do cronograma.

        Returns:
            O cronograma encontrado.

        Raises:
            ValidationError: Se o UUID for inválido.
            NotFound: Se o cronograma não existir.
        """
        try:
            return Cronograma.objects.get(uuid=cronograma_uuid)
        except ValidationError:
            raise ValidationError("UUID inválido.")
        except Cronograma.DoesNotExist:
            raise NotFound("Cronograma não encontrado.")

    def _get_questao(self, ficha_tecnica):
        """Retorna as questões por produto da ficha técnica informada."""
        return self.get_queryset().filter(ficha_tecnica=ficha_tecnica).first()

    @action(
        detail=False,
        methods=["GET"],
        url_path="busca-questoes-cronograma",
        permission_classes=(PermissaoParaVisualizarQuestoesConferencia,),
    )
    def busca_questoes_cronograma(self, request):
        """Busca as questões de conferência de um cronograma.

        Endpoint ``GET /questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid={uuid}``.
        Retorna as questões (primárias e secundárias) vinculadas à ficha
        técnica do cronograma; ``400`` para uuid inválido ou parâmetro
        ausente, ``404`` para cronograma inexistente e ``200`` vazio quando
        o produto não possui questões cadastradas.
        """
        cronograma_uuid = request.query_params.get("cronograma_uuid")
        if not cronograma_uuid:
            raise ValidationError("Parâmetro 'cronograma_uuid' obrigatório.")
        try:
            cronograma = self._get_cronograma(cronograma_uuid)
            questao = self._get_questao(cronograma.ficha_tecnica)

            if not questao:
                return Response(status=status.HTTP_200_OK)

            serializer = QuestoesPorProdutoDetalheSerializer(questao)
            return Response(serializer.data)
        except ValidationError as error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as error:
            return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)


class FichaDeRecebimentoRascunhoViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset de rascunho das fichas de recebimento.

    Exposto em ``/rascunho-ficha-de-recebimento/``, restrito ao perfil
    ``DILOG_QUALIDADE``. Cria e atualiza fichas como rascunho, sem iniciar
    o fluxo (a ficha permanece em ``RASCUNHO``); ao atualizar uma ficha
    ``ASSINADA``, ela volta para ``RASCUNHO`` (``volta_para_rascunho``).
    """

    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoRascunhoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarFichaRecebimento,)

    def create(self, request, *args, **kwargs):
        """Cria uma ficha de recebimento como rascunho."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        output_serializer = FichaDeRecebimentoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Atualiza uma ficha de recebimento rascunho."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        output_serializer = FichaDeRecebimentoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class FichaRecebimentoModelViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset principal das fichas de recebimento.

    Exposto em ``/fichas-de-recebimento/``. A visualização é permitida aos
    perfis ``DILOG_QUALIDADE``, ``COORDENADOR_CODAE_DILOG_LOGISTICA``,
    ``DILOG_CRONOGRAMA``, ``DILOG_DIRETORIA`` e ``DILOG_ABASTECIMENTO``; a
    criação e a atualização são restritas a ``DILOG_QUALIDADE``. As ações
    de criar/atualizar exigem a verificação de autenticidade do usuário
    (senha) e disparam ``inicia_fluxo`` (RASCUNHO → ASSINADA) nos
    serializers.
    """

    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaRecebimento,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaRecebimentoFilter

    def get_serializer_class(self):
        """Retorna o serializer conforme a ação.

        ``create``/``update`` usam ``FichaDeRecebimentoCreateSerializer``;
        ``create_saldo_zero``/``update_saldo_zero`` usam
        ``FichaDeRecebimentoCreateSerializerSaldoZero``; ``retrieve`` usa
        ``FichaDeRecebimentoDetalharSerializer``; demais ações usam
        ``FichaDeRecebimentoSerializer``.
        """
        if self.action in ["create", "update"]:
            return FichaDeRecebimentoCreateSerializer
        if self.action in ["create_saldo_zero", "update_saldo_zero"]:
            return FichaDeRecebimentoCreateSerializerSaldoZero
        if self.action == "retrieve":
            return FichaDeRecebimentoDetalharSerializer
        return FichaDeRecebimentoSerializer

    def get_permissions(self):
        """Aplica permissões por ação.

        A criação e a atualização (incluindo as variantes ``saldo_zero``)
        exigem ``PermissaoParaCadastrarFichaRecebimento``; as demais ações
        usam ``PermissaoParaVisualizarFichaRecebimento``.
        """
        permission_classes_map = {
            "list": (PermissaoParaVisualizarFichaRecebimento,),
            "retrieve": (PermissaoParaVisualizarFichaRecebimento,),
            "create": (PermissaoParaCadastrarFichaRecebimento,),
            "update": (PermissaoParaCadastrarFichaRecebimento,),
            "create_saldo_zero": (PermissaoParaCadastrarFichaRecebimento,),
            "update_saldo_zero": (PermissaoParaCadastrarFichaRecebimento,),
        }
        action_permissions = permission_classes_map.get(self.action, [])
        self.permission_classes = (*self.permission_classes, *action_permissions)
        return super(FichaRecebimentoModelViewSet, self).get_permissions()

    def _process_ficha_request(self, request, instance=None, create=False):
        """Processa a criação/atualização de uma ficha de recebimento.

        Verifica a autenticidade do usuário (senha), valida o serializer e
        retorna a ficha serializada. A transição de workflow (``inicia_fluxo``)
        é executada pelo serializer.

        Args:
            request: Requisição HTTP.
            instance: Ficha existente (na atualização).
            create: ``True`` para criação, ``False`` para atualização.

        Returns:
            ``Response`` com a ficha serializada, ``201`` na criação e
            ``200`` na atualização.
        """
        if auth_response := verificar_autenticidade_usuario(request):
            return auth_response

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        saved_instance = serializer.save()

        output_serializer = FichaDeRecebimentoSerializer(saved_instance)
        status_code = status.HTTP_201_CREATED if create else status.HTTP_200_OK
        return Response(output_serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        """Cria uma ficha de recebimento assinada (``inicia_fluxo``)."""
        return self._process_ficha_request(request, create=True)

    def update(self, request, *args, **kwargs):
        """Atualiza uma ficha de recebimento."""
        instance = self.get_object()
        return self._process_ficha_request(request, instance=instance, create=False)

    @action(detail=False, methods=["POST"], url_path="cadastrar-saldo-zero")
    def create_saldo_zero(self, request):
        """Cria uma ficha ignorando os campos de saldo total zero.

        Endpoint ``POST /fichas-de-recebimento/cadastrar-saldo-zero/``.
        Usa ``FichaDeRecebimentoCreateSerializerSaldoZero``, que ignora os
        campos validados com ``requiredSaldoTotalZero`` no frontend.
        """
        return self._process_ficha_request(request, create=True)

    @action(detail=True, methods=["PUT"], url_path="atualizar-saldo-zero")
    def update_saldo_zero(self, request, uuid=None):
        """Atualiza uma ficha ignorando os campos de saldo total zero.

        Endpoint ``PUT /fichas-de-recebimento/{uuid}/atualizar-saldo-zero/``.
        """
        instance = self.get_object()
        return self._process_ficha_request(request, instance=instance, create=False)

    @action(
        detail=True,
        methods=["GET"],
        url_path="gerar-pdf-ficha",
        permission_classes=(PermissaoParaVisualizarRelatorioCronograma,),
    )
    def gerar_pdf_ficha(self, request, uuid=None):
        """Gera o PDF da ficha de recebimento.

        Endpoint ``GET /fichas-de-recebimento/{uuid}/gerar-pdf-ficha/``.
        """
        ficha = self.get_object()
        return get_pdf_ficha_recebimento(request, ficha)


class FichaDeRecebimentoReposicaoViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset de reposição das fichas de recebimento.

    Exposto em ``/reposicao-ficha-de-recebimento/``, restrito ao perfil
    ``DILOG_QUALIDADE``. Cria/atualiza uma ficha de recebimento no fluxo de
    reposição de cronograma (produtos faltantes/recusados), disparando
    ``inicia_fluxo`` na criação ou quando a ficha está em ``RASCUNHO``.
    """

    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoReposicaoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarFichaRecebimento,)


class ReposicaoCronogramaFichaRecebimentoViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset de leitura dos tipos de reposição de cronograma.

    Exposto em ``/reposicao-cronograma-ficha-recebimento/``. Lista os tipos
    de reposição disponíveis (Repor, Crédito, Outros) para seleção nas
    fichas de recebimento.
    """

    serializer_class = ReposicaoCronogramaFichaRecebimentoSerializer
    queryset = ReposicaoCronogramaFichaRecebimento.objects.all().order_by("-criado_em")
