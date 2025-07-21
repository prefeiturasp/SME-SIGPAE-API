from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ...dados_comuns.api.paginations import DefaultPagination
from ...pre_recebimento.cronograma_entrega.models import Cronograma
from ..models import FichaDeRecebimento, QuestaoConferencia, QuestoesPorProduto
from .filters import FichaRecebimentoFilter, QuestoesPorProdutoFilter
from .permissions import (
    PermissaoParaCadastrarFichaRecebimento,
    PermissaoParaVisualizarFichaRecebimento,
    PermissaoParaVisualizarQuestoesConferencia,
)
from .serializers.serializers import (
    FichaDeRecebimentoSerializer,
    QuestaoConferenciaSerializer,
    QuestaoConferenciaSimplesSerializer,
    QuestoesPorProdutoDetalheSerializer,
    QuestoesPorProdutoSerializer,
    QuestoesPorProdutoSimplesSerializer,
)
from .serializers.serializers_create import (
    FichaDeRecebimentoRascunhoSerializer,
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

    @action(
        detail=False,
        methods=["GET"],
        url_path="busca-questoes-cronograma",
        permission_classes=(PermissaoParaVisualizarQuestoesConferencia,),
    )
    def busca_questoes_cronograma(self, request):
        cronograma_uuid = request.query_params.get("cronograma_uuid")

        if not cronograma_uuid:
            return Response(
                {"detail": "Parâmetro 'cronograma_uuid' obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cronograma = Cronograma.objects.get(uuid=cronograma_uuid)
            ficha_tecnica = cronograma.ficha_tecnica
            questao = self.get_queryset().get(ficha_tecnica=ficha_tecnica)

        except Cronograma.DoesNotExist:
            return Response(
                {"detail": "Cronograma não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError:
            return Response(
                {"detail": "UUID inválido."}, status=status.HTTP_400_BAD_REQUEST
            )
        except QuestoesPorProduto.DoesNotExist:
            return Response()

        serializer = QuestoesPorProdutoDetalheSerializer(questao)
        return Response(serializer.data)


class FichaDeRecebimentoRascunhoViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoRascunhoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarFichaRecebimento,)


class FichaRecebimentoModelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaRecebimento,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaRecebimentoFilter
