import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker
from xworkflows import InvalidTransitionError

from sme_sigpae_api.cardapio.base.models import Cardapio
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.escola.models import Escola

pytestmark = pytest.mark.django_db


def test_inversao_dia_cardapio(inversao_dia_cardapio):
    assert isinstance(inversao_dia_cardapio.escola, Escola)
    assert isinstance(inversao_dia_cardapio.cardapio_de, Cardapio)
    assert isinstance(inversao_dia_cardapio.cardapio_para, Cardapio)
    assunto, template_html = inversao_dia_cardapio.template_mensagem
    assert assunto == "TESTE INVERSAO CARDAPIO"
    assert "RASCUNHO" in template_html


@freeze_time("2019-12-12")
def test_inversao_dia_cardapio_fluxo_codae_em_cima_da_hora_error(inversao_dia_cardapio):
    # a data do evento é dia 15 de dez a solicitação foi pedida em 12 dez (ou seja em cima da hora)
    # e no mesmo dia 12 a codae tenta autorizar, ela nao deve ser capaz de autorizar, deve questionar
    user = baker.make("Usuario")
    assert inversao_dia_cardapio.data == datetime.date(2019, 12, 15)
    assert inversao_dia_cardapio.prioridade == "PRIORITARIO"
    inversao_dia_cardapio.inicia_fluxo(user=user)
    inversao_dia_cardapio.dre_valida(user=user)
    assert inversao_dia_cardapio.foi_solicitado_fora_do_prazo is True
    assert inversao_dia_cardapio.status == "DRE_VALIDADO"
    with pytest.raises(
        InvalidTransitionError,
        match="CODAE não pode autorizar direto caso seja em cima da hora, deve questionar",
    ):
        inversao_dia_cardapio.codae_autoriza(user=user)


def test_inversao_dia_cardapio_fluxo(inversao_dia_cardapio):
    fake_user = baker.make("perfil.Usuario")
    inversao_dia_cardapio.inicia_fluxo(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    inversao_dia_cardapio.dre_valida(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )


@freeze_time("2012-01-14")
def test_inversao_dia_cardapio_fluxo_cancelamento(inversao_dia_cardapio):
    justificativa = "este e um cancelamento"
    fake_user = baker.make("perfil.Usuario")
    inversao_dia_cardapio.inicia_fluxo(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    inversao_dia_cardapio.cancelar_pedido(user=fake_user, justificativa=justificativa)
    assert (
        str(inversao_dia_cardapio.status)
        == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU
    )


def test_inversao_dia_cardapio_fluxo_cancelamento_erro(inversao_dia_cardapio2):
    justificativa = "este e um cancelamento"
    fake_user = baker.make("perfil.Usuario")
    with pytest.raises(
        InvalidTransitionError,
        match=r".*Só pode cancelar com no mínimo 2 dia\(s\) úteis de antecedência.*",
    ):
        inversao_dia_cardapio2.inicia_fluxo(user=fake_user)
        inversao_dia_cardapio2.cancelar_pedido(
            user=fake_user, justificativa=justificativa
        )


def test_inversao_dia_cardapio_fluxo_erro(inversao_dia_cardapio):
    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_pede_revisao' isn't available from state 'RASCUNHO'.",
    ):
        inversao_dia_cardapio.dre_pede_revisao()
