from django.urls import include, path
from rest_framework import routers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api import (
    viewsets as alteracao_tipo_alimentacao_viewsets,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.api import (
    viewsets as alteracao_tipo_alimentacao_cei_viewsets,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api import (
    viewsets as alteracao_tipo_alimentacao_cemei_viewsets,
)
from sme_sigpae_api.cardapio.base.api import viewsets as base_viewsets
from sme_sigpae_api.cardapio.base.api.viewsets import (
    VinculosPorTipoUnidadeEscolarViewSet,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.api import (
    viewsets as inversao_dia_cardapio_viewsets,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.api import (
    viewsets as suspensao_alimentacao_viewsets,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.api import (
    viewsets as suspensao_alimentacao_cei_viewsets,
)

router = routers.DefaultRouter()
router.register("cardapios", base_viewsets.CardapioViewSet, "Cardápios")
router.register(
    "tipos-alimentacao", base_viewsets.TipoAlimentacaoViewSet, "Tipos de Alimentação"
)
router.register(
    "inversoes-dia-cardapio",
    inversao_dia_cardapio_viewsets.InversaoCardapioViewSet,
    "Inversão de dia de Cardápio",
)
router.register(
    "grupos-suspensoes-alimentacao",
    suspensao_alimentacao_viewsets.GrupoSuspensaoAlimentacaoSerializerViewSet,
    "Grupos de suspensão de alimentação.",
)
router.register(
    "alteracoes-cardapio",
    alteracao_tipo_alimentacao_viewsets.AlteracoesCardapioViewSet,
    "Alterações de Cardápio",
)
router.register(
    "alteracoes-cardapio-cei",
    alteracao_tipo_alimentacao_cei_viewsets.AlteracoesCardapioCEIViewSet,
    "Alterações de Cardápio CEI",
)
router.register(
    "alteracoes-cardapio-cemei",
    alteracao_tipo_alimentacao_cemei_viewsets.AlteracoesCardapioCEMEIViewSet,
    "Alterações de Cardápio CEMEI",
)
router.register(
    "motivos-alteracao-cardapio",
    alteracao_tipo_alimentacao_viewsets.MotivosAlteracaoCardapioViewSet,
    "Motivos de alteração de cardápio",
)
router.register(
    "motivos-suspensao-cardapio",
    suspensao_alimentacao_viewsets.MotivosSuspensaoCardapioViewSet,
    "Motivos de suspensão de cardápio",
)
router.register(
    "vinculos-tipo-alimentacao-u-e-periodo-escolar",
    base_viewsets.VinculoTipoAlimentacaoViewSet,
    "Vínculos de tipo de alimentação no periodo escolar e tipo de u.e",
)
router.register(
    "combos-vinculos-tipo-alimentacao-u-e-periodo-escolar",
    base_viewsets.CombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet,
    "Combos dos vínculos de tipo de alimentação no periodo escolar e tipo de u.e",
)
router.register(
    "substituicoes-combos-vinculos-tipo-alimentacao-u-e-periodo-escolar",
    base_viewsets.SubstituicaoDoCombosDoVinculoTipoAlimentacaoPeriodoTipoUEViewSet,
    "Substituições dos combos dos vínculos de tipo de alimentação no periodo escolar e tipo de u.e",
)
router.register(
    "horario-do-combo-tipo-de-alimentacao-por-unidade-escolar",
    base_viewsets.HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarViewSet,
    "horario-do-combo-tipo-de-alimentacao-por-unidade-escolar",
)
router.register(
    "suspensao-alimentacao-de-cei",
    suspensao_alimentacao_cei_viewsets.SuspensaoAlimentacaoDaCEIViewSet,
    "suspensao-alimentacao-de-cei",
)
router.register(
    "motivos-dre-nao-valida",
    base_viewsets.MotivosDRENaoValidaViewSet,
    "Motivos de não validação da DRE",
)
router.register(
    "tipos-unidade-escolar-agrupados",
    VinculosPorTipoUnidadeEscolarViewSet,
    basename="tipos-unidade-escolar-agrupados",
)
urlpatterns = [
    path("", include(router.urls)),
]
