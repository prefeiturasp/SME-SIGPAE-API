import datetime

from django.db import models


class GrupoSuspensaoAlimentacaoDestaSemanaManager(models.Manager):
    def get_queryset(self):
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
    def get_queryset(self):
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
