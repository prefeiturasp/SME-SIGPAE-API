import pytest
from freezegun import freeze_time
from model_bakery import baker

from ...dados_comuns.fluxo_status import (
    PedidoAPartirDaDiretoriaRegionalWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ...kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheUnificada,
)

pytestmark = pytest.mark.django_db


#
# Kit lanche avulso
#


def _monta_kit_lanche_avulso(
    kits_avulsos_datas, escola, status=PedidoAPartirDaEscolaWorkflow.RASCUNHO
):
    solicitacao_kit_lanche_base = baker.make(
        "SolicitacaoKitLanche", data=kits_avulsos_datas
    )
    solicitacao_kit_lanche_avulsa = baker.make(
        "SolicitacaoKitLancheAvulsa",
        status=status,
        escola=escola,
        solicitacao_kit_lanche=solicitacao_kit_lanche_base,
    )
    return solicitacao_kit_lanche_avulsa


@freeze_time("2019-10-03")
def test_manager_kit_lanche_avulso_vencido(
    kits_avulsos_datas_passado_parametros, escola
):
    kits_avulsos_datas, status = kits_avulsos_datas_passado_parametros
    solicitacao_kit_lanche_avulsa = _monta_kit_lanche_avulso(
        kits_avulsos_datas, escola, status
    )
    assert solicitacao_kit_lanche_avulsa in SolicitacaoKitLancheAvulsa.vencidos.all()


@freeze_time("2019-10-03")
def test_manager_kit_lanche_avulso_desta_semana(kits_avulsos_datas_semana, escola):
    solicitacao_kit_lanche_avulsa = _monta_kit_lanche_avulso(
        kits_avulsos_datas_semana, escola
    )
    assert (
        solicitacao_kit_lanche_avulsa in SolicitacaoKitLancheAvulsa.desta_semana.all()
    )


@freeze_time("2019-10-03")
def test_manager_kit_lanche_avulso_deste_mes(kits_avulsos_datas_mes, escola):
    solicitacao_kit_lanche_avulsa = _monta_kit_lanche_avulso(
        kits_avulsos_datas_mes, escola
    )
    assert solicitacao_kit_lanche_avulsa in SolicitacaoKitLancheAvulsa.deste_mes.all()


#
# Kit lanche unificado
#


def _monta_kit_lanche_unificado(
    kits_avulsos_datas, status=PedidoAPartirDaDiretoriaRegionalWorkflow.RASCUNHO
):
    solicitacao_kit_lanche_base = baker.make(
        "SolicitacaoKitLanche", data=kits_avulsos_datas
    )
    solicitacao_kit_lanche_unificada = baker.make(
        "SolicitacaoKitLancheUnificada",
        status=status,
        solicitacao_kit_lanche=solicitacao_kit_lanche_base,
    )
    return solicitacao_kit_lanche_unificada


@freeze_time("2019-10-03")
def test_manager_kit_lanche_unificado_vencido(kits_unificados_datas_passado_parametros):
    kits_avulsos_datas, status = kits_unificados_datas_passado_parametros
    solicitacao_kit_lanche_unificada = _monta_kit_lanche_unificado(
        kits_avulsos_datas, status
    )
    assert (
        solicitacao_kit_lanche_unificada in SolicitacaoKitLancheUnificada.vencidos.all()
    )


@freeze_time("2019-10-03")
def test_manager_kit_lanche_unificado_deste_mes(kits_avulsos_datas_mes):
    solicitacao_kit_lanche_unificada = _monta_kit_lanche_unificado(
        kits_avulsos_datas_mes
    )
    assert (
        solicitacao_kit_lanche_unificada
        in SolicitacaoKitLancheUnificada.deste_mes.all()
    )


@freeze_time("2019-10-03")
def test_manager_kit_lanche_unificado_deste_semana(kits_avulsos_datas_semana):
    solicitacao_kit_lanche_unificada = _monta_kit_lanche_unificado(
        kits_avulsos_datas_semana
    )
    assert (
        solicitacao_kit_lanche_unificada
        in SolicitacaoKitLancheUnificada.desta_semana.all()
    )
