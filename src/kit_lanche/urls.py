from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register("kit-lanches", viewsets.KitLancheViewSet, basename="kit-lanches")

router.register(
    "solicitacoes-kit-lanche-avulsa",
    viewsets.SolicitacaoKitLancheAvulsaViewSet,
    basename="solicitacao-kit-lanche-avulsa",
)

router.register(
    "solicitacoes-kit-lanche-cei-avulsa",
    viewsets.SolicitacaoKitLancheCEIAvulsaViewSet,
    basename="solicitacao-kit-lanche-cei-avulsa",
)

router.register(
    "solicitacoes-kit-lanche-unificada",
    viewsets.SolicitacaoKitLancheUnificadaViewSet,
    basename="solicitacao-kit-lanche-unificada",
)

router.register(
    "solicitacao-kit-lanche-cemei",
    viewsets.SolicitacaoKitLancheCEMEIViewSet,
    basename="solicitacao-kit-lanche-cemei",
)

urlpatterns = [path("", include(router.urls))]
