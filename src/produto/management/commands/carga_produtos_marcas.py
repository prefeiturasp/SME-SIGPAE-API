from django.conf import settings
from django.core.management.base import BaseCommand

from utility.carga_dados.produto.importa_dados import cria_marca2, cria_produto_marca


class Command(BaseCommand):
    help = "Importa produtos e marcas no banco de dados."

    def handle(self, *args, **options):
        self.stdout.write("Importando dados...")

        if settings.DEBUG:
            cria_marca2()
            cria_produto_marca()
