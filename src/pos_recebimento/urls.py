from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register(
    "termos",
    viewsets.TermoRecebimentoDefinitivoViewSet,
    basename="termos-recebimento-definitivo",
)


urlpatterns = [path("pos-recebimento/", include(router.urls))]
