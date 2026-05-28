"""Managers customizados para o modelo InversaoCardapio.

Cada manager aplica um recorte temporal ou de status sobre o queryset padrao,
facilitando consultas de solicitacoes proximas, do mes e vencidas.
"""

import datetime

from django.db import models
from django.db.models import Q

from src.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


class InversaoCardapioDestaSemanaManager(models.Manager):
    """Manager que retorna inversões com datas previstas para os próximos 7 dias.

    Considera tanto ``data_de_inversao`` quanto ``data_para_inversao`` e exige
    que ambas as datas da solicitação ainda não tenham passado.
    """

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo da semana atual.

        Returns:
            QuerySet: Inversoes com ``data_de_inversao`` ou
            ``data_para_inversao`` entre hoje e hoje + 7 dias.
        """
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=7)
        return (
            super(InversaoCardapioDestaSemanaManager, self)
            .get_queryset()
            .filter(
                Q(data_de_inversao__range=(data_limite_inicial, data_limite_final))
                | Q(data_para_inversao__range=(data_limite_inicial, data_limite_final))
            )
            .filter(
                data_de_inversao__gte=data_limite_inicial,
                data_para_inversao__gte=data_limite_inicial,
            )
        )


class InversaoCardapioDesteMesManager(models.Manager):
    """Manager que retorna inversões com datas previstas para os próximos 30 dias.

    Considera tanto ``data_de_inversao`` quanto ``data_para_inversao`` e exige
    que ambas as datas da solicitação ainda não tenham passado.
    """

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo do mês atual.

        Returns:
            QuerySet: Inversões com ``data_de_inversao`` ou
            ``data_para_inversao`` entre hoje e hoje + 30 dias.
        """
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=30)
        return (
            super(InversaoCardapioDesteMesManager, self)
            .get_queryset()
            .filter(
                Q(data_de_inversao__range=(data_limite_inicial, data_limite_final))
                | Q(data_para_inversao__range=(data_limite_inicial, data_limite_final))
            )
            .filter(
                data_de_inversao__gte=data_limite_inicial,
                data_para_inversao__gte=data_limite_inicial,
            )
        )


class InversaoCardapioVencidaManager(models.Manager):
    """Manager que retorna inversões vencidas ainda em status aberto.

    Considera vencidas as solicitações cuja data de início ou fim já passou e
    que ainda estejam em status pendentes do fluxo da escola ou da DRE.
    """

    def get_queryset(self):
        """Retorna o queryset das inversões vencidas.

        Returns:
            QuerySet: Inversões com datas passadas e status ainda não
            finalizados.
        """
        hoje = datetime.date.today()
        return (
            super(InversaoCardapioVencidaManager, self)
            .get_queryset()
            .filter(Q(data_de_inversao__lt=hoje) | Q(data_para_inversao__lt=hoje))
            .filter(
                status__in=[
                    PedidoAPartirDaEscolaWorkflow.RASCUNHO,
                    PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
                    PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                ]
            )
        )
