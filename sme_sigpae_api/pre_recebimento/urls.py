from django.urls import include, path
from rest_framework import routers

from .cronograma_entrega.api import viewsets as cronograma_viewsets
from .qualidade.api import viewsets as qualidade_viewsets
from .base.api import viewsets as base_viewsets
from .documento_recebimento.api import viewsets as documento_viewsets
from .ficha_tecnica.api import viewsets as ficha_tecnica_viewsets
from .layout_embalagem.api import viewsets as layout_viewsets

router = routers.DefaultRouter()

router.register("cronogramas", cronograma_viewsets.CronogramaModelViewSet)
router.register("laboratorios", qualidade_viewsets.LaboratorioModelViewSet)
router.register("tipos-embalagens", qualidade_viewsets.TipoEmbalagemQldModelViewSet)
router.register("unidades-medida-logistica", base_viewsets.UnidadeMedidaViewset)
router.register(
    "layouts-de-embalagem",
    layout_viewsets.LayoutDeEmbalagemModelViewSet,
    basename="layouts-de-embalagem",
)
router.register(
    "documentos-de-recebimento",
    documento_viewsets.DocumentoDeRecebimentoModelViewSet,
    basename="documentos-de-recebimento",
)

router.register(
    "solicitacao-de-alteracao-de-cronograma",
    cronograma_viewsets.SolicitacaoDeAlteracaoCronogramaViewSet,
    basename="solicitacao-de-alteracao-de-cronograma",
)
router.register(
    "rascunho-ficha-tecnica",
    ficha_tecnica_viewsets.FichaTecnicaRascunhoViewSet,
    basename="rascunho-ficha-tecnica",
)
router.register(
    "ficha-tecnica", ficha_tecnica_viewsets.FichaTecnicaModelViewSet, basename="ficha-tecnica"
)
router.register(
    "calendario-cronogramas",
    cronograma_viewsets.CalendarioCronogramaViewset,
    basename="calendario-cronogramas",
)


urlpatterns = [path("", include(router.urls))]
