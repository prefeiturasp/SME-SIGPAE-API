from django.urls import include, path
from rest_framework import routers

from .api import viewsets, viewsets_painel

router = routers.DefaultRouter()

router.register(
    "motivos-inclusao-continua",
    viewsets.MotivoInclusaoContinuaViewSet,
    basename="motivo-inclusao-continua",
)
router.register(
    "motivos-inclusao-normal",
    viewsets.MotivoInclusaoNormalViewSet,
    basename="motivo-inclusao-normal",
)
router.register(
    "grupos-inclusao-alimentacao-normal",
    viewsets.GrupoInclusaoAlimentacaoNormalViewSet,
    basename="grupo-inclusao-alimentacao-normal",
)
router.register(
    "inclusoes-alimentacao-continua",
    viewsets.InclusaoAlimentacaoContinuaViewSet,
    basename="inclusao-alimentacao-continua",
)
router.register(
    "inclusoes-alimentacao-da-cei",
    viewsets.InclusaoAlimentacaoDaCEIViewSet,
    basename="inclusao-alimentacao-da-cei",
)
router.register(
    "inclusao-alimentacao-cemei",
    viewsets.InclusaoAlimentacaoCEMEIViewSet,
    basename="inclusao-alimentacao-cemei",
)

router.register(
    "inclusao-alimentacao",
    viewsets_painel.InclusaoAlimentacaoPainelViewSet,
    basename="inclusao-alimentacao",
)

urlpatterns = [path("", include(router.urls))]
