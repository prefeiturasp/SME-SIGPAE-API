import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-4")
def test_manager_alteracao_vencida(datas_alteracao_vencida):
    data_inicial, status = datas_alteracao_vencida
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_vencida = baker.make(
        AlteracaoCardapio,
        escola=escola,
        data_inicial=data_inicial,
        data_final=data_final,
        status=status,
    )
    assert alteracao_cardapio_vencida in AlteracaoCardapio.vencidos.all()
    assert alteracao_cardapio_vencida not in AlteracaoCardapio.desta_semana.all()
    assert alteracao_cardapio_vencida not in AlteracaoCardapio.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_alteracao_desta_semana(datas_alteracao_semana):
    data_inicial, status = datas_alteracao_semana
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_semana = baker.make(
        AlteracaoCardapio,
        escola=escola,
        data_inicial=data_inicial,
        data_final=data_final,
        status=status,
    )
    assert alteracao_cardapio_semana not in AlteracaoCardapio.vencidos.all()
    assert alteracao_cardapio_semana in AlteracaoCardapio.desta_semana.all()
    assert alteracao_cardapio_semana in AlteracaoCardapio.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_alteracao_deste_mes(datas_alteracao_mes):
    data_inicial, status = datas_alteracao_mes
    lote = baker.make("Lote")
    escola = baker.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_mes = baker.make(
        AlteracaoCardapio,
        escola=escola,
        data_inicial=data_inicial,
        data_final=data_final,
        status=status,
    )
    assert alteracao_cardapio_mes not in AlteracaoCardapio.vencidos.all()
    assert alteracao_cardapio_mes in AlteracaoCardapio.deste_mes.all()
