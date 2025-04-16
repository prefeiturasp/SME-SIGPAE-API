from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sme_sigpae_api.dados_comuns.constants import FILTRO_PADRAO_PEDIDOS, SEM_FILTRO
from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaRecuperarDietaEspecial,
    UsuarioCODAEGestaoAlimentacao,
)
from sme_sigpae_api.paineis_consolidados.api.constants import (
    AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    AUTORIZADOS,
    AUTORIZADOS_DIETA_ESPECIAL,
    CANCELADOS,
    CANCELADOS_DIETA_ESPECIAL,
    INATIVAS_DIETA_ESPECIAL,
    INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
    NEGADOS,
    NEGADOS_DIETA_ESPECIAL,
    PENDENTES_AUTORIZACAO,
    PENDENTES_AUTORIZACAO_DIETA_ESPECIAL,
    QUESTIONAMENTOS,
    TIPO_VISAO,
    TIPO_VISAO_SOLICITACOES,
)
from sme_sigpae_api.paineis_consolidados.api.serializers import SolicitacoesSerializer
from sme_sigpae_api.paineis_consolidados.api.viewsets import SolicitacoesViewSet
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesCODAE
from sme_sigpae_api.paineis_consolidados.solicitacoes_codae.api.filters import (
    SolicitacoesCODAEFilter,
)


class CODAESolicitacoesViewSet(SolicitacoesViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = SolicitacoesCODAE.objects.all()
    serializer_class = SolicitacoesSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SolicitacoesCODAEFilter

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}/{FILTRO_PADRAO_PEDIDOS}/{TIPO_VISAO}",
    )
    def pendentes_autorizacao_secao_pendencias(
        self, request, filtro_aplicado=SEM_FILTRO, tipo_visao=TIPO_VISAO_SOLICITACOES
    ):
        query_set = SolicitacoesCODAE.get_pendentes_autorizacao(filtro=filtro_aplicado)
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        response = {
            "results": self._agrupa_por_tipo_visao(
                tipo_visao=tipo_visao, query_set=query_set
            )
        }

        return Response(response)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}/{FILTRO_PADRAO_PEDIDOS}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def pendentes_autorizacao(self, request, filtro_aplicado=SEM_FILTRO):
        query_set = SolicitacoesCODAE.get_pendentes_autorizacao(filtro=filtro_aplicado)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=f"{PENDENTES_AUTORIZACAO}",
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def pendentes_autorizacao_sem_filtro(self, request):
        query_set = SolicitacoesCODAE.get_pendentes_autorizacao()
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=AUTORIZADOS,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def autorizados(self, request):
        query_set = SolicitacoesCODAE.get_autorizados()
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=NEGADOS,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def negados(self, request):
        query_set = SolicitacoesCODAE.get_negados()
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=CANCELADOS,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def cancelados(self, request):
        query_set = SolicitacoesCODAE.get_cancelados()
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=QUESTIONAMENTOS,
        permission_classes=(UsuarioCODAEGestaoAlimentacao,),
    )
    def questionamentos(self, request):
        query_set = SolicitacoesCODAE.get_questionamentos()
        query_set = SolicitacoesCODAE.busca_filtro(query_set, request.query_params)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=PENDENTES_AUTORIZACAO_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def pendentes_autorizacao_dieta_especial(self, request):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_pendentes_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=AUTORIZADOS_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def autorizados_dieta_especial(self, request):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_autorizados_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=NEGADOS_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def negados_dieta_especial(self, request):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_negados_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=CANCELADOS_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def cancelados_dieta_especial(self, request):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_cancelados_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def autorizadas_temporariamente_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_autorizadas_temporariamente_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def inativas_temporariamente_dieta_especial(self, request, dre_uuid=None):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_inativas_temporariamente_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)

    @action(
        detail=False,
        methods=["GET"],
        url_path=INATIVAS_DIETA_ESPECIAL,
        permission_classes=(
            IsAuthenticated,
            PermissaoParaRecuperarDietaEspecial,
        ),
    )
    def inativas_dieta_especial(self, request):
        tem_parametro_sem_paginacao = request.GET.get("sem_paginacao", False)
        query_set = SolicitacoesCODAE.get_inativas_dieta_especial()
        query_set = SolicitacoesCODAE.busca_filtro_dietas_especiais(
            query_set, request.query_params
        )
        if tem_parametro_sem_paginacao:
            return self._retorno_base(query_set, True)
        return self._retorno_base(query_set)
