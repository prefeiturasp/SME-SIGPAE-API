import datetime
import logging

from django.core.management import BaseCommand

from src.perfil.models import Vinculo

logger = logging.getLogger("sigpae.normaliza_vinculos")


class Command(BaseCommand):
    help = "Normaliza vinculos com status errado"

    def handle(self, *args, **options):
        self.normaliza_vinculos()

    def normaliza_vinculos(self):
        hoje = datetime.date.today()
        Vinculo.objects.filter(
            ativo=True, data_inicial__isnull=False, data_final__isnull=False
        ).update(ativo=False)
        Vinculo.objects.filter(
            ativo=True, data_inicial__isnull=True, data_final__isnull=True
        ).update(data_inicial=hoje)
        Vinculo.objects.filter(
            ativo=False, data_inicial__isnull=False, data_final__isnull=True
        ).update(ativo=True)
        Vinculo.objects.filter(
            ativo=False, data_inicial__isnull=True, data_final__isnull=False
        ).update(data_inicial=hoje)
