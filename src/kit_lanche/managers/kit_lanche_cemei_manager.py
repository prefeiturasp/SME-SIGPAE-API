import datetime

from django.db import models


class SolicitacoesKitLancheCemeiDestaSemanaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(SolicitacoesKitLancheCemeiDestaSemanaManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )


class SolicitacoesKitLancheCemeiDesteMesManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(SolicitacoesKitLancheCemeiDesteMesManager, self)
            .get_queryset()
            .filter(data__range=(data_limite_inicial, data_limite_final))
        )
