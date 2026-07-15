from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()
router.register(
    "dados-usuario-eol-completo",
    viewsets.DadosUsuarioEOLCompletoViewSet,
    basename="Dados Usuario EOL Completo",
)
router.register(
    "dados-alunos-eol", viewsets.DadosAlunoEOLViewSet, basename="Dados Aluno EOL"
)

urlpatterns = [
    path("", include(router.urls)),
]
