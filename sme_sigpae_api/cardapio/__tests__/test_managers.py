import datetime

import pytest
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)

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


@freeze_time("2019-10-4")
def test_manager_altercao_vencida(datas_alteracao_vencida):
    data_inicial, status = datas_alteracao_vencida
    lote = mommy.make("Lote")
    escola = mommy.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_vencida = mommy.make(
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
    lote = mommy.make("Lote")
    escola = mommy.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_semana = mommy.make(
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
    lote = mommy.make("Lote")
    escola = mommy.make("Escola", lote=lote)
    data_inicial = datetime.date(*data_inicial)
    data_final = data_inicial + datetime.timedelta(days=10)
    alteracao_cardapio_mes = mommy.make(
        AlteracaoCardapio,
        escola=escola,
        data_inicial=data_inicial,
        data_final=data_final,
        status=status,
    )
    assert alteracao_cardapio_mes not in AlteracaoCardapio.vencidos.all()
    assert alteracao_cardapio_mes in AlteracaoCardapio.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inclusoes_normais_deste_mes(
    suspensao_alimentacao_parametros_mes, escola
):
    data_evento, _ = suspensao_alimentacao_parametros_mes
    grupo_suspensoes = mommy.make(GrupoSuspensaoAlimentacao, escola=escola)
    mommy.make(SuspensaoAlimentacao, data=data_evento, grupo_suspensao=grupo_suspensoes)
    assert grupo_suspensoes in GrupoSuspensaoAlimentacao.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inclusoes_normais_desta_semana(
    suspensao_alimentacao_parametros_semana, escola
):
    data_evento, _ = suspensao_alimentacao_parametros_semana
    grupo_suspensoes = mommy.make(GrupoSuspensaoAlimentacao, escola=escola)
    mommy.make(SuspensaoAlimentacao, data=data_evento, grupo_suspensao=grupo_suspensoes)
    assert grupo_suspensoes in GrupoSuspensaoAlimentacao.desta_semana.all()
