from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register("dias-letivos", viewsets.DiaLetivoViewSet, basename="dias-letivos")

urlpatterns = [path("", include(router.urls))]
