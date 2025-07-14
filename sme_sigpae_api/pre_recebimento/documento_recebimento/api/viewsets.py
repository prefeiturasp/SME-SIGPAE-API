from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
)

from sme_sigpae_api.dados_comuns.fluxo_status import (
    DocumentoDeRecebimentoWorkflow,
)
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaDashboardDocumentosDeRecebimento,
    PermissaoParaVisualizarDocumentosDeRecebimento,
    UsuarioEhDilogQualidade,
    UsuarioEhFornecedor,
    ViewSetActionPermissionMixin,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.filters import (
    DocumentoDeRecebimentoFilter,
)

from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializer_create import (
    DocumentoDeRecebimentoAnalisarRascunhoSerializer,
    DocumentoDeRecebimentoAnalisarSerializer,
    DocumentoDeRecebimentoAtualizacaoSerializer,
    DocumentoDeRecebimentoCorrecaoSerializer,
    DocumentoDeRecebimentoCreateSerializer,

)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocRecebimentoDetalharCodaeSerializer,
    DocRecebimentoDetalharSerializer,
    DocumentoDeRecebimentoSerializer,
    PainelDocumentoDeRecebimentoSerializer,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.services import (
    ServiceDashboardDocumentosDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)

from ....dados_comuns.api.paginations import DefaultPagination


class DocumentoDeRecebimentoModelViewSet(
    ViewSetActionPermissionMixin, viewsets.ModelViewSet
):
    lookup_field = "uuid"
    serializer_class = DocumentoDeRecebimentoSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DocumentoDeRecebimentoFilter
    pagination_class = DefaultPagination
    permission_classes = (PermissaoParaVisualizarDocumentosDeRecebimento,)
    permission_action_classes = {
        "create": [UsuarioEhFornecedor],
        "delete": [UsuarioEhFornecedor],
    }

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return DocumentoDeRecebimento.objects.filter(
                cronograma__empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")
        return DocumentoDeRecebimento.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        user = self.request.user
        retrieve = (
            DocRecebimentoDetalharSerializer
            if user.eh_fornecedor
            else DocRecebimentoDetalharCodaeSerializer
        )
        serializer_classes_map = {
            "list": DocumentoDeRecebimentoSerializer,
            "retrieve": retrieve,
        }
        return serializer_classes_map.get(
            self.action, DocumentoDeRecebimentoCreateSerializer
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardDocumentosDeRecebimento,),
    )
    def dashboard(self, request):
        dashboard_service = ServiceDashboardDocumentosDeRecebimento(
            self.get_queryset().order_by("-alterado_em"),
            DocumentoDeRecebimentoFilter,
            PainelDocumentoDeRecebimentoSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="analise-documentos-rascunho",
        permission_classes=(UsuarioEhDilogQualidade,),
    )
    def codae_analisa_documentos_rascunho(self, request, uuid):
        serializer = DocumentoDeRecebimentoAnalisarRascunhoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documento_recebimento_atualizado = serializer.save()
            return Response(
                DocRecebimentoDetalharCodaeSerializer(
                    documento_recebimento_atualizado
                ).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="analise-documentos",
        permission_classes=(UsuarioEhDilogQualidade,),
    )
    def codae_analisa_documentos(self, request, uuid):
        serializer = DocumentoDeRecebimentoAnalisarSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documento_recebimento_atualizado = serializer.save()
            return Response(
                DocRecebimentoDetalharCodaeSerializer(
                    documento_recebimento_atualizado
                ).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="corrigir-documentos",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_correcao(self, request, uuid):
        serializer = DocumentoDeRecebimentoCorrecaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documentos_corrigidos = serializer.save()
            return Response(
                DocRecebimentoDetalharSerializer(documentos_corrigidos).data
            )

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="atualizar-documentos",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def fornecedor_realiza_atualizacao(self, request, uuid):
        serializer = DocumentoDeRecebimentoAtualizacaoSerializer(
            instance=self.get_object(), data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            documentos_atualizados = serializer.save()
            return Response(
                DocRecebimentoDetalharSerializer(documentos_atualizados).data
            )

    @action(
        detail=True,
        methods=["GET"],
        url_path="download-laudo-assinado",
        permission_classes=(PermissaoParaVisualizarDocumentosDeRecebimento,),
    )
    def download_laudo_assinado(self, request, uuid):
        doc_recebimento = self.get_object()
        if doc_recebimento.status != DocumentoDeRecebimentoWorkflow.APROVADO:
            return HttpResponse(
                "Não é possível fazer download do Laudo assinado de um Documento não Aprovado.",
                status=HTTP_401_UNAUTHORIZED,
            )

        return HttpResponse(
            doc_recebimento.arquivo_laudo_assinado,
            content_type="application/pdf",
        )

