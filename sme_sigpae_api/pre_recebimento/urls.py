from django.urls import include, path
from rest_framework import routers

from .api import viewsets

router = routers.DefaultRouter()

router.register("cronogramas", viewsets.CronogramaModelViewSet)
router.register("laboratorios", viewsets.LaboratorioModelViewSet)
router.register("tipos-embalagens", viewsets.TipoEmbalagemQldModelViewSet)
router.register("unidades-medida-logistica", viewsets.UnidadeMedidaViewset)
router.register(
    "layouts-de-embalagem",
    viewsets.LayoutDeEmbalagemModelViewSet,
    basename="layouts-de-embalagem",
)
router.register(
    "documentos-de-recebimento",
    viewsets.DocumentoDeRecebimentoModelViewSet,
    basename="documentos-de-recebimento",
)

router.register(
    "solicitacao-de-alteracao-de-cronograma",
    viewsets.SolicitacaoDeAlteracaoCronogramaViewSet,
    basename="solicitacao-de-alteracao-de-cronograma",
)
router.register(
    "rascunho-ficha-tecnica",
    viewsets.FichaTecnicaRascunhoViewSet,
    basename="rascunho-ficha-tecnica",
)
router.register(
    "ficha-tecnica", viewsets.FichaTecnicaModelViewSet, basename="ficha-tecnica"
)
router.register(
    "calendario-cronogramas",
    viewsets.CalendarioCronogramaViewset,
    basename="calendario-cronogramas",
)


urlpatterns = [path("", include(router.urls))]
