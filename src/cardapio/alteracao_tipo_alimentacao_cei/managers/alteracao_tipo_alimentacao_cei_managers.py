"""Managers customizados para o modelo AlteracaoCardapioCEI.

Cada manager aplica um filtro diferente sobre o queryset padrão, segmentando
as alterações de cardápio CEI por janela temporal.
"""

import datetime

from django.db import models


class AlteracoesCardapioCEIDestaSemanaManager(models.Manager):
    """Manager que retorna alterações de cardápio CEI com data nos próximos 7 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo da semana atual.

        Returns:
            QuerySet: Alterações cuja ``data`` está entre hoje e hoje + 7 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(AlteracoesCardapioCEIDestaSemanaManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioCEIDesteMesManager(models.Manager):
    """Manager que retorna alterações de cardápio CEI com data nos próximos 31 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo do mês atual.

        Returns:
            QuerySet: Alterações cuja ``data`` está entre hoje e hoje + 31 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(AlteracoesCardapioCEIDesteMesManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )
