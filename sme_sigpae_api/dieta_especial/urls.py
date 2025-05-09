from django.urls import include, path, re_path
from rest_framework import routers

from .api import viewsets
from .constants import (
    ENDPOINT_ALERGIAS_INTOLERANCIAS,
    ENDPOINT_ALIMENTOS,
    ENDPOINT_CLASSIFICACOES_DIETA,
    ENDPOINT_MOTIVOS_NEGACAO,
    ENDPOINT_TIPO_CONTAGEM,
)

router = routers.DefaultRouter()

router.register(
    "solicitacoes-dieta-especial",
    viewsets.SolicitacaoDietaEspecialViewSet,
    basename="Solicitações de dieta especial",
)
router.register(
    ENDPOINT_ALERGIAS_INTOLERANCIAS,
    viewsets.AlergiaIntoleranciaViewSet,
    basename="Alergias/Intolerâncias alimentares",
)
router.register(
    ENDPOINT_ALIMENTOS,
    viewsets.AlimentoViewSet,
    basename="Alimentos que podem ser substituídos em uma dieta especial",
)
router.register(
    ENDPOINT_CLASSIFICACOES_DIETA,
    viewsets.ClassificacaoDietaViewSet,
    basename="Classificação de dieta especial",
)
router.register(
    ENDPOINT_MOTIVOS_NEGACAO,
    viewsets.MotivoNegacaoViewSet,
    basename="Motivos de negação de dieta especial",
)
router.register(
    ENDPOINT_TIPO_CONTAGEM,
    viewsets.TipoContagemViewSet,
    basename="Tipos de contagem de refeições",
)
router.register(
    "motivo-alteracao-ue",
    viewsets.MotivoAlteracaoUEViewSet,
    basename="Motivos alteracao UE de dieta especial",
)
router.register(
    "protocolo-padrao-dieta-especial",
    viewsets.ProtocoloPadraoDietaEspecialViewSet,
    basename="Protocolo padrao de dieta especial",
)
router.register(
    "log-quantidade-dietas-autorizadas",
    viewsets.LogQuantidadeDietasAutorizadasViewSet,
    basename="Log quantidade dietas autorizadas",
)
router.register(
    "log-quantidade-dietas-autorizadas-cei",
    viewsets.LogQuantidadeDietasAutorizadasCEIViewSet,
    basename="Log quantidade dietas autorizadas CEI",
)


urlpatterns = [
    path("", include(router.urls)),
    re_path(
        r"^solicitacoes-dieta-especial-ativas-inativas/$",
        viewsets.SolicitacoesAtivasInativasPorAlunoView.as_view(),
    ),
]
