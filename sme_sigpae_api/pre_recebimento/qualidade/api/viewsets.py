from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaCadastrarLaboratorio,
    PermissaoParaCadastrarVisualizarEmbalagem,
    ViewSetActionPermissionMixin,
)
from sme_sigpae_api.pre_recebimento.base.api.paginations import (
    PreRecebimentoPagination,
)
from sme_sigpae_api.pre_recebimento.qualidade.api.filters import (
    LaboratorioFilter,
    TipoEmbalagemQldFilter,
)
from sme_sigpae_api.pre_recebimento.qualidade.api.serializers.serializer_create import (
    LaboratorioCreateSerializer,
    TipoEmbalagemQldCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.qualidade.api.serializers.serializers import (
    LaboratorioCredenciadoSimplesSerializer,
    LaboratorioSerializer,
    LaboratorioSimplesFiltroSerializer,
    TipoEmbalagemQldSerializer,
)
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class LaboratorioModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Laboratorio.objects.all().order_by("-criado_em")
    serializer_class = LaboratorioSerializer
    pagination_class = PreRecebimentoPagination
    filterset_class = LaboratorioFilter
    filter_backends = (filters.DjangoFilterBackend,)
    permission_classes = (PermissaoParaCadastrarLaboratorio,)
    permission_action_classes = {
        "create": [PermissaoParaCadastrarLaboratorio],
        "delete": [PermissaoParaCadastrarLaboratorio],
    }

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return LaboratorioSerializer
        else:
            return LaboratorioCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-laboratorios")
    def lista_nomes_laboratorios(self, request):
        queryset = Laboratorio.objects.all()
        response = {"results": [q.nome for q in queryset]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios-credenciados")
    def lista_nomes_laboratorios_credenciados(self, request):
        laboratorios = self.get_queryset().filter(credenciado=True)
        serializer = LaboratorioCredenciadoSimplesSerializer(
            laboratorios, many=True
        ).data
        response = {"results": serializer}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios")
    def lista_laboratorios_para_filtros(self, request):
        laboratorios = self.get_queryset()
        serializer = LaboratorioSimplesFiltroSerializer(laboratorios, many=True).data
        response = {"results": serializer}
        return Response(response)


class TipoEmbalagemQldModelViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = TipoEmbalagemQld.objects.all().order_by("-criado_em")
    serializer_class = TipoEmbalagemQldSerializer
    permission_classes = (PermissaoParaCadastrarVisualizarEmbalagem,)
    pagination_class = PreRecebimentoPagination
    filterset_class = TipoEmbalagemQldFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return TipoEmbalagemQldSerializer
        else:
            return TipoEmbalagemQldCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-tipos-embalagens")
    def lista_nomes_tipos_embalagens(self, request):
        queryset = TipoEmbalagemQld.objects.all().values_list("nome", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(
        detail=False, methods=["GET"], url_path="lista-abreviacoes-tipos-embalagens"
    )
    def lista_abreviacoes_tipos_embalagens(self, request):
        queryset = TipoEmbalagemQld.objects.all().values_list("abreviacao", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-tipos-embalagens")
    def lista_tipo_embalagem_completa(self, request):
        queryset = self.get_queryset()
        serializer = TipoEmbalagemQldSerializer(queryset, many=True).data
        response = {"results": serializer}
        return Response(response)
