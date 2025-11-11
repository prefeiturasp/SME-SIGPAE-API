from django.urls import include, path
from rest_framework import routers

from .api import viewsets
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.api import (
    viewsets as recreio_nas_ferias_viewsets,
)

router = routers.DefaultRouter()

router.register("categorias-medicao", viewsets.CategoriaMedicaoViewSet)
router.register("dias-sobremesa-doce", viewsets.DiaSobremesaDoceViewSet)
router.register("medicao", viewsets.MedicaoViewSet)
router.register(
    "solicitacao-medicao-inicial", viewsets.SolicitacaoMedicaoInicialViewSet
)
router.register("tipo-contagem-alimentacao", viewsets.TipoContagemAlimentacaoViewSet)
router.register("valores-medicao", viewsets.ValorMedicaoViewSet)
router.register("ocorrencia", viewsets.OcorrenciaViewSet)
router.register(
    "alimentacoes-lancamentos-especiais", viewsets.AlimentacaoLancamentoEspecialViewSet
)
router.register(
    "permissao-lancamentos-especiais", viewsets.PermissaoLancamentoEspecialViewSet
)
router.register("dias-para-corrigir", viewsets.DiasParaCorrigirViewSet)
router.register("empenhos", viewsets.EmpenhoViewSet)
router.register("clausulas-de-descontos", viewsets.ClausulaDeDescontoViewSet)

router.register("relatorios", viewsets.RelatoriosViewSet, basename="relatorios")
router.register(
    "parametrizacao-financeira",
    viewsets.ParametrizacaoFinanceiraViewSet,
    basename="parametrizacao-financeira",
)
router.register(
    "relatorio-financeiro",
    viewsets.RelatorioFinanceiroViewSet,
    basename="relatorio-financeiro",
)
router.register("recreio-nas-ferias", recreio_nas_ferias_viewsets.RecreioNasFeriasViewSet, basename="recreio-nas-ferias")

urlpatterns = [
    path("medicao-inicial/", include(router.urls)),
]
