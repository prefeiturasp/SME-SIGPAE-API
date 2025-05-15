import datetime

from django.db.models import Q
from rest_framework import serializers

from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.escola.models import Escola


def nao_pode_existir_solicitacao_igual_para_mesma_escola(
    data_de: datetime.date,
    data_para: datetime.date,
    escola: Escola,
    tipos_alimentacao: list,
):
    inversao_cardapio = (
        InversaoCardapio.objects.filter(
            Q(
                cardapio_de__data=data_de,
                cardapio_para__data=data_para,
                escola=escola,
                tipos_alimentacao__in=tipos_alimentacao,
            )
            | Q(
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
    diferenca = abs((data_para - data_de).days)
    if diferenca > 60:
        raise serializers.ValidationError(
            "Diferença entre as datas não pode ultrapassar de 60 dias"
        )
    return True
