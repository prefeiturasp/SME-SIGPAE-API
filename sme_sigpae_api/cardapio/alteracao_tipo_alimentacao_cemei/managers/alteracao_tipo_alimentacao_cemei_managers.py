import datetime

from django.db import models
from django.db.models import Q


class AlteracoesCardapioCEMEIDestaSemanaManager(models.Manager):
    def get_queryset(self):
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
    def get_queryset(self):
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
