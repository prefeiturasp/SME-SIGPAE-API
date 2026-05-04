from django.urls import include, path
from rest_framework import routers

from .api import viewsets
from .api.soup import views as soup_views

router = routers.DefaultRouter()

router.register(
    "solicitacao-remessa",
    viewsets.SolicitacaoModelViewSet,
    basename="solicitacao-remessa",
)
router.register(
    "solicitacao-remessa-envio",
    viewsets.SolicitacaoEnvioEmMassaModelViewSet,
    basename="solicitacao-remessa-envio",
)
router.register(
    "solicitacao-remessa-cancelamento",
    viewsets.SolicitacaoCancelamentoModelViewSet,
    basename="solicitacao-remessa-cancelamento",
)
router.register(
    "guias-da-requisicao",
    viewsets.GuiaDaRequisicaoModelViewSet,
    basename="guias-da-requisicao",
)
router.register(
    "alimentos-da-guia",
    viewsets.AlimentoDaGuiaModelViewSet,
    basename="alimentos-da-guia",
)
router.register(
    "conferencia-da-guia",
    viewsets.ConferenciaDaGuiaModelViewSet,
    basename="conferencia-da-guia",
)
router.register(
    "conferencia-da-guia-com-ocorrencia",
    viewsets.ConferenciaDaGuiaComOcorrenciaModelViewSet,
    basename="conferencia-da-guia-com-ocorrencia",
)
router.register(
    "conferencia-individual",
    viewsets.ConferenciaindividualModelViewSet,
    basename="conferencia-individual",
)
router.register(
    "insucesso-de-entrega",
    viewsets.InsucessoDeEntregaGuiaModelViewSet,
    basename="insucesso-de-entrega",
)
router.register(
    "solicitacao-de-alteracao-de-requisicao",
    viewsets.SolicitacaoDeAlteracaoDeRequisicaoViewset,
    basename="solicitacao-de-alteracao-de-requisicao",
)
router.register(
    "notificacao-guias-com-ocorrencias",
    viewsets.NotificacaoOcorrenciaGuiaModelViewSet,
    basename="notificacao-guias-com-ocorrencias",
)

router.register(
    "webserver/solicitacao-remessa/wsdl",
    soup_views.WSDLSolicitacaoServiceViewSet,
    basename="solicitacao-remessa-wsdl",
)

urlpatterns = [
    path("", include(router.urls)),
    path("webserver/solicitacao-remessa/", soup_views.solicitacao_application),
]
