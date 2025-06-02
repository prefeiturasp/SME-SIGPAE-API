import pytest
from rest_framework import serializers

from sme_sigpae_api.cardapio.base.api.validators import (
    escola_nao_pode_cadastrar_dois_combos_iguais,
    hora_inicio_nao_pode_ser_maior_que_hora_final,
)

pytestmark = pytest.mark.django_db


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


def test_escola_nao_pode_cadastrar_dois_combos_iguais(
    escola_dre_guaianases, tipo_alimentacao, periodo_manha
):
    existe_combo = escola_nao_pode_cadastrar_dois_combos_iguais(
        escola_dre_guaianases, tipo_alimentacao, periodo_manha
    )
    assert existe_combo is True


def test_escola_nao_pode_cadastrar_dois_combos_iguais_exception(
    escola_dre_guaianases,
    tipo_alimentacao,
    periodo_manha,
    escola_com_horario_vinculo_alimentacao,
):
    with pytest.raises(
        serializers.ValidationError,
        match="Já existe um horário registrado para esse tipo de alimentacao neste período e escola",
    ):
        escola_nao_pode_cadastrar_dois_combos_iguais(
            escola_dre_guaianases, tipo_alimentacao, periodo_manha
        )
