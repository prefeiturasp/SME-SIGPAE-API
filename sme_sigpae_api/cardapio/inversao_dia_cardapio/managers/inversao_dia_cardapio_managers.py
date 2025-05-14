import datetime

from django.db import models
from django.db.models import Q

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


class InversaoCardapioDestaSemanaManager(models.Manager):
    def get_queryset(self):
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=7)
        return (
            super(InversaoCardapioDestaSemanaManager, self)
            .get_queryset()
            .filter(
                Q(cardapio_de__data__range=(data_limite_inicial, data_limite_final))
                | Q(  # noqa W504
                    cardapio_para__data__range=(data_limite_inicial, data_limite_final)
                )
            )
            .filter(
                cardapio_de__data__gte=data_limite_inicial,
                cardapio_para__data__gte=data_limite_inicial,
            )
        )


class InversaoCardapioDesteMesManager(models.Manager):
    def get_queryset(self):
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=30)
        return (
            super(InversaoCardapioDesteMesManager, self)
            .get_queryset()
            .filter(
                Q(cardapio_de__data__range=(data_limite_inicial, data_limite_final))
                | Q(  # noqa W504
                    cardapio_para__data__range=(data_limite_inicial, data_limite_final)
                )
            )
            .filter(
                cardapio_de__data__gte=data_limite_inicial,
                cardapio_para__data__gte=data_limite_inicial,
            )
        )


class InversaoCardapioVencidaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        return (
            super(InversaoCardapioVencidaManager, self)
            .get_queryset()
            .filter(Q(cardapio_de__data__lt=hoje) | Q(cardapio_para__data__lt=hoje))
            .filter(
                status__in=[
                    PedidoAPartirDaEscolaWorkflow.RASCUNHO,
                    PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
                    PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                ]
            )
        )
