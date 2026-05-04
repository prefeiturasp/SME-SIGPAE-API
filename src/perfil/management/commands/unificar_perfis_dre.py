import logging

from django.core.management import BaseCommand

from src.dados_comuns.constants import COGESTOR_DRE
from src.perfil.models import Perfil, Vinculo

logger = logging.getLogger("sigpae.atualiza_vinculos_de_perfis_removidos")


class Command(BaseCommand):
    help = "Migra usuários que possuam vinculos de SUPLENTE, ADMINISTRADOR E COGESTOR para COGESTOR_DRE."

    def handle(self, *args, **options):
        self.unificar_perfis_dre()

    def unificar_perfis_dre(self):
        perfil = Perfil.objects.get(nome__iexact=COGESTOR_DRE)
        Vinculo.objects.filter(
            perfil__nome__in=["ADMINISTRADOR_DRE", "SUPLENTE", "COGESTOR"]
        ).update(perfil=perfil)
