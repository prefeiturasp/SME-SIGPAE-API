from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register("periodos-de-visita", viewsets.PeriodoVisitaModelViewSet)
router.register(
    "rascunho-formulario-supervisao",
    viewsets.FormularioSupervisaoRascunhoModelViewSet,
    basename="rascunho-formulario-supervisao",
)
router.register(
    "formulario-supervisao",
    viewsets.FormularioSupervisaoModelViewSet,
    basename="formulario-supervisao",
)
router.register("formulario-diretor", viewsets.FormularioDiretorModelViewSet)
router.register("utensilios-cozinha", viewsets.UtensilioCozinhaViewSet)
router.register("utensilios-mesa", viewsets.UtensilioMesaViewSet)
router.register("equipamentos", viewsets.EquipamentoViewSet)
router.register("mobiliarios", viewsets.MobiliarioViewSet)
router.register("reparos-e-adaptacoes", viewsets.ReparoEAdaptacaoViewSet)
router.register("insumos", viewsets.InsumoViewSet)

urlpatterns = [
    path("imr/", include(router.urls)),
]
