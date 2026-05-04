import logging

from django.core.management import BaseCommand
from django.db.models import F

from src.perfil.models import Usuario, Vinculo

logger = logging.getLogger("sigpae.cmd_atualiza_username_usuarios_empresas")


class Command(BaseCommand):
    help = "Atualiza username de usuários empresas (que possuem CPF)"

    def handle(self, *args, **options):
        self.atualiza_username_com_cpf()

    def atualiza_username_com_cpf(self):
        logger.info("Inicia atualização do campo username.")
        uuids_usuarios = (
            Vinculo.objects.filter(
                content_type__model="terceirizada", usuario__is_active=True, ativo=True
            )
            .exclude(usuario__cpf=None)
            .values_list("usuario__uuid", flat=True)
        )
        Usuario.objects.filter(uuid__in=uuids_usuarios).update(username=F("cpf"))
