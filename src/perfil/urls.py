from django.urls import include, path
from rest_framework import routers

from .api import viewsets
from .api.login import LoginView

router = routers.DefaultRouter()

router.register("cadastro", viewsets.UsuarioUpdateViewSet, "Cadastro de Usuários")
router.register(
    "cadastro-com-coresso", viewsets.UsuarioComCoreSSOViewSet, "Cadastro com CoreSSO"
)
router.register("usuarios", viewsets.UsuarioViewSet, "Usuários")
router.register("perfis", viewsets.PerfilViewSet, "Perfis")
router.register(
    "perfis-vinculados", viewsets.PerfisVinculadosViewSet, "Perfis Vinculados"
)
router.register("vinculos", viewsets.VinculoViewSet, "Vinculos")
router.register(
    "planilha-coresso-servidor",
    viewsets.ImportacaoPlanilhaUsuarioServidorCoreSSOViewSet,
    "Planilhas de Importação de Usuário Servidor - CoreSSO",
)
router.register(
    "planilha-coresso-externo",
    viewsets.ImportacaoPlanilhaUsuarioExternoCoreSSOViewSet,
    "Planilhas de Importação de Usuário Externo - CoreSSO",
)
router.register(
    "planilha-coresso-ue-parceira",
    viewsets.ImportacaoPlanilhaUsuarioUEParceiraCoreSSOViewSet,
    "Planilhas de Importação de Usuário UE Parceira - CoreSSO",
)
router.register(
    "confirmar_email/(?P<uuid>[^/]+)/(?P<confirmation_key>[^/]+)",
    viewsets.UsuarioConfirmaEmailViewSet,
    "Confirmar E-mail",
)

urlpatterns = [
    path("", include(router.urls)),
    path("login/", LoginView.as_view()),
]
