import datetime

from django.db import models


class AlteracoesCardapioCEIDestaSemanaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(AlteracoesCardapioCEIDestaSemanaManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioCEIDesteMesManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(AlteracoesCardapioCEIDesteMesManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )
