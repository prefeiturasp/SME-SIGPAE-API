"""Validadores de negocio da API base de cardapio."""

import datetime

from rest_framework import serializers

from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    TipoAlimentacao,
)
from src.escola.models import Escola, PeriodoEscolar


def hora_inicio_nao_pode_ser_maior_que_hora_final(
    hora_inicial: datetime.time, hora_final: datetime.time
):
    """Valida se o horario inicial e anterior ao horario final.

    Args:
        hora_inicial (datetime.time): Horario inicial informado.
        hora_final (datetime.time): Horario final informado.

    Returns:
        bool: ``True`` quando a faixa de horario e valida.

    Raises:
        ValidationError: Quando ``hora_inicial`` e maior ou igual a
            ``hora_final``.
    """
    if hora_inicial >= hora_final:
        raise serializers.ValidationError(
            "Hora Inicio não pode ser maior do que hora final"
        )
    return True


def escola_nao_pode_cadastrar_dois_combos_iguais(
    escola: Escola, tipo_alimentacao: TipoAlimentacao, periodo_escolar: PeriodoEscolar
):
    """Impede a criacao de horarios duplicados para a mesma combinacao.

    Garante que cada escola tenha no maximo um horario cadastrado para um
    determinado tipo de alimentacao em um mesmo periodo escolar.

    Args:
        escola (Escola): Escola dona da configuracao.
        tipo_alimentacao (TipoAlimentacao): Tipo de alimentacao configurado.
        periodo_escolar (PeriodoEscolar): Periodo escolar da configuracao.

    Returns:
        bool: ``True`` quando nao existe duplicidade para a combinacao.

    Raises:
        ValidationError: Quando ja existe um horario com a mesma escola, tipo
            de alimentacao e periodo escolar.
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
