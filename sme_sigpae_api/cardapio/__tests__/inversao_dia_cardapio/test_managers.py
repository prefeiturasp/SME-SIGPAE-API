import datetime

import pytest
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-4")
def test_manager_inversao_vencida(datas_inversao_vencida, escola):
    dia_de, dia_para, status = datas_inversao_vencida
    cardapio_de = mommy.make("cardapio.Cardapio", data=dia_de)
    cardapio_para = mommy.make("cardapio.Cardapio", data=dia_para)
    inversao_cardapio_vencida = mommy.make(
        InversaoCardapio,
        escola=escola,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        status=status,
    )
    assert inversao_cardapio_vencida in InversaoCardapio.vencidos.all()
    assert inversao_cardapio_vencida not in InversaoCardapio.desta_semana.all()
    assert inversao_cardapio_vencida not in InversaoCardapio.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inversao_desta_semana(datas_inversao_desta_semana):
    dia_de, dia_para, status = datas_inversao_desta_semana
    lote = mommy.make("Lote")
    escola = mommy.make("Escola", lote=lote)
    cardapio_de = mommy.make("cardapio.Cardapio", data=datetime.date(*dia_de))
    cardapio_para = mommy.make("cardapio.Cardapio", data=datetime.date(*dia_para))
    inversao_cardapio_desta_semana = mommy.make(
        InversaoCardapio,
        escola=escola,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        status=status,
    )
    assert inversao_cardapio_desta_semana in InversaoCardapio.desta_semana.all()
    assert inversao_cardapio_desta_semana in InversaoCardapio.deste_mes.all()
    assert inversao_cardapio_desta_semana not in InversaoCardapio.vencidos.all()


@freeze_time("2019-10-4")
def test_manager_inversao_deste_mes(datas_inversao_deste_mes):
    dia_de, dia_para, status = datas_inversao_deste_mes
    lote = mommy.make("Lote")
    escola = mommy.make("Escola", lote=lote)
    cardapio_de = mommy.make("cardapio.Cardapio", data=dia_de)
    cardapio_para = mommy.make("cardapio.Cardapio", data=dia_para)
    inversao_cardapio_desta_semana = mommy.make(
        InversaoCardapio,
        escola=escola,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        status=status,
    )
    assert inversao_cardapio_desta_semana in InversaoCardapio.deste_mes.all()
    assert inversao_cardapio_desta_semana not in InversaoCardapio.vencidos.all()
