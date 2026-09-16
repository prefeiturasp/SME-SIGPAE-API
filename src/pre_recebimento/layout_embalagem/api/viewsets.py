"""Viewsets da API do submódulo de layout de embalagem."""

from django.http import Http404, HttpResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.permissions import (
    PermissaoParaDashboardLayoutEmbalagem,
    PermissaoParaVisualizarLayoutDeEmbalagem,
    UsuarioEhFornecedor,
    ViewSetActionPermissionMixin,
)
from src.pre_recebimento.layout_embalagem.api.serializers.serializer_create import (
    LayoutDeEmbalagemAnaliseSerializer,
    LayoutDeEmbalagemCorrecaoSerializer,
    LayoutDeEmbalagemCreateSerializer,
)
from src.pre_recebimento.layout_embalagem.api.serializers.serializers import (
    LayoutDeEmbalagemDetalheSerializer,
    LayoutDeEmbalagemSerializer,
    PainelLayoutEmbalagemSerializer,
)
from src.pre_recebimento.layout_embalagem.api.services import (
    ServiceDashboardLayoutEmbalagem,
)
from src.pre_recebimento.layout_embalagem.filters import (
    LayoutDeEmbalagemFilter,
)
from src.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
)

from ....dados_comuns.api.paginations import DefaultPagination


class LayoutDeEmbalagemModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    """Viewset de layouts de embalagem.

    Exposto em ``/layouts-de-embalagem/``. A criação e a exclusão são
    restritas ao fornecedor (``UsuarioEhFornecedor``); a visualização é
    controlada por ``PermissaoParaVisualizarLayoutDeEmbalagem``. O
    queryset é filtrado pela empresa do fornecedor quando o usuário é
    fornecedor.
    """

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
        """Retorna os layouts conforme o perfil do usuário.

        Fornecedores veem apenas os layouts das fichas técnicas da própria
        empresa; os demais usuários veem todos os layouts. Ordenado por
        ``-criado_em``.
        """
        user = self.request.user
        if user.eh_fornecedor:
            return LayoutDeEmbalagem.objects.filter(
                ficha_tecnica__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return LayoutDeEmbalagem.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        """Retorna o serializer conforme a ação.

        ``list`` usa ``LayoutDeEmbalagemSerializer`` e ``retrieve`` usa
        ``LayoutDeEmbalagemDetalheSerializer``; as demais ações usam
        ``LayoutDeEmbalagemCreateSerializer``.
        """
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
        """Analisa o layout de embalagem pela CODAE.

        Endpoint ``PATCH /layouts-de-embalagem/{uuid}/codae-aprova-ou-solicita-correcao/``.
        Analisa cada tipo de embalagem: se todos estiverem aprovados, o
        layout é aprovado (``codae_aprova``); caso contrário, a CODAE
        solicita correção (``codae_solicita_correcao``).
        """
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
        """Retorna os dados do dashboard de layouts de embalagem.

        Endpoint ``GET /layouts-de-embalagem/dashboard/``. Usa
        ``ServiceDashboardLayoutEmbalagem`` para montar os cards por
        status conforme o perfil do usuário.
        """
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
        """Registra a correção do layout pelo fornecedor.

        Endpoint ``PATCH /layouts-de-embalagem/{uuid}/fornecedor-realiza-correcao/``.
        O fornecedor reenvia as imagens dos tipos de embalagem reprovados,
        que voltam para ``EM_ANALISE``, e o layout volta para
        ``ENVIADO_PARA_ANALISE`` (``fornecedor_realiza_correcao``).
        """
        serializer = LayoutDeEmbalagemCorrecaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            layout_corrigido = serializer.save()
            return Response(LayoutDeEmbalagemDetalheSerializer(layout_corrigido).data)

    @action(
        detail=True,
        methods=["GET"],
        url_path="download/(?P<imagem_uuid>[^/.]+)",
        permission_classes=(PermissaoParaVisualizarLayoutDeEmbalagem,),
    )
    def download_imagem_assinada(self, request, uuid, imagem_uuid):
        """Gera e retorna a imagem do Layout de Embalagem com rodapé de assinatura digital.

        Segue o mesmo padrão de DocumentoDeRecebimento.download_laudo_assinado.
        Se a imagem for PDF, faz merge com rodapé diretamente.
        Se for PNG/JPG, converte para PDF e depois faz o merge.
        """
        layout = self.get_object()

        try:
            imagem = ImagemDoTipoDeEmbalagem.objects.get(uuid=imagem_uuid)
        except ImagemDoTipoDeEmbalagem.DoesNotExist:
            raise Http404("Imagem não encontrada.")

        if imagem.tipo_de_embalagem.layout_de_embalagem != layout:
            return HttpResponse(
                "A imagem informada não pertence a este Layout de Embalagem.",
                status=401,
            )

        pdf_bytes = layout.arquivo_imagem_assinada(imagem)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{imagem.nome}"'
        return response
