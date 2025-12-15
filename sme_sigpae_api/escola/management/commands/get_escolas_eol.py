import tempfile

from django.core.management.base import BaseCommand

from sme_sigpae_api.escola.utils_escola import get_escolas


class Command(BaseCommand):
    help = """
    Lê uma planilha específica com Dietas Ativas a serem integradas no sistema.
    Pega todos os códigos EOL da escola na API do EOL.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            "-a",
            dest="arquivo",
            help="Informar caminho absoluto do arquivo xlsx.",
        )
        parser.add_argument(
            "--arquivo_codigos_escolas",
            "-ace",
            dest="arquivo_codigos_escolas",
            help="Informar caminho absoluto do arquivo xlsx.",
        )

    def handle(self, *args, **options):
        arquivo = options["arquivo"]
        arquivo_codigos_escolas = options["arquivo_codigos_escolas"]

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
        get_escolas(arquivo, arquivo_codigos_escolas, temp_filename, in_memory=False)
