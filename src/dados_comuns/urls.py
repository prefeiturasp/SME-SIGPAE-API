from django.urls import include, path, re_path
from rest_framework import routers

from .api import viewsets
from .consumers import SolicitacoesAbertasConsumer
from .views import send_test_email, test_visualiza_email

router = routers.DefaultRouter()
router.register("api-version", viewsets.ApiVersion, basename="Version")
router.register("email", viewsets.ConfiguracaoEmailViewSet, basename="Email")
router.register("dias-semana", viewsets.DiasDaSemanaViewSet, basename="Dias da semana")
router.register(
    "tempos-passeio", viewsets.TempoDePasseioViewSet, basename="Tempos de passeio"
)
router.register("dias-uteis", viewsets.DiasUteisViewSet, basename="Dias úteis")
router.register("feriados-ano", viewsets.FeriadosAnoViewSet, basename="Feriados no Ano")
router.register(
    "templates-mensagem",
    viewsets.TemplateMensagemViewSet,
    basename="Configuração de mensagem",
)
router.register(
    "perguntas-frequentes",
    viewsets.PerguntaFrequenteViewSet,
    basename="Perguntas Frequentes",
)
router.register(
    "categorias-pergunta-frequente",
    viewsets.CategoriaPerguntaFrequenteViewSet,
    basename="Categorias de Pergunta Frequente",
)
router.register("notificacoes", viewsets.NotificacaoViewSet, basename="Notificações")
router.register("downloads", viewsets.CentralDeDownloadViewSet, basename="Downloads")
router.register(
    "solicitacoes-abertas",
    viewsets.SolicitacaoAbertaViewSet,
    basename="Solicitações abertas",
)

urlpatterns = [
    path("", include(router.urls)),
    path("email-teste/", send_test_email, name="enviar_email_teste"),
    path("visualiza-email/", test_visualiza_email, name="email_teste"),
]

ws_urlpatterns = [
    re_path(r"ws/solicitacoes-abertas/", SolicitacoesAbertasConsumer.as_asgi())
]
