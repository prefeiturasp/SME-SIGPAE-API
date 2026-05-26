from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
)

from src.dados_comuns.fluxo_status import (
    DocumentoDeRecebimentoWorkflow,
)
from src.dados_comuns.permissions import (
    PermissaoParaDashboardDocumentosDeRecebimento,
    PermissaoParaVisualizarDocumentosDeRecebimento,
    PermissaoParaRelatorioDocumentosDeRecebimento,
    UsuarioEhDilogQualidade,
    UsuarioEhFornecedor,
    ViewSetActionPermissionMixin,
)
from src.pre_recebimento.documento_recebimento.api.filters import (
    CronogramaRelatorioDocumentosFilter,
    DocumentoDeRecebimentoFilter,
)
from src.pre_recebimento.documento_recebimento.api.serializers.serializer_create import (
    DocumentoDeRecebimentoAnalisarRascunhoSerializer,
    DocumentoDeRecebimentoAnalisarSerializer,
    DocumentoDeRecebimentoAtualizacaoSerializer,
    DocumentoDeRecebimentoCorrecaoSerializer,
    DocumentoDeRecebimentoCreateSerializer,
)
from src.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    CronogramaRelatorioDocumentosSerializer,
    DocRecebimentoDetalharCodaeSerializer,
    DocRecebimentoDetalharSerializer,
    DocumentoDeRecebimentoSerializer,
    PainelDocumentoDeRecebimentoSerializer,
)
from src.pre_recebimento.documento_recebimento.api.services import (
    ServiceDashboardDocumentosDeRecebimento,
)
from src.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)

from django.db.models import Prefetch, Count
from src.pre_recebimento.cronograma_entrega.models import Cronograma

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

        queryset = (
            DocumentoDeRecebimento.objects.select_related(
                "cronograma",
                "cronograma__empresa",
            )
            .prefetch_related("fichas_documentos__ficha_recebimento")
            .order_by("-criado_em")
        )

        if user.eh_fornecedor:
            return queryset.filter(cronograma__empresa=user.vinculo_atual.instituicao)
        return queryset

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
    
    def _calcular_totalizadores(self, docs_qs):
        contagens = docs_qs.values("status").annotate(total=Count("status"))
        contagens_por_status = {item["status"]: item["total"] for item in contagens}
        return {
            "Total de Documentos Recebidos": sum(contagens_por_status.values()),
            "Total de Pendentes de Aprovação": contagens_por_status.get(DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE, 0),
            "Total de Enviados para Correção": contagens_por_status.get(DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO, 0),
            "Total de Aprovados": contagens_por_status.get(DocumentoDeRecebimentoWorkflow.APROVADO, 0),
        }

    @action(
        detail=False,
        permission_classes=(PermissaoParaRelatorioDocumentosDeRecebimento,),
        methods=["GET"],
        url_path="listagem-relatorio",
    )
    def lista_relatorio(self, request, *args, **kwargs):
        status_documento = request.query_params.getlist("status_documento")

        docs_qs = (
            DocumentoDeRecebimento.objects
            .select_related("laboratorio", "unidade_medida")
            .prefetch_related("datas_fabricacao_e_prazos")
        )
        if status_documento:
            docs_qs = docs_qs.filter(status__in=status_documento)

        queryset = (
            Cronograma.objects.filter(documentos_de_recebimento__isnull=False)
            .select_related("ficha_tecnica__produto", "empresa", "contrato")
            .prefetch_related(Prefetch("documentos_de_recebimento", queryset=docs_qs))
            .order_by("-alterado_em")
            .distinct()
        )

        queryset = CronogramaRelatorioDocumentosFilter(
            request.query_params, queryset=queryset
        ).qs.distinct()

        if status_documento:
            queryset = queryset.filter(
                documentos_de_recebimento__status__in=status_documento
            )

        docs_totais = DocumentoDeRecebimento.objects.filter(
            cronograma__in=queryset
        )
        if status_documento:
            docs_totais = docs_totais.filter(status__in=status_documento)

        totalizadores = self._calcular_totalizadores(docs_totais)

        page = self.paginate_queryset(queryset)
        itens = page if page is not None else queryset

        serializer = CronogramaRelatorioDocumentosSerializer(itens, many=True)
        dados = [item for item in serializer.data if item["documentos"]]

        if page is not None:
            response = self.get_paginated_response(dados)
            response.data["totalizadores"] = totalizadores
            return response
        return Response({"results": dados, "totalizadores": totalizadores})
