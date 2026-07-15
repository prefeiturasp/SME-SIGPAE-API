from django.urls import include, path
from rest_framework import routers

from .viewsets import CronogramaSemanalViewSet

router = routers.DefaultRouter()
router.register("cronogramas-semanais", CronogramaSemanalViewSet)

urlpatterns = [path("", include(router.urls))]
