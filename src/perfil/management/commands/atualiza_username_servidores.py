import logging

from django.core.management import BaseCommand
from django.db.models import F

from src.perfil.models import Usuario

logger = logging.getLogger("sigpae.cmd_atualiza_username_servidores")


class Command(BaseCommand):
    help = "Atualiza username de usuários servidores (que possuem RF)"

    def handle(self, *args, **options):
        self.atualiza_username_com_rf()

    def atualiza_username_com_rf(self):
        Usuario.objects.exclude(email__contains="@admin.com").exclude(
            registro_funcional=None
        ).exclude(registro_funcional="").update(username=F("registro_funcional"))
