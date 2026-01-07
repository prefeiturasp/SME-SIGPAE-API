from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.helpers_autenticidade import (
    verificar_autenticidade_usuario,
)
from sme_sigpae_api.relatorios.relatorios import get_pdf_ficha_recebimento

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
    lookup_field = "uuid"
    queryset = QuestaoConferencia.objects.order_by("posicao")
    permission_classes = (PermissaoParaVisualizarQuestoesConferencia,)
    serializer_class = QuestaoConferenciaSerializer

    def list(self, request, *args, **kwargs):
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
        questoes = self.get_queryset().order_by("questao").distinct("questao")
        serializer = QuestaoConferenciaSimplesSerializer(questoes, many=True).data
        response = {"results": serializer}
        return Response(response)


class QuestoesPorProdutoModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = QuestoesPorProduto.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarQuestoesConferencia,)
    serializer_class = QuestoesPorProdutoSerializer
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = QuestoesPorProdutoFilter

    def get_serializer_class(self):
        return {
            "list": QuestoesPorProdutoSerializer,
            "retrieve": QuestoesPorProdutoSimplesSerializer,
        }.get(self.action, QuestoesPorProdutoCreateSerializer)

    def _get_cronograma(self, cronograma_uuid):
        try:
            return Cronograma.objects.get(uuid=cronograma_uuid)
        except ValidationError:
            raise ValidationError("UUID inválido.")
        except Cronograma.DoesNotExist:
            raise NotFound("Cronograma não encontrado.")

    def _get_questao(self, ficha_tecnica):
        return self.get_queryset().filter(ficha_tecnica=ficha_tecnica).first()

    @action(
        detail=False,
        methods=["GET"],
        url_path="busca-questoes-cronograma",
        permission_classes=(PermissaoParaVisualizarQuestoesConferencia,),
    )
    def busca_questoes_cronograma(self, request):
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
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoRascunhoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarFichaRecebimento,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        output_serializer = FichaDeRecebimentoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
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
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaRecebimento,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaRecebimentoFilter

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return FichaDeRecebimentoCreateSerializer
        if self.action in ["create_saldo_zero", "update_saldo_zero"]:
            return FichaDeRecebimentoCreateSerializerSaldoZero
        if self.action == "retrieve":
            return FichaDeRecebimentoDetalharSerializer
        return FichaDeRecebimentoSerializer

    def get_permissions(self):
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
        if auth_response := verificar_autenticidade_usuario(request):
            return auth_response

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        saved_instance = serializer.save()

        output_serializer = FichaDeRecebimentoSerializer(saved_instance)
        status_code = status.HTTP_201_CREATED if create else status.HTTP_200_OK
        return Response(output_serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        return self._process_ficha_request(request, create=True)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        return self._process_ficha_request(request, instance=instance, create=False)

    @action(detail=False, methods=["POST"], url_path="cadastrar-saldo-zero")
    def create_saldo_zero(self, request):
        return self._process_ficha_request(request, create=True)

    @action(detail=True, methods=["PUT"], url_path="atualizar-saldo-zero")
    def update_saldo_zero(self, request, uuid=None):
        instance = self.get_object()
        return self._process_ficha_request(request, instance=instance, create=False)

    @action(detail=True, methods=["GET"], url_path="gerar-pdf-ficha")
    def gerar_pdf_ficha(self, request, uuid=None):
        ficha = self.get_object()
        return get_pdf_ficha_recebimento(request, ficha)


class FichaDeRecebimentoReposicaoViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoReposicaoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarFichaRecebimento,)


class ReposicaoCronogramaFichaRecebimentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReposicaoCronogramaFichaRecebimentoSerializer
    queryset = ReposicaoCronogramaFichaRecebimento.objects.all().order_by("-criado_em")
