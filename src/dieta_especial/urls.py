from django.urls import include, path, re_path
from rest_framework import routers

from src.dieta_especial.logs_models.api import viewsets as logs_models_viewsets
from src.dieta_especial.protocolo_padrao.api import (
    viewsets as protocolo_padrao_viewsets,
)
from src.dieta_especial.solicitacao_dieta_especial.api import (
    viewsets as solicitacao_dieta_especial_viewsets,
)

from .constants import (
    ENDPOINT_ALERGIAS_INTOLERANCIAS,
    ENDPOINT_ALIMENTOS,
    ENDPOINT_CLASSIFICACOES_DIETA,
    ENDPOINT_MOTIVOS_NEGACAO,
)

router = routers.DefaultRouter()

router.register(
    "solicitacoes-dieta-especial",
    solicitacao_dieta_especial_viewsets.SolicitacaoDietaEspecialViewSet,
    basename="Solicitações de dieta especial",
)
router.register(
    ENDPOINT_ALERGIAS_INTOLERANCIAS,
    solicitacao_dieta_especial_viewsets.AlergiaIntoleranciaViewSet,
    basename="Alergias/Intolerâncias alimentares",
)
router.register(
    ENDPOINT_ALIMENTOS,
    solicitacao_dieta_especial_viewsets.AlimentoViewSet,
    basename="Alimentos que podem ser substituídos em uma dieta especial",
)
router.register(
    ENDPOINT_CLASSIFICACOES_DIETA,
    solicitacao_dieta_especial_viewsets.ClassificacaoDietaViewSet,
    basename="Classificação de dieta especial",
)
router.register(
    ENDPOINT_MOTIVOS_NEGACAO,
    solicitacao_dieta_especial_viewsets.MotivoNegacaoViewSet,
    basename="Motivos de negação de dieta especial",
)
router.register(
    "motivo-alteracao-ue",
    solicitacao_dieta_especial_viewsets.MotivoAlteracaoUEViewSet,
    basename="Motivos alteracao UE de dieta especial",
)
router.register(
    "protocolo-padrao-dieta-especial",
    protocolo_padrao_viewsets.ProtocoloPadraoDietaEspecialViewSet,
    basename="Protocolo padrao de dieta especial",
)
router.register(
    "log-quantidade-dietas-autorizadas",
    logs_models_viewsets.LogQuantidadeDietasAutorizadasViewSet,
    basename="Log quantidade dietas autorizadas",
)
router.register(
    "log-quantidade-dietas-autorizadas-cei",
    logs_models_viewsets.LogQuantidadeDietasAutorizadasCEIViewSet,
    basename="Log quantidade dietas autorizadas CEI",
)
router.register(
    "log-quantidade-dietas-autorizadas-recreio-nas-ferias",
    logs_models_viewsets.LogQuantidadeDietasAutorizadasRecreioNasFeriasViewSet,
    basename="Log quantidade dietas autorizadas RecreioNasFerias",
)
router.register(
    "log-quantidade-dietas-autorizadas-recreio-nas-ferias-cei",
    logs_models_viewsets.LogQuantidadeDietasAutorizadasRecreioNasFeriasCEIViewSet,
    basename="Log quantidade dietas autorizadas RecreioNasFerias CEI",
)


urlpatterns = [
    path("", include(router.urls)),
    re_path(
        r"^solicitacoes-dieta-especial-ativas-inativas/$",
        solicitacao_dieta_especial_viewsets.SolicitacoesAtivasInativasPorAlunoView.as_view(),
    ),
]
