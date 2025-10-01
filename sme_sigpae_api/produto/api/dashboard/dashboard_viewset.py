from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from sme_sigpae_api.dados_comuns.permissions import (
    UsuarioCODAEGestaoProduto,
    UsuarioEmpresaGenerico,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    HomologacaoProdutoPainelGerencialSerializer,
)
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.produto.utils.genericos import DashboardPagination
from sme_sigpae_api.produto.utils.query_produtos_por_status import (
    produtos_aguardando_amostra_analise_sensorial,
    produtos_aguardando_analise_reclamacao,
    produtos_correcao_de_produto,
    produtos_homologados,
    produtos_nao_homologados,
    produtos_pendente_homologacao,
    produtos_questionamento_da_codae,
    produtos_suspensos,
)


class HomologacaoProdutoDashboardViewSet(ModelViewSet):
    lookup_field = "uuid"
    serializer_class = HomologacaoProdutoPainelGerencialSerializer
    queryset = HomologacaoProduto.objects.all()
    pagination_class = DashboardPagination

    @action(
        detail=False,
        methods=["GET"],
        url_path="homologados",
        pagination_class=DashboardPagination,
    )
    def dashboard_homologados(self, request):
        lista_produtos_homologados = produtos_homologados(request)
        page = self.paginate_queryset(lista_produtos_homologados)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_HOMOLOGADO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="nao-homologados",
        pagination_class=DashboardPagination,
    )
    def dashboard_nao_homologados(self, request):
        lista = produtos_nao_homologados(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_NAO_HOMOLOGADO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="suspensos",
        pagination_class=DashboardPagination,
    )
    def dashboard_suspensos(self, request):
        lista = produtos_suspensos(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_SUSPENDEU"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="aguardando-analise-reclamacao",
        pagination_class=DashboardPagination,
    )
    def dashboard_aguardando_analise_reclamacao(self, request):
        lista = produtos_aguardando_analise_reclamacao(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "ESCOLA_OU_NUTRICIONISTA_RECLAMOU"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="pendente-homologacao",
        pagination_class=DashboardPagination,
        permission_classes=[UsuarioEmpresaGenerico | UsuarioCODAEGestaoProduto],
    )
    def dashboard_pendente_homologacao(self, request):
        lista = produtos_pendente_homologacao(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_PENDENTE_HOMOLOGACAO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="correcao-de-produtos",
        pagination_class=DashboardPagination,
        permission_classes=[UsuarioEmpresaGenerico | UsuarioCODAEGestaoProduto],
    )
    def dashboard_correcao_de_produtos(self, request):
        lista = produtos_correcao_de_produto(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_QUESTIONADO"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="aguardando-amostra-analise-sensorial",
        pagination_class=DashboardPagination,
        permission_classes=[UsuarioEmpresaGenerico | UsuarioCODAEGestaoProduto],
    )
    def dashboard_aguardando_amostra_analise_sensorial(self, request):
        lista = produtos_aguardando_amostra_analise_sensorial(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_PEDIU_ANALISE_SENSORIAL"}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="questionamento-da-codae",
        pagination_class=DashboardPagination,
    )
    def dashboard_questionamento_da_codae(self, request):
        lista = produtos_questionamento_da_codae(request)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_PEDIU_ANALISE_RECLAMACAO"}, many=True
        )
        return self.get_paginated_response(serializer.data)
