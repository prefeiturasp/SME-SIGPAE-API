import environ
from des import urls as des_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from sme_sigpae_api.cardapio.urls import urlpatterns as cardapio_urls
from sme_sigpae_api.dados_comuns.urls import urlpatterns as comuns_urls
from sme_sigpae_api.dieta_especial.urls import urlpatterns as dieta_especial_urls
from sme_sigpae_api.eol_servico.urls import urlpatterns as eol_servico_urls
from sme_sigpae_api.escola.urls import urlpatterns as escola_urls
from sme_sigpae_api.imr.urls import urlpatterns as imr_urls
from sme_sigpae_api.inclusao_alimentacao.urls import urlpatterns as inclusao_urls
from sme_sigpae_api.kit_lanche.urls import urlpatterns as kit_lanche_urls
from sme_sigpae_api.lancamento_inicial.urls import (
    urlpatterns as lancamento_inicial_urls,
)
from sme_sigpae_api.logistica.urls import urlpatterns as logistica_urls
from sme_sigpae_api.medicao_inicial.urls import urlpatterns as medicao_inicial_urls
from sme_sigpae_api.paineis_consolidados.urls import (
    urlpatterns as paineis_consolidados_urls,
)
from sme_sigpae_api.perfil.urls import urlpatterns as perfil_urls
from sme_sigpae_api.pre_recebimento.urls import urlpatterns as pre_recebimento_urls
from sme_sigpae_api.produto.urls import urlpatterns as produto_urls
from sme_sigpae_api.recebimento.urls import urlpatterns as recebimento_urls
from sme_sigpae_api.relatorios.urls import urlpatterns as relatorio_urls
from sme_sigpae_api.terceirizada.urls import urlpatterns as terceirizada_urls

env = environ.Env()

admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path("django-des/", include(des_urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api-token-auth/", TokenObtainPairView.as_view()),
    path("api-token-refresh/", TokenRefreshView.as_view()),
    path("", include("django_prometheus.urls")),
    path("docs-swagger/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs-swagger/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "docs-swagger/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ADDING ROUTERS FROM ALL APPS
urlpatterns += comuns_urls
urlpatterns += eol_servico_urls
urlpatterns += escola_urls
urlpatterns += perfil_urls
urlpatterns += inclusao_urls
urlpatterns += kit_lanche_urls
urlpatterns += lancamento_inicial_urls
urlpatterns += cardapio_urls
urlpatterns += terceirizada_urls
urlpatterns += paineis_consolidados_urls
urlpatterns += dieta_especial_urls
urlpatterns += relatorio_urls
urlpatterns += produto_urls
urlpatterns += logistica_urls
urlpatterns += medicao_inicial_urls
urlpatterns += pre_recebimento_urls
urlpatterns += recebimento_urls
urlpatterns += imr_urls

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
