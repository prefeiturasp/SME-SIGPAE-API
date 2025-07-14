from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaDashboardLayoutEmbalagem,
    PermissaoParaVisualizarLayoutDeEmbalagem,
    UsuarioEhFornecedor,
    ViewSetActionPermissionMixin,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.filters import (
    LayoutDeEmbalagemFilter,
)

from sme_sigpae_api.pre_recebimento.layout_embalagem.api.serializers.serializer_create import (
    LayoutDeEmbalagemAnaliseSerializer,
    LayoutDeEmbalagemCorrecaoSerializer,
    LayoutDeEmbalagemCreateSerializer,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.api.serializers.serializers import (
    LayoutDeEmbalagemDetalheSerializer,
    LayoutDeEmbalagemSerializer,
    PainelLayoutEmbalagemSerializer,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.api.services import (
    ServiceDashboardLayoutEmbalagem,

)
from sme_sigpae_api.pre_recebimento.layout_embalagem.models import (
    LayoutDeEmbalagem,
)

from ....dados_comuns.api.paginations import DefaultPagination


class LayoutDeEmbalagemModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    lookup_field = "uuid"
    serializer_class = LayoutDeEmbalagemSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LayoutDeEmbalagemFilter
    pagination_class = DefaultPagination
    permission_classes = (PermissaoParaVisualizarLayoutDeEmbalagem,)
    permission_action_classes = {
        "create": [UsuarioEhFornecedor],
        "delete": [UsuarioEhFornecedor],
    }

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return LayoutDeEmbalagem.objects.filter(
                ficha_tecnica__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return LayoutDeEmbalagem.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        serializer_classes_map = {
            "list": LayoutDeEmbalagemSerializer,
            "retrieve": LayoutDeEmbalagemDetalheSerializer,
        }
        return serializer_classes_map.get(
            self.action, LayoutDeEmbalagemCreateSerializer
        )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="codae-aprova-ou-solicita-correcao",
        permission_classes=(PermissaoParaDashboardLayoutEmbalagem,),
    )
    def codae_aprova_ou_solicita_correcao(self, request, uuid):
        serializer = LayoutDeEmbalagemAnaliseSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            layout_atualizado = serializer.save()
            return Response(LayoutDeEmbalagemDetalheSerializer(layout_atualizado).data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardLayoutEmbalagem,),
    )
    def dashboard(self, request):
        dashboard_service = ServiceDashboardLayoutEmbalagem(
            self.get_queryset(),
            LayoutDeEmbalagemFilter,
            PainelLayoutEmbalagemSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="fornecedor-realiza-correcao",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_correcao(self, request, uuid):
        serializer = LayoutDeEmbalagemCorrecaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            layout_corrigido = serializer.save()
            return Response(LayoutDeEmbalagemDetalheSerializer(layout_corrigido).data)

