from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register(
    "termos",
    viewsets.TermoRecebimentoProvisorioViewSet,
    basename="termos-recebimento-provisorio",
)
router.register(
    "memorandos-ocorrencia",
    viewsets.MemorandoOcorrenciaViewSet,
    basename="memorandos-ocorrencia",
)


urlpatterns = [path("pos-recebimento/", include(router.urls))]
