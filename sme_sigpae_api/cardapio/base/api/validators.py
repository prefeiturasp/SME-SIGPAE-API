import datetime

from rest_framework import serializers

from sme_sigpae_api.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    TipoAlimentacao,
)
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar


def hora_inicio_nao_pode_ser_maior_que_hora_final(
    hora_inicial: datetime.time, hora_final: datetime.time
):
    if hora_inicial >= hora_final:
        raise serializers.ValidationError(
            "Hora Inicio não pode ser maior do que hora final"
        )
    return True


def escola_nao_pode_cadastrar_dois_combos_iguais(
    escola: Escola, tipo_alimentacao: TipoAlimentacao, periodo_escolar: PeriodoEscolar
):
    """
    Se o horário de tipo de alimentação já estiver cadastrado para a Escola e Período escolar, deve retornar erro.

    Pois para cada tipo de alimentação só é possivel registrar um intervalo de horario, caso o tipo de alimentação já
    estiver cadastrado, só será possivel atualizar o objeto HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.
    """
    horario_alimento_por_escola_e_periodo = (
        HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.filter(
            escola=escola,
            tipo_alimentacao=tipo_alimentacao,
            periodo_escolar=periodo_escolar,
        ).exists()
    )
    if horario_alimento_por_escola_e_periodo:
        raise serializers.ValidationError(
            "Já existe um horário registrado para esse tipo de alimentacao neste período e escola"
        )
    return True
