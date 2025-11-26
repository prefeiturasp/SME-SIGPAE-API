from django.core.management.base import BaseCommand
from faker import Faker

from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.perfil.models import Usuario

faker = Faker()
fake = Faker("pt-br")


def cancelar_dieta(dieta_uuid):
    usuario_nutricodae = Usuario.objects.get(email="nutricodae@admin.com")

    dieta = SolicitacaoDietaEspecial.objects.get(uuid__startswith=dieta_uuid)
    usuario = dieta.criado_por

    justificativa = f"<p>{fake.paragraph(nb_sentences=10)}</p>"
    dieta.inicia_fluxo_inativacao(user=usuario, justificativa=justificativa)

    dieta.cancelar_pedido(user=usuario_nutricodae, justificativa=justificativa)
    dieta.save()

    return dieta


class Command(BaseCommand):
    help = """
    Cancela uma Dieta Especial, informando o uuid da Dieta.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            "-u",
            dest="uuid",
            help="Informar uuid (5 primeiros dígitos) da dieta.",
        )

    def handle(self, *args, **options):
        uuid = options["uuid"]
        dieta = cancelar_dieta(uuid)
        self.stdout.write(f"Dieta Cancelada: {dieta}")
