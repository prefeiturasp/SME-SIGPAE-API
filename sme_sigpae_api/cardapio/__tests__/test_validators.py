import pytest
from rest_framework import serializers

from sme_sigpae_api.cardapio.base.api.validators import (
    hora_inicio_nao_pode_ser_maior_que_hora_final,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.validators import (
    nao_pode_ter_mais_que_60_dias_diferenca,
)

pytestmark = pytest.mark.django_db


def test_valida_60_dias_exception(datas_de_inversoes_intervalo_maior_60_dias):
    data_de, data_para, esperado = datas_de_inversoes_intervalo_maior_60_dias
    with pytest.raises(serializers.ValidationError, match=esperado):
        nao_pode_ter_mais_que_60_dias_diferenca(data_de, data_para)


def test_valida_intervalo_menor_que_60_dias(datas_de_inversoes_intervalo_entre_60_dias):
    data_de, data_para, esperado = datas_de_inversoes_intervalo_entre_60_dias
    assert nao_pode_ter_mais_que_60_dias_diferenca(data_de, data_para) is esperado


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
