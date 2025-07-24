from django.urls import include, path
from rest_framework import routers

from sme_sigpae_api.paineis_consolidados.api import viewsets
from sme_sigpae_api.paineis_consolidados.solicitacoes_codae.api.viewsets import (
    CODAESolicitacoesViewSet,
)
from sme_sigpae_api.paineis_consolidados.solicitacoes_escola.api.viewsets import (
    EscolaSolicitacoesViewSet,
)

router = routers.DefaultRouter()
router.register(
    "solicitacoes-genericas", viewsets.SolicitacoesViewSet, "solicitacoes_genericas"
)
router.register("codae-solicitacoes", CODAESolicitacoesViewSet, "codae_solicitacoes")
router.register(
    "nutrisupervisao-solicitacoes",
    viewsets.NutrisupervisaoSolicitacoesViewSet,
    "nutrisupervisao_solicitacoes",
)
router.register(
    "nutrimanifestacao-solicitacoes",
    viewsets.NutrimanifestacaoSolicitacoesViewSet,
    "nutrimanifestacao_solicitacoes",
)
router.register("escola-solicitacoes", EscolaSolicitacoesViewSet, "escola_solicitacoes")
router.register(
    "diretoria-regional-solicitacoes",
    viewsets.DRESolicitacoesViewSet,
    "dre_solicitacoes",
)
router.register(
    "terceirizada-solicitacoes",
    viewsets.TerceirizadaSolicitacoesViewSet,
    "terceirizada_solicitacoes",
)

urlpatterns = [
    path("", include(router.urls)),
]
