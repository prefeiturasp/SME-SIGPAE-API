from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register(
    "termos",
    viewsets.TermoRecebimentoProvisorioViewSet,
    basename="termos-recebimento-provisorio",
)


urlpatterns = [path("pos-recebimento/", include(router.urls))]
