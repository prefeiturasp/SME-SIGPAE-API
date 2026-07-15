from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register(
    "lancamento-diario", viewsets.LancamentoDiarioViewSet, basename="lancamento-diario"
)

urlpatterns = [path("", include(router.urls))]
