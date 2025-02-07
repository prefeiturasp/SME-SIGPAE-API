from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from sme_sigpae_api.dados_comuns.permissions import (
    UsuarioCODAEGestaoProduto,
    UsuarioTerceirizada,
)
from sme_sigpae_api.dados_comuns.utils import ordena_queryset_por_ultimo_log
from sme_sigpae_api.produto.api.dashboard.utils import (
    filtra_produtos_da_terceirizada,
    filtra_reclamacoes_por_usuario,
    filtrar_query_params,
    retorna_produtos_homologados,
    trata_parcialmente_homologados_ou_suspensos,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    HomologacaoProdutoPainelGerencialSerializer,
)
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.produto.utils import DashboardPagination


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
        query_set = self.get_queryset()
        query_set = filtrar_query_params(request, query_set)
        query_set = trata_parcialmente_homologados_ou_suspensos(
            request, query_set, vinculo_suspenso=False
        )
        query_set = retorna_produtos_homologados(query_set)
        lista = ordena_queryset_por_ultimo_log(query_set)
        page = self.paginate_queryset(lista)
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
        query_set = self.get_queryset().filter(
            status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO
        )
        query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
        lista = ordena_queryset_por_ultimo_log(query_set)
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
        query_set = self.get_queryset().exclude(
            status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO
        )
        query_set = filtrar_query_params(request, query_set, filtra_por_edital=True)
        query_set = trata_parcialmente_homologados_ou_suspensos(
            request, query_set, vinculo_suspenso=True
        )
        lista = ordena_queryset_por_ultimo_log(query_set)
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
        query_set = self.get_queryset().filter(
            status__in=[
                HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
                HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
                HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_UE,
                HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_NUTRISUPERVISOR,
                HomologacaoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
                HomologacaoProduto.workflow_class.UE_RESPONDEU_QUESTIONAMENTO,
                HomologacaoProduto.workflow_class.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
            ]
        )
        query_set = filtrar_query_params(request, query_set)
        query_set = filtra_reclamacoes_por_usuario(request, query_set)
        lista = ordena_queryset_por_ultimo_log(query_set)
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
        permission_classes=[UsuarioTerceirizada | UsuarioCODAEGestaoProduto],
    )
    def dashboard_pendente_homologacao(self, request):
        query_set = self.get_queryset().filter(
            status=HomologacaoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO
        )
        query_set = filtrar_query_params(request, query_set, filtra_por_edital=False)
        lista = ordena_queryset_por_ultimo_log(query_set)
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
        permission_classes=[UsuarioTerceirizada | UsuarioCODAEGestaoProduto],
    )
    def dashboard_correcao_de_produtos(self, request):
        query_set = self.get_queryset().filter(
            status=HomologacaoProduto.workflow_class.CODAE_QUESTIONADO
        )
        query_set = filtrar_query_params(request, query_set)
        query_set = filtra_produtos_da_terceirizada(request, query_set)
        lista = ordena_queryset_por_ultimo_log(query_set)
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
        permission_classes=[UsuarioTerceirizada | UsuarioCODAEGestaoProduto],
    )
    def dashboard_aguardando_amostra_analise_sensorial(self, request):
        query_set = self.get_queryset().filter(
            status=HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_SENSORIAL
        )
        query_set = filtrar_query_params(request, query_set)
        query_set = filtra_produtos_da_terceirizada(request, query_set)
        lista = ordena_queryset_por_ultimo_log(query_set)
        page = self.paginate_queryset(lista)
        serializer = self.get_serializer(
            page, context={"workflow": "CODAE_PEDIU_ANALISE_SENSORIAL"}, many=True
        )
        return self.get_paginated_response(serializer.data)
