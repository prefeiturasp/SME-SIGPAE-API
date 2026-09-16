"""Viewsets da API do submódulo de qualidade."""

from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.dados_comuns.permissions import (
    PermissaoParaCadastrarLaboratorio,
    PermissaoParaCadastrarVisualizarEmbalagem,
    ViewSetActionPermissionMixin,
)
from src.pre_recebimento.base.api.paginations import (
    PreRecebimentoPagination,
)
from src.pre_recebimento.qualidade.api.filters import (
    LaboratorioFilter,
    TipoEmbalagemQldFilter,
)
from src.pre_recebimento.qualidade.api.serializers.serializer_create import (
    LaboratorioCreateSerializer,
    TipoEmbalagemQldCreateSerializer,
)
from src.pre_recebimento.qualidade.api.serializers.serializers import (
    LaboratorioCredenciadoSimplesSerializer,
    LaboratorioSerializer,
    LaboratorioSimplesFiltroSerializer,
    TipoEmbalagemQldSerializer,
)
from src.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class LaboratorioModelViewSet(ViewSetActionPermissionMixin, viewsets.ModelViewSet):
    """Viewset de laboratórios.

    Exposto em ``/laboratorios/``, com CRUD completo. A criação e a
    exclusão exigem a permissão ``PermissaoParaCadastrarLaboratorio``
    (apenas ``DILOG_QUALIDADE`` e ``COORDENADOR_CODAE_DILOG_LOGISTICA``).
    """

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
        """Retorna o serializer conforme a ação.

        ``retrieve`` e ``list`` usam ``LaboratorioSerializer`` (com
        contatos); as demais ações usam ``LaboratorioCreateSerializer``,
        que exige os dados cadastrais e cria/atualiza os contatos.
        """
        if self.action in ["retrieve", "list"]:
            return LaboratorioSerializer
        else:
            return LaboratorioCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-laboratorios")
    def lista_nomes_laboratorios(self, request):
        """Lista apenas os nomes de todos os laboratórios.

        Endpoint ``GET /laboratorios/lista-nomes-laboratorios/``, usado
        para popular seletores no frontend.
        """
        queryset = Laboratorio.objects.all()
        response = {"results": [q.nome for q in queryset]}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios-credenciados")
    def lista_nomes_laboratorios_credenciados(self, request):
        """Lista os laboratórios credenciados.

        Endpoint ``GET /laboratorios/lista-laboratorios-credenciados/``.
        Retorna ``uuid`` e ``nome`` apenas dos laboratórios com
        ``credenciado = True``.
        """
        laboratorios = self.get_queryset().filter(credenciado=True)
        serializer = LaboratorioCredenciadoSimplesSerializer(
            laboratorios, many=True
        ).data
        response = {"results": serializer}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-laboratorios")
    def lista_laboratorios_para_filtros(self, request):
        """Lista os laboratórios para uso em filtros.

        Endpoint ``GET /laboratorios/lista-laboratorios/``. Retorna
        ``nome`` e ``cnpj`` de todos os laboratórios.
        """
        laboratorios = self.get_queryset()
        serializer = LaboratorioSimplesFiltroSerializer(laboratorios, many=True).data
        response = {"results": serializer}
        return Response(response)


class TipoEmbalagemQldModelViewSet(viewsets.ModelViewSet):
    """Viewset de tipos de embalagem (qualidade).

    Exposto em ``/tipos-embalagens/``, com CRUD completo. O acesso é
    controlado por ``PermissaoParaCadastrarVisualizarEmbalagem`` (perfis
    ``DILOG_QUALIDADE``, ``DILOG_CRONOGRAMA`` e
    ``COORDENADOR_CODAE_DILOG_LOGISTICA``).
    """

    lookup_field = "uuid"
    queryset = TipoEmbalagemQld.objects.all().order_by("-criado_em")
    serializer_class = TipoEmbalagemQldSerializer
    permission_classes = (PermissaoParaCadastrarVisualizarEmbalagem,)
    pagination_class = PreRecebimentoPagination
    filterset_class = TipoEmbalagemQldFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_serializer_class(self):
        """Retorna o serializer conforme a ação.

        ``retrieve`` e ``list`` usam ``TipoEmbalagemQldSerializer``; as
        demais ações usam ``TipoEmbalagemQldCreateSerializer``, que
        normaliza nome e abreviação em letras maiúsculas.
        """
        if self.action in ["retrieve", "list"]:
            return TipoEmbalagemQldSerializer
        else:
            return TipoEmbalagemQldCreateSerializer

    @action(detail=False, methods=["GET"], url_path="lista-nomes-tipos-embalagens")
    def lista_nomes_tipos_embalagens(self, request):
        """Lista apenas os nomes dos tipos de embalagem.

        Endpoint ``GET /tipos-embalagens/lista-nomes-tipos-embalagens/``,
        usado para popular seletores no frontend.
        """
        queryset = TipoEmbalagemQld.objects.all().values_list("nome", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(
        detail=False, methods=["GET"], url_path="lista-abreviacoes-tipos-embalagens"
    )
    def lista_abreviacoes_tipos_embalagens(self, request):
        """Lista apenas as abreviações dos tipos de embalagem.

        Endpoint
        ``GET /tipos-embalagens/lista-abreviacoes-tipos-embalagens/``,
        usado para popular seletores no frontend.
        """
        queryset = TipoEmbalagemQld.objects.all().values_list("abreviacao", flat=True)
        response = {"results": queryset}
        return Response(response)

    @action(detail=False, methods=["GET"], url_path="lista-tipos-embalagens")
    def lista_tipo_embalagem_completa(self, request):
        """Lista os tipos de embalagem completos.

        Endpoint ``GET /tipos-embalagens/lista-tipos-embalagens/``.
        Retorna todos os campos serializados de cada tipo de embalagem.
        """
        queryset = self.get_queryset()
        serializer = TipoEmbalagemQldSerializer(queryset, many=True).data
        response = {"results": serializer}
        return Response(response)
