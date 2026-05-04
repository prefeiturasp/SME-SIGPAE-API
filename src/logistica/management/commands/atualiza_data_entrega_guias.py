from datetime import date, timedelta

from django.core.management.base import BaseCommand

from src.logistica.models import Guia


class Command(BaseCommand):
    """
    Script feito para atualizar a data de entrega das guias.
    Em caso de data vencida a guia com a data atualizada poderá ser utilida novamente.
    """

    help = "Atualiza data de entrega das guias de remessa"

    # flake8: noqa: C901
    def handle(self, *args, **options):
        print("")
        print("")
        print("Início...")
        print("")

        guias = Guia.objects.all()
        nova_data = date.today() + timedelta(days=30)
        print("Nova data de entrega: " + str(nova_data))
        guias.update(data_entrega=nova_data)
        print(f"Quantidade de guias atualizadas: {guias.count()}")

        print("")
        print("")
        print("Fim...")
        print("")
        print("")
