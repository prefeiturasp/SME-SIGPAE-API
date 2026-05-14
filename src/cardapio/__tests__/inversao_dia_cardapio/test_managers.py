import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-4")
def test_manager_inversao_vencida(datas_inversao_vencida, escola):
    dia_de, dia_para, status = datas_inversao_vencida
    inversao_cardapio_vencida = baker.make(
        InversaoCardapio,
        escola=escola,
        data_de_inversao=dia_de,
        data_para_inversao=dia_para,
        status=status,
    )
    assert inversao_cardapio_vencida in InversaoCardapio.vencidos.all()
    assert inversao_cardapio_vencida not in InversaoCardapio.desta_semana.all()
    assert inversao_cardapio_vencida not in InversaoCardapio.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inversao_desta_semana(datas_inversao_desta_semana):
    dia_de, dia_para, status = datas_inversao_desta_semana
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    inversao_cardapio_desta_semana = baker.make(
        InversaoCardapio,
        escola=escola,
        data_de_inversao=datetime.date(*dia_de),
        data_para_inversao=datetime.date(*dia_para),
        status=status,
    )
    assert inversao_cardapio_desta_semana in InversaoCardapio.desta_semana.all()
    assert inversao_cardapio_desta_semana in InversaoCardapio.deste_mes.all()
    assert inversao_cardapio_desta_semana not in InversaoCardapio.vencidos.all()


@freeze_time("2019-10-4")
def test_manager_inversao_deste_mes(datas_inversao_deste_mes):
    dia_de, dia_para, status = datas_inversao_deste_mes
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    inversao_cardapio_desta_semana = baker.make(
        InversaoCardapio,
        escola=escola,
        data_de_inversao=dia_de,
        data_para_inversao=dia_para,
        status=status,
    )
    assert inversao_cardapio_desta_semana in InversaoCardapio.deste_mes.all()
    assert inversao_cardapio_desta_semana not in InversaoCardapio.vencidos.all()
