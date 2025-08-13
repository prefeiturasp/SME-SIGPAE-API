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
    FichaDeRecebimentoCreateSerializer,
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


class FichaRecebimentoModelViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    lookup_field = "uuid"
    serializer_class = FichaDeRecebimentoSerializer
    queryset = FichaDeRecebimento.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaRecebimento,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaRecebimentoFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return FichaDeRecebimentoCreateSerializer
        return FichaDeRecebimentoSerializer

    def get_permissions(self):
        permission_classes_map = {
            "list": (PermissaoParaVisualizarFichaRecebimento,),
            "retrieve": (PermissaoParaVisualizarFichaRecebimento,),
            "create": (PermissaoParaCadastrarFichaRecebimento,),
            "update": (PermissaoParaCadastrarFichaRecebimento,),
        }
        action_permissions = permission_classes_map.get(self.action, [])
        self.permission_classes = (*self.permission_classes, *action_permissions)
        return super(FichaRecebimentoModelViewSet, self).get_permissions()

    def create(self, request, *args, **kwargs):
        auth_response = self._verificar_autenticidade_usuario(request, *args, **kwargs)
        if auth_response:
            return auth_response

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        instance = FichaDeRecebimento.objects.prefetch_related(
            'documentos_recebimento',
            'arquivos',
            'questoes_conferencia',
            'ocorrencias'
        ).get(uuid=instance.uuid)

        output_serializer = FichaDeRecebimentoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        auth_response = self._verificar_autenticidade_usuario(request, *args, **kwargs)
        if auth_response:
            return auth_response

        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        instance = FichaDeRecebimento.objects.prefetch_related(
            'documentos_recebimento',
            'arquivos',
            'questoes_conferencia',
            'ocorrencias'
        ).get(uuid=instance.uuid)

        output_serializer = FichaDeRecebimentoSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def _verificar_autenticidade_usuario(self, request, *args, **kwargs):
        usuario = request.user
        password = request.data.pop("password", "")

        if not usuario.verificar_autenticidade(password):
            return Response(
                {
                    "Senha inválida. Em caso de esquecimento de senha, solicite a recuperação e tente novamente."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
