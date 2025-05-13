from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register(
    "questoes-conferencia",
    viewsets.QuestoesConferenciaModelViewSet,
)
router.register(
    "questoes-por-produto",
    viewsets.QuestoesPorProdutoModelViewSet,
)
router.register(
    "rascunho-ficha-de-recebimento",
    viewsets.FichaDeRecebimentoRascunhoViewSet,
    basename="rascunho-ficha-de-recebimento",
)
router.register(
    "fichas-de-recebimento",
    viewsets.FichaRecebimentoModelViewSet,
    basename="fichas-de-recebimento",
)

urlpatterns = [path("", include(router.urls))]
