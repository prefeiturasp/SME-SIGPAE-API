import datetime

from django.db.models import Q
from rest_framework import serializers

from ...cardapio.models import (
    Cardapio,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
)
from ...escola.models import Escola, PeriodoEscolar
from ..models import InversaoCardapio


def cardapio_antigo(cardapio: Cardapio):
    if cardapio.data <= datetime.date.today():
        raise serializers.ValidationError('Não pode ser cardápio antigo')
    return True


def data_troca_nao_pode_ser_superior_a_data_inversao(data_de: datetime.date, data_para: datetime.date):
    if data_de >= data_para:
        raise serializers.ValidationError(
            'Data da referência deve ser anterior a data aplicar em')
    return True


def nao_pode_existir_solicitacao_igual_para_mesma_escola(data_de: datetime.date, data_para: datetime.date,
                                                         escola: Escola, tipos_alimentacao: list):
    inversao_cardapio = InversaoCardapio.objects.filter(
        Q(cardapio_de__data=data_de, cardapio_para__data=data_para,
          escola=escola, tipos_alimentacao__in=tipos_alimentacao) |
        Q(data_de_inversao=data_de, data_para_inversao=data_para,
          escola=escola, tipos_alimentacao__in=tipos_alimentacao) |
        Q(data_de_inversao_2=data_de, data_para_inversao_2=data_para,
          escola=escola, tipos_alimentacao__in=tipos_alimentacao)
    ).filter(~Q(status__in=[
        InversaoCardapio.workflow_class.RASCUNHO,
        InversaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        InversaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO,
        InversaoCardapio.workflow_class.ESCOLA_CANCELOU,
        InversaoCardapio.workflow_class.CANCELADO_AUTOMATICAMENTE,
    ])).exists()
    if inversao_cardapio:
        raise serializers.ValidationError(
            'Já existe uma solicitação de inversão com estes dados')
    return True


def nao_pode_ter_mais_que_60_dias_diferenca(data_de: datetime.date, data_para: datetime.date):
    diferenca = abs((data_para - data_de).days)
    if diferenca > 60:
        raise serializers.ValidationError(
            'Diferença entre as datas não pode ultrapassar de 60 dias'
        )
    return True


def precisa_pertencer_a_um_tipo_de_alimentacao(tipos_alimentacao_de,
                                               tipo_alimentacao_para,
                                               tipo_unidade_escolar,
                                               periodo_escolar):
    tipos_alimentacao = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(periodo_escolar=periodo_escolar, tipo_unidade_escolar=tipo_unidade_escolar).tipos_alimentacao.all()  # noqa E501
    for tipo_alimentacao in tipos_alimentacao_de:
        if tipo_alimentacao not in tipos_alimentacao:
            raise serializers.ValidationError(
                f'Tipo de alimentação {tipo_alimentacao.nome} não pertence ao período e tipo de unidade'
            )
    if tipo_alimentacao_para in tipos_alimentacao_de:
        raise serializers.ValidationError(
            f'Substituto {tipo_alimentacao_para.nome} está incluso na lista de alimentos substituídos'
        )
    return True


def hora_inicio_nao_pode_ser_maior_que_hora_final(hora_inicial: datetime.time, hora_final: datetime.time):
    if hora_inicial >= hora_final:
        raise serializers.ValidationError(
            'Hora Inicio não pode ser maior do que hora final'
        )
    return True


def escola_nao_pode_cadastrar_dois_combos_iguais(escola: Escola, tipo_alimentacao:
                                                 TipoAlimentacao, periodo_escolar: PeriodoEscolar):
    """
    Se o horário de tipo de alimentação já estiver cadastrado para a Escola e Período escolar, deve retornar erro.

    Pois para cada tipo de alimentação só é possivel registrar um intervalo de horario, caso o tipo de alimentação já
    estiver cadastrado, só será possivel atualizar o objeto HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.
    """
    horario_alimento_por_escola_e_periodo = HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar.objects.filter(
        escola=escola,
        tipo_alimentacao=tipo_alimentacao,
        periodo_escolar=periodo_escolar
    ).exists()
    if horario_alimento_por_escola_e_periodo:
        raise serializers.ValidationError(
            'Já existe um horário registrado para esse tipo de alimentacao neste período e escola')
    return True
