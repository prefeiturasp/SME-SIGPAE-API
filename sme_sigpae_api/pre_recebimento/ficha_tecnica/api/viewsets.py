from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
)

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaAnalisarFichaTecnica,
    PermissaoParaDashboardFichaTecnica,
    PermissaoParaVisualizarCronograma,
    PermissaoParaVisualizarFichaTecnica,
    UsuarioEhFornecedor,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.filters import (
    FichaTecnicaFilter,
)

from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializer_create import (
    AnaliseFichaTecnicaCreateSerializer,
    AnaliseFichaTecnicaRascunhoSerializer,
    CorrecaoFichaTecnicaSerializer,
    FichaTecnicaAtualizacaoSerializer,
    FichaTecnicaCreateSerializer,
    FichaTecnicaRascunhoSerializer,

)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaComAnaliseDetalharSerializer,
    FichaTecnicaCronogramaSerializer,
    FichaTecnicaDetalharSerializer,
    FichaTecnicaListagemSerializer,
    FichaTecnicaSimplesSerializer,
    PainelFichaTecnicaSerializer,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.services import (
    ServiceDashboardFichaTecnica,
)

from ....dados_comuns.api.paginations import DefaultPagination
from ....relatorios.relatorios import get_pdf_ficha_tecnica
from ..models import FichaTecnicaDoProduto


class FichaTecnicaRascunhoViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    lookup_field = "uuid"
    serializer_class = FichaTecnicaRascunhoSerializer
    queryset = FichaTecnicaDoProduto.objects.all().order_by("-criado_em")
    permission_classes = (UsuarioEhFornecedor,)


class FichaTecnicaModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = FichaTecnicaRascunhoSerializer
    queryset = FichaTecnicaDoProduto.objects.all().order_by("-criado_em")
    permission_classes = (PermissaoParaVisualizarFichaTecnica,)
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FichaTecnicaFilter

    def get_queryset(self):
        user = self.request.user
        if user.eh_fornecedor:
            return FichaTecnicaDoProduto.objects.filter(
                empresa=user.vinculo_atual.instituicao
            ).order_by("-criado_em")

        return FichaTecnicaDoProduto.objects.all().order_by("-criado_em")

    def get_serializer_class(self):
        serializer_classes_map = {
            "list": FichaTecnicaListagemSerializer,
            "retrieve": FichaTecnicaDetalharSerializer,
            "create": FichaTecnicaCreateSerializer,
            "update": FichaTecnicaCreateSerializer,
        }

        return serializer_classes_map.get(self.action, FichaTecnicaRascunhoSerializer)

    def create(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or super().update(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["GET"],
        url_path="dashboard",
        permission_classes=(PermissaoParaDashboardFichaTecnica,),
    )
    def dashboard(self, request):
        qs = FichaTecnicaDoProduto.objects.order_by("-alterado_em")
        dashboard_service = ServiceDashboardFichaTecnica(
            qs,
            FichaTecnicaFilter,
            PainelFichaTecnicaSerializer,
            request,
        )

        return Response({"results": dashboard_service.get_dados_dashboard()})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO)

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-aprovadas",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_aprovadas(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.filter(status=FichaTecnicaDoProduto.workflow_class.APROVADA)

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-cronograma",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_cronograma(self, request, **kwargs):
        qs = (
            self.get_queryset()
            .exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO)
            .exclude(cronograma__isnull=False)
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-layout-embalagem",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_layout_embalagem(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO).exclude(
            layout_embalagem__isnull=False
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=False,
        methods=["GET"],
        url_path="lista-simples-sem-questoes-conferencia",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def lista_simples_sem_questoes_conferencia(self, request, **kwargs):
        usuario = self.request.user

        qs = (
            self.get_queryset().filter(empresa=usuario.vinculo_atual.instituicao)
            if usuario.eh_empresa
            else self.get_queryset()
        )

        qs = qs.exclude(status=FichaTecnicaDoProduto.workflow_class.RASCUNHO).exclude(
            questoes_conferencia__isnull=False
        )

        return Response({"results": FichaTecnicaSimplesSerializer(qs, many=True).data})

    @action(
        detail=True,
        methods=["GET"],
        url_path="dados-cronograma",
        permission_classes=(PermissaoParaVisualizarCronograma,),
    )
    def dados_cronograma(self, request, **kwargs):
        return Response(FichaTecnicaCronogramaSerializer(self.get_object()).data)

    @action(
        detail=True,
        methods=["GET"],
        url_path="detalhar-com-analise",
        permission_classes=(PermissaoParaVisualizarFichaTecnica,),
    )
    def detalhar_com_analise(self, request, **kwargs):
        return Response(
            FichaTecnicaComAnaliseDetalharSerializer(
                self.get_object(),
                context=self.get_serializer_context(),
            ).data
        )

    @action(
        detail=True,
        methods=["POST", "PUT"],
        url_path="rascunho-analise-gpcodae",
        permission_classes=(PermissaoParaAnalisarFichaTecnica,),
    )
    def rascunho_analise_gpcodae(self, request, *args, **kwargs):
        ficha_tecnica = self.get_object()
        analise = ficha_tecnica.analises.last()
        criado_por = self.request.user

        serializer = AnaliseFichaTecnicaRascunhoSerializer(
            instance=analise,
            data=request.data,
            context={
                "ficha_tecnica": ficha_tecnica,
                "criado_por": criado_por,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=HTTP_201_CREATED if analise is None else HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["POST", "PUT"],
        url_path="analise-gpcodae",
        permission_classes=(PermissaoParaAnalisarFichaTecnica,),
    )
    def analise_gpcodae(self, request, *args, **kwargs):
        ficha_tecnica = self.get_object()
        analise = ficha_tecnica.analises.last()
        criado_por = self.request.user

        serializer = AnaliseFichaTecnicaCreateSerializer(
            instance=analise,
            data=request.data,
            context={
                "ficha_tecnica": ficha_tecnica,
                "criado_por": criado_por,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=HTTP_201_CREATED if analise is None else HTTP_200_OK)

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="correcao-fornecedor",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def correcao_fornecedor(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or self._processa_correcao(request, *args, **kwargs)

    def _processa_correcao(self, request, *args, **kwargs):
        serializer = CorrecaoFichaTecnicaSerializer(
            instance=self.get_object(),
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(HTTP_200_OK)

    @action(
        detail=True,
        methods=["PATCH"],
        url_path="atualizacao-fornecedor",
        permission_classes=(UsuarioEhFornecedor,),
    )
    def atualizacao_fornecedor(self, request, *args, **kwargs):
        return self._verificar_autenticidade_usuario(
            request, *args, **kwargs
        ) or self._processa_atualizacao(request, *args, **kwargs)

    def _processa_atualizacao(self, request, *args, **kwargs):
        serializer = FichaTecnicaAtualizacaoSerializer(
            instance=self.get_object(),
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(HTTP_200_OK)

    def _verificar_autenticidade_usuario(self, request, *args, **kwargs):
        usuario = request.user
        password = request.data.pop("password", "")

        if not usuario.verificar_autenticidade(password):
            return Response(
                {
                    "Senha inválida": "em caso de esquecimento de senha, solicite a recuperação e tente novamente."
                },
                status=HTTP_401_UNAUTHORIZED,
            )

    @action(detail=True, methods=["GET"], url_path="gerar-pdf-ficha")
    def gerar_pdf_ficha(self, request, uuid=None):
        ficha = self.get_object()
        return get_pdf_ficha_tecnica(request, ficha)
