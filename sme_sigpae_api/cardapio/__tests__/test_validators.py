import pytest
from freezegun import freeze_time
from model_mommy import mommy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.cardapio.api.validators import (
    hora_inicio_nao_pode_ser_maior_que_hora_final,
    nao_pode_existir_solicitacao_igual_para_mesma_escola,
    nao_pode_ter_mais_que_60_dias_diferenca,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio

pytestmark = pytest.mark.django_db


def test_valida_60_dias_exception(datas_de_inversoes_intervalo_maior_60_dias):
    data_de, data_para, esperado = datas_de_inversoes_intervalo_maior_60_dias
    with pytest.raises(serializers.ValidationError, match=esperado):
        nao_pode_ter_mais_que_60_dias_diferenca(data_de, data_para)


def test_valida_intervalo_menor_que_60_dias(datas_de_inversoes_intervalo_entre_60_dias):
    data_de, data_para, esperado = datas_de_inversoes_intervalo_entre_60_dias
    assert nao_pode_ter_mais_que_60_dias_diferenca(data_de, data_para) is esperado


def test_nao_pode_existir_solicitacao_igual_para_mesma_escola_exceptio(
    datas_inversao_deste_mes, escola, tipo_alimentacao
):
    data_de, data_para, _ = datas_inversao_deste_mes
    cardapio_de = mommy.make("Cardapio", data=data_de)
    cardapio_para = mommy.make("Cardapio", data=data_para)
    inversao = mommy.make(
        InversaoCardapio,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        status=InversaoCardapio.workflow_class.DRE_A_VALIDAR,
        escola=escola,
    )
    inversao.tipos_alimentacao.add(tipo_alimentacao)
    inversao.save()
    with pytest.raises(
        ValidationError, match="Já existe uma solicitação de inversão com estes dados"
    ):
        nao_pode_existir_solicitacao_igual_para_mesma_escola(
            data_de=data_de,
            data_para=data_para,
            escola=escola,
            tipos_alimentacao=[tipo_alimentacao],
        )


def test_hora_inicio_nao_pode_ser_maior_que_hora_final(
    horarios_combos_tipo_alimentacao_validos,
):
    data_inicial, data_final, esperado = horarios_combos_tipo_alimentacao_validos
    assert (
        hora_inicio_nao_pode_ser_maior_que_hora_final(data_inicial, data_final)
        is esperado
    )


def test_hora_inicio_nao_pode_ser_maior_que_hora_final_exception(
    horarios_combos_tipo_alimentacao_invalidos,
):
    data_inicial, data_final, esperado = horarios_combos_tipo_alimentacao_invalidos
    with pytest.raises(serializers.ValidationError, match=esperado):
        hora_inicio_nao_pode_ser_maior_que_hora_final(data_inicial, data_final)
