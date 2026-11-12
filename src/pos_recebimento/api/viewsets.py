from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Prefetch, Q
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.api.paginations import DefaultPagination
from src.dados_comuns.constants import DILOG_DIRETORIA
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.relatorios.relatorios import get_pdf_termo_recebimento_provisorio

from ..models import (
    AssinaturaTermoRecebimentoProvisorio,
    CronogramaTermoRecebimentoProvisorio,
    MemorandoOcorrencia,
    TermoRecebimentoProvisorio,
)
from .filters import TermoRecebimentoProvisorioFilter
from .permissions import (
    PermissaoParaAssinarTermoRecebimentoProvisorio,
    PermissaoParaCadastrarTermoRecebimentoProvisorio,
    PermissaoParaGerarPdfTermoRecebimentoProvisorio,
    PermissaoParaRegistrarMemorandoOcorrencia,
    PermissaoParaVisualizarTermoRecebimentoProvisorio,
    usuario_vinculado_a_empresa_fornecedor,
)
from .serializers.serializers import (
    MemorandoOcorrenciaSerializer,
    TermoRecebimentoProvisorioListagemSerializer,
    TermoRecebimentoProvisorioPainelAssinaturaSerializer,
    TermoRecebimentoProvisorioSerializer,
)
from .serializers.serializers_create import (
    MemorandoOcorrenciaCreateSerializer,
    TermoRecebimentoProvisorioCreateSerializer,
)


class TermoRecebimentoProvisorioViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Criação e listagem do Termo de Recebimento Provisório.

    Endpoints:
    - ``POST /`` — Cria o termo (Salvar e Enviar).
    - ``GET /`` — Lista os termos (paginado, com filtros por produto,
      empresa, número de cronograma, status e período de cadastro).
    - ``GET /<uuid>/`` — Detalhe do termo.
    - ``GET /pendentes-assinatura/`` — Painel: termos aguardando assinatura.
    - ``GET /assinados/`` — Painel: termos já assinados.
    - ``PATCH /<uuid>/fiscal-assina-termo/`` — Registra a assinatura de um
      dos três Fiscais do Contrato (assinatura eletrônica com senha).
    """

    lookup_field = "uuid"
    serializer_class = TermoRecebimentoProvisorioCreateSerializer
    queryset = TermoRecebimentoProvisorio.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaCadastrarTermoRecebimentoProvisorio,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TermoRecebimentoProvisorioFilter
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
        queryset = TermoRecebimentoProvisorio.objects.all().order_by("-criado_em")

        if usuario_vinculado_a_empresa_fornecedor(self.request.user):
            queryset = queryset.filter(
                empresa=self.request.user.vinculo_atual.instituicao,
                status__in=[
                    *TermoRecebimentoProvisorio.STATUS_RECEBIDO_FORNECEDOR,
                    TermoRecebimentoProvisorio.ASSINADO_FORNECEDOR,
                ],
            )

        if self.action == "gerar_pdf_termo":
            return queryset.select_related(
                "empresa",
                "contrato",
                "fiscal_1",
                "fiscal_2",
                "fiscal_3",
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
        if self.action == "gerar_pdf_termo":
            return [PermissaoParaGerarPdfTermoRecebimentoProvisorio()]
        if self.action in ("list", "retrieve", *self.ACTIONS_PAINEL_ASSINATURA):
            return [PermissaoParaVisualizarTermoRecebimentoProvisorio()]
        if self.action == "fiscal_assina_termo":
            return [PermissaoParaAssinarTermoRecebimentoProvisorio()]

        return [PermissaoParaCadastrarTermoRecebimentoProvisorio()]

    def get_serializer_class(self):
        """Retorna o serializer adequado conforme a ação."""
        if self.action == "list":
            return TermoRecebimentoProvisorioListagemSerializer
        if self.action == "retrieve":
            return TermoRecebimentoProvisorioSerializer
        if self.action in self.ACTIONS_PAINEL_ASSINATURA:
            return TermoRecebimentoProvisorioPainelAssinaturaSerializer

        return TermoRecebimentoProvisorioCreateSerializer

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

    def _termos_do_fiscal(self, request):
        """Termos em que o usuário da requisição é um dos três fiscais,
        já com os filtros do painel (``numero_contrato``, ``nome_produto``
        e ``nome_empresa``) aplicados.
        """
        usuario = request.user
        return (
            self.filter_queryset(self.get_queryset())
            .filter(Q(fiscal_1=usuario) | Q(fiscal_2=usuario) | Q(fiscal_3=usuario))
            .order_by("-criado_em")
            .distinct()
        )

    def _resposta_paginada(self, queryset):
        """Resposta paginada com o serializer da ação corrente."""
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
        """Termos aguardando assinatura.

        Fiscais: termos com assinatura pendente do fiscal logado (que ainda
        não assinou). DILOG Diretoria: termos com a etapa dos fiscais
        concluída, aguardando a assinatura da diretoria.

        Endpoint: ``GET /pos-recebimento/termos/pendentes-assinatura/``
        """
        if request.user.vinculo_atual.perfil.nome == DILOG_DIRETORIA:
            queryset = (
                self.filter_queryset(self.get_queryset())
                .filter(status=TermoRecebimentoProvisorio.ENVIADO_DILOG)
                .order_by("-criado_em")
                .distinct()
            )
            return self._resposta_paginada(queryset)

        queryset = self._termos_do_fiscal(request).filter(
            status=TermoRecebimentoProvisorio.ENVIADO_FISCAIS
        )
        queryset = queryset.exclude(
            assinaturas__usuario=request.user,
            assinaturas__etapa=AssinaturaTermoRecebimentoProvisorio.FISCAL_CONTRATO,
        )
        return self._resposta_paginada(queryset)

    def _assinatura_do_fiscal(self, campo_fiscal):
        """Exists da assinatura de Fiscal registrada pelo usuário do campo.

        Cada papel de fiscal é verificado individualmente, o que trata
        naturalmente o mesmo usuário repetido em mais de um papel.
        """
        return Exists(
            AssinaturaTermoRecebimentoProvisorio.objects.filter(
                termo=OuterRef("pk"),
                usuario=OuterRef(campo_fiscal),
                etapa=AssinaturaTermoRecebimentoProvisorio.FISCAL_CONTRATO,
            )
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="assinados",
        url_name="assinados",
    )
    def assinados(self, request):
        """Termos dos quais o usuário logado é fiscal, com a etapa dos
        fiscais concluída (todos os fiscais distintos assinaram) ou já
        assinados pelo fornecedor.

        Endpoint: ``GET /pos-recebimento/termos/assinados/``
        """
        queryset = self._termos_do_fiscal(request)
        for campo_fiscal in ("fiscal_1", "fiscal_2", "fiscal_3"):
            queryset = queryset.annotate(
                **{f"assinou_{campo_fiscal}": self._assinatura_do_fiscal(campo_fiscal)}
            )
        queryset = queryset.filter(
            Q(assinou_fiscal_1=True, assinou_fiscal_2=True, assinou_fiscal_3=True)
            | Q(status=TermoRecebimentoProvisorio.ASSINADO_FORNECEDOR)
        )
        return self._resposta_paginada(queryset)

    def perform_create(self, serializer):
        """Persiste o termo, cria as linhas do modelo intermediário
        (cronograma + quantidade total recebida) para cada cronograma do
        payload e inicia o fluxo de assinaturas (``ENVIADO_FISCAIS``)."""
        cronogramas = serializer.validated_data.pop("cronogramas")
        instance = serializer.save(
            criado_por=self.request.user,
            alterado_por=self.request.user,
        )
        for item in cronogramas:
            CronogramaTermoRecebimentoProvisorio.objects.create(
                termo=instance,
                cronograma=item["cronograma"],
                quantidade_total_recebida=item["quantidade_total_recebida"],
            )
        instance.inicia_fluxo(user=self.request.user)

    def _valida_assinatura_fiscal(self, termo, usuario):
        """Valida se o usuário pode assinar o termo como Fiscal do Contrato.

        Retorna a ``Response`` de erro quando a assinatura não é permitida
        ou ``None`` quando a assinatura pode prosseguir.
        """
        if not termo.eh_fiscal(usuario):
            return Response(
                dict(detail="Apenas os Fiscais do Contrato podem assinar o termo."),
                status=status.HTTP_403_FORBIDDEN,
            )
        if termo.status != TermoRecebimentoProvisorio.ENVIADO_FISCAIS:
            return Response(
                dict(
                    detail="O termo não está pendente de assinatura dos Fiscais do Contrato."
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        if termo.usuario_ja_assinou_fiscal(usuario):
            return Response(
                dict(detail="O fiscal já assinou este termo."),
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    def _registra_assinatura_fiscal(self, termo, usuario):
        """Cria a assinatura do fiscal e conclui a etapa dos fiscais
        quando o último fiscal distinto assina."""
        AssinaturaTermoRecebimentoProvisorio.objects.create(
            termo=termo,
            usuario=usuario,
            etapa=AssinaturaTermoRecebimentoProvisorio.FISCAL_CONTRATO,
        )
        termo.salvar_log_transicao(
            status_evento=(
                LogSolicitacoesUsuario.TERMO_RECEBIMENTO_PROVISORIO_ASSINADO_PELO_FISCAL
            ),
            usuario=usuario,
        )
        if termo.etapa_fiscais_concluida:
            termo.fiscais_assinam(user=usuario)

    @transaction.atomic
    @action(
        detail=True,
        methods=["patch"],
        permission_classes=(PermissaoParaAssinarTermoRecebimentoProvisorio,),
        url_path="fiscal-assina-termo",
        url_name="fiscal_assina_termo",
    )
    def fiscal_assina_termo(self, request, uuid=None):
        """Registra a assinatura de um dos três Fiscais do Contrato.

        A senha do usuário é validada (assinatura eletrônica) e a etapa dos
        fiscais é concluída quando a terceira assinatura é registrada,
        encaminhando o termo para a DILOG Diretoria.

        Endpoint: ``PATCH /pos-recebimento/termos/<uuid>/fiscal-assina-termo/``
        """
        usuario = request.user
        if not usuario.verificar_autenticidade(request.data.get("password")):
            return Response(
                dict(
                    detail="Assinatura do termo não foi validada. Verifique sua senha."
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        termo = self.get_object()
        erro = self._valida_assinatura_fiscal(termo, usuario)
        if erro:
            return erro

        try:
            with transaction.atomic():
                self._registra_assinatura_fiscal(termo, usuario)
        except IntegrityError:
            return Response(
                dict(detail="O fiscal já assinou este termo."),
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TermoRecebimentoProvisorioSerializer(
            termo, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["GET"],
        url_path="gerar-pdf-termo",
        url_name="gerar_pdf_termo",
    )
    def gerar_pdf_termo(self, request, uuid=None):
        """Gera o PDF do Termo de Recebimento Provisório.

        Disponível apenas após a conclusão das assinaturas dos três Fiscais
        do Contrato (``etapa_fiscais_concluida``), quando o termo passa ao
        status ``ENVIADO_DILOG``.

        Endpoint: ``GET /pos-recebimento/termos/<uuid>/gerar-pdf-termo/``
        """
        termo = self.get_object()
        if not termo.etapa_fiscais_concluida:
            return Response(
                dict(
                    detail=(
                        "O PDF só está disponível após as assinaturas dos "
                        "três Fiscais do Contrato."
                    )
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return get_pdf_termo_recebimento_provisorio(request, termo)

    def create(self, request, *args, **kwargs):
        """Cria o termo (valida, persiste e retorna 201 com o serializador
        de saída)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        output_serializer = TermoRecebimentoProvisorioSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MemorandoOcorrenciaViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Cadastro de ocorrências do Memorando de Ocorrências.

    Endpoint:
    - ``POST /pos-recebimento/memorandos-ocorrencia/`` — Registra uma
      ocorrência com um ou mais lotes.
    """

    lookup_field = "uuid"
    queryset = MemorandoOcorrencia.objects.all()
    serializer_class = MemorandoOcorrenciaCreateSerializer
    permission_classes = (PermissaoParaRegistrarMemorandoOcorrencia,)

    def create(self, request, *args, **kwargs):
        """Cria o memorando, persiste os lotes e retorna 201."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        output_serializer = MemorandoOcorrenciaSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
