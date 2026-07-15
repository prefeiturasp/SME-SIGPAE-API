"""Managers customizados para o modelo GrupoSuspensaoAlimentacao.

Cada manager aplica um filtro diferente sobre o queryset padrão, segmentando
as suspensões de alimentação por janela temporal.
"""

import datetime

from django.db import models


class GrupoSuspensaoAlimentacaoDestaSemanaManager(models.Manager):
    """Manager que retorna suspensões de alimentação nos próximos 7 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo da semana atual.

        Returns:
            QuerySet: Suspensões cuja data está entre hoje e hoje + 7 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(GrupoSuspensaoAlimentacaoDestaSemanaManager, self)
            .get_queryset()
            .filter(
                suspensoes_alimentacao__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )


class GrupoSuspensaoAlimentacaoDesteMesManager(models.Manager):
    """Manager que retorna suspensões de alimentação nos próximos 31 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo do mês atual.

        Returns:
            QuerySet: Suspensões cuja data está entre hoje e hoje + 31 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(GrupoSuspensaoAlimentacaoDesteMesManager, self)
            .get_queryset()
            .filter(
                suspensoes_alimentacao__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )
