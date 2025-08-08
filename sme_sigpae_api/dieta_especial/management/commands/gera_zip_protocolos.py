import zipfile
from io import BytesIO

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from weasyprint import HTML

from sme_sigpae_api.dados_comuns.utils import envia_email_unico_com_anexo_inmemory
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.relatorios.relatorios import relatorio_dieta_especial_protocolo


class Command(BaseCommand):
    help = "Gera PDFs dos protocolos de dieta especial, salva um .zip em /tmp e envia por e-mail"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lote", required=True, type=str, help="Nome do lote (obrigatório)"
        )
        parser.add_argument(
            "--email", required=True, type=str, help="E-mail de destino (obrigatório)"
        )
        parser.add_argument(
            "--inicio", type=int, default=0, help="Índice inicial (opcional)"
        )
        parser.add_argument(
            "--fim", type=int, default=None, help="Índice final (opcional)"
        )

    def handle(self, *args, **options):
        lote = options["lote"]
        email = options["email"]
        inicio = options["inicio"]
        fim = options["fim"]

        zip_filename = f"protocolos_dieta_especial_{lote}.zip"
        buffer_zip = BytesIO()

        dietas = SolicitacaoDietaEspecial.objects.filter(
            status="CODAE_AUTORIZADO", escola_destino__lote__nome=lote
        ).order_by("id")[inicio:fim]

        if not dietas.exists():
            raise CommandError("Nenhuma dieta encontrada com os filtros fornecidos.")

        with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for dieta in dietas:
                nome = dieta.aluno.nome.replace("/", "-")
                codigo = dieta.aluno.codigo_eol or "Nao matriculado"
                filename = f"Protocolo - {nome} - {codigo}.pdf"

                html_string = relatorio_dieta_especial_protocolo(None, dieta)
                pdf_buffer = BytesIO()
                HTML(string=html_string, base_url=settings.STATIC_URL).write_pdf(
                    pdf_buffer
                )

                zip_file.writestr(filename, pdf_buffer.getvalue())
                self.stdout.write(self.style.SUCCESS(f"Adicionado: {filename}"))

        envia_email_unico_com_anexo_inmemory(
            assunto=f"Protocolos de Dieta Especial - {lote} - {inicio} a {fim}",
            corpo=f"""
                <p>Olá,</p>
                <p>Segue em anexo o arquivo ZIP com os protocolos do lote <strong>{lote}</strong>.</p>
                <p>Atenciosamente,<br>SIGPAE</p>
            """,
            email=email,
            anexo_nome=zip_filename,
            mimetypes="application/zip",
            anexo=buffer_zip.getvalue(),
        )

        self.stdout.write(self.style.SUCCESS(f"E-mail enviado para {email}"))
