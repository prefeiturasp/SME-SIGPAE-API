"""Managers customizados para o modelo AlteracaoCardapioCEMEI.

Cada manager aplica um filtro diferente sobre o queryset padrão, segmentando
as alterações de cardápio CEMEI por janela temporal. O filtro considera tanto
o campo ``alterar_dia`` (solicitação de dia único) quanto ``data_inicial``
(solicitação por intervalo), pois o CEMEI suporta ambos os modos.
"""

import datetime

from django.db import models
from django.db.models import Q


class AlteracoesCardapioCEMEIDestaSemanaManager(models.Manager):
    """Manager que retorna alterações de cardápio CEMEI com data nos próximos 7 dias.

    Considera tanto solicitações de dia único (``alterar_dia``) quanto
    solicitações por intervalo (``data_inicial``).
    """

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo da semana atual.

        Returns:
            QuerySet: Alterações cujo ``alterar_dia`` ou ``data_inicial`` está
            entre hoje e hoje + 7 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(AlteracoesCardapioCEMEIDestaSemanaManager, self)
            .get_queryset()
            .filter(
                Q(alterar_dia__range=(data_limite_inicial, data_limite_final))
                | Q(data_inicial__range=(data_limite_inicial, data_limite_final))
            )
        )


class AlteracoesCardapioCEMEIDesteMesManager(models.Manager):
    """Manager que retorna alterações de cardápio CEMEI com data nos próximos 31 dias.

    Considera tanto solicitações de dia único (``alterar_dia``) quanto
    solicitações por intervalo (``data_inicial``).
    """

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo do mês atual.

        Returns:
            QuerySet: Alterações cujo ``alterar_dia`` ou ``data_inicial`` está
            entre hoje e hoje + 31 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(AlteracoesCardapioCEMEIDesteMesManager, self)
            .get_queryset()
            .filter(
                Q(alterar_dia__range=(data_limite_inicial, data_limite_final))
                | Q(data_inicial__range=(data_limite_inicial, data_limite_final))
            )
        )
