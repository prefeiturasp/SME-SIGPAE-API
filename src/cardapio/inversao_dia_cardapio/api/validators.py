"""Validadores de negócio da API de Inversão de dia de Cardápio."""

import datetime

from django.db.models import Q
from rest_framework import serializers

from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from src.escola.models import Escola


def nao_pode_existir_solicitacao_igual_para_mesma_escola(
    data_de: datetime.date,
    data_para: datetime.date,
    escola: Escola,
    tipos_alimentacao: list,
):
    """Impede a criação de solicitações duplicadas para a mesma escola.

    Considera tanto o primeiro quanto o segundo par de datas da solicitação e
    ignora pedidos em status finais que não bloqueiam nova criação.

    Args:
        data_de (datetime.date): Data inicial da inversão.
        data_para (datetime.date): Data final da inversão.
        escola (Escola): Escola associada ao pedido.
        tipos_alimentacao (list): Tipos de alimentação vinculados ao pedido.

    Returns:
        bool: ``True`` quando não existe solicitação equivalente em aberto.

    Raises:
        ValidationError: Quando já existe uma solicitação com os mesmos dados.
    """
    inversao_cardapio = (
        InversaoCardapio.objects.filter(
            Q(
                data_de_inversao=data_de,
                data_para_inversao=data_para,
                escola=escola,
                tipos_alimentacao__in=tipos_alimentacao,
            )
            | Q(
                data_de_inversao_2=data_de,
                data_para_inversao_2=data_para,
                escola=escola,
                tipos_alimentacao__in=tipos_alimentacao,
            )
        )
        .filter(
            ~Q(
                status__in=[
                    InversaoCardapio.workflow_class.RASCUNHO,
                    InversaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
                    InversaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO,
                    InversaoCardapio.workflow_class.ESCOLA_CANCELOU,
                    InversaoCardapio.workflow_class.CANCELADO_AUTOMATICAMENTE,
                ]
            )
        )
        .exists()
    )
    if inversao_cardapio:
        raise serializers.ValidationError(
            "Já existe uma solicitação de inversão com estes dados"
        )
    return True


def nao_pode_ter_mais_que_60_dias_diferenca(
    data_de: datetime.date, data_para: datetime.date
):
    """Valida o limite máximo de diferença entre as datas da inversão, que é de 60 dias.

    Args:
        data_de (datetime.date): Data inicial da inversão.
        data_para (datetime.date): Data final da inversão.

    Returns:
        bool: ``True`` quando a diferença entre as datas é de até 60 dias.

    Raises:
        ValidationError: Quando a diferença absoluta entre as datas ultrapassa
            60 dias.
    """
    diferenca = abs((data_para - data_de).days)
    if diferenca > 60:
        raise serializers.ValidationError(
            "Diferença entre as datas não pode ultrapassar 60 dias"
        )
    return True
