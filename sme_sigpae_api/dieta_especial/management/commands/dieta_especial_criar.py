from django.core.management.base import BaseCommand
from faker import Faker

from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.models import Aluno, Escola
from sme_sigpae_api.perfil.models import Usuario

faker = Faker()
fake = Faker("pt-br")


def criar_dieta(codigo_eol_aluno, codigo_eol_escola):
    aluno = Aluno.objects.filter(codigo_eol=codigo_eol_aluno).first()
    escola_destino = Escola.objects.get(codigo_eol=codigo_eol_escola)

    if escola_destino.codigo_eol == "017981":
        email = "escolaemef@admin.com"
    if escola_destino.codigo_eol == "099791":
        email = "escolaemef3@admin.com"

    criado_por = Usuario.objects.get(email=email)
    dieta_existe = SolicitacaoDietaEspecial.objects.filter(
        aluno__codigo_eol=codigo_eol_aluno
    ).first()
    if not dieta_existe:
        dieta = SolicitacaoDietaEspecial.objects.create(
            criado_por=criado_por,
            ativo=False,
            aluno=aluno,
            escola_destino=escola_destino,
            nome_completo_pescritor=fake.name(),
            registro_funcional_pescritor=codigo_eol_aluno[:6],
            observacoes=fake.paragraph(nb_sentences=10),
        )
        dieta.inicia_fluxo(user=criado_por)


class Command(BaseCommand):
    help = """
    Cria uma Dieta Especial, informando aluno e escola.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--aluno", "-a", dest="aluno", help="Informar código EOL do aluno."
        )
        parser.add_argument(
            "--escola",
            "-e",
            dest="escola",
            help="Informar código EOL da escola. Pericles 017981, Plinio 099791",
        )

    def handle(self, *args, **options):
        aluno = options["aluno"]
        escola = options["escola"]
        criar_dieta(aluno, escola)
