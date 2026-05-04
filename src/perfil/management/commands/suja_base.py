import logging

import environ
from django.core.management import BaseCommand
from django.db.models import Q, Value
from django.db.models.functions import Concat

from src.dados_comuns.models import Contato
from src.perfil.models import Usuario
from src.terceirizada.models import EmailTerceirizadaPorModulo, Terceirizada

logger = logging.getLogger("sigpae.cmd_suja_base")

env = environ.Env()


class Command(BaseCommand):
    help = "Suja base de dados para que não tenha e-mails verdadeiros em ambientes que não são produção"

    def handle(self, *args, **options):
        if env("DJANGO_ENV") == "production":
            self.stdout.write(self.style.ERROR("PRODUÇÃO! NÃO PODE SUJAR A BASE"))
            return
        filtro_ignorar = (
            Q(email__isnull=True)
            | Q(email="")
            | Q(email__icontains="fake_")
            | Q(email__icontains="@admin.com")
            | Q(email__icontains="@amcom.com")
        )
        self.suja_emails_usuarios(filtro_ignorar)
        self.suja_emails_contatos(filtro_ignorar)
        self.suja_representante_emails_terceirizadas()
        self.suja_responsavel_emails_terceirizadas()
        self.suja_modulos_emails_terceirizadas()

    def suja_emails_usuarios(self, filtro):
        usuarios = Usuario.objects.exclude(filtro)
        self.stdout.write(
            self.style.SUCCESS(f"Atualizando {usuarios.count()} usuarios")
        )
        qtd_atualizados = usuarios.update(email=Concat(Value("fake_"), "email"))
        self.stdout.write(self.style.SUCCESS(f"{qtd_atualizados} atualizados"))

    def suja_emails_contatos(self, filtro):
        contatos = Contato.objects.exclude(filtro)
        self.stdout.write(
            self.style.SUCCESS(f"Atualizando {contatos.count()} contatos")
        )
        qtd_contatos = contatos.update(email=Concat(Value("fake_"), "email"))
        self.stdout.write(self.style.SUCCESS(f"{qtd_contatos} atualizados"))

    def suja_representante_emails_terceirizadas(self):
        terceirizadas_representante_email = Terceirizada.objects.exclude(
            Q(representante_email__isnull=True)
            | Q(representante_email="")
            | Q(representante_email__icontains="fake_")
            | Q(representante_email__icontains="@admin.com")
            | Q(representante_email__icontains="@amcom.com")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Atualizando {terceirizadas_representante_email.count()} "
                "terceirizadas no campo representante_email"
            )
        )
        qtd_terceirizadas = terceirizadas_representante_email.update(
            representante_email=Concat(Value("fake_"), "representante_email")
        )
        self.stdout.write(self.style.SUCCESS(f"{qtd_terceirizadas} atualizados"))

    def suja_responsavel_emails_terceirizadas(self):
        terceirizadas_responsavel_email = Terceirizada.objects.exclude(
            Q(responsavel_email__isnull=True)
            | Q(responsavel_email="")
            | Q(responsavel_email__icontains="fake_")
            | Q(responsavel_email__icontains="@admin.com")
            | Q(responsavel_email__icontains="@amcom.com")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Atualizando {terceirizadas_responsavel_email.count()} "
                "terceirizadas no campo responsavel_email"
            )
        )
        qtd_terceirizadas = terceirizadas_responsavel_email.update(
            responsavel_email=Concat(Value("fake_"), "responsavel_email")
        )
        self.stdout.write(self.style.SUCCESS(f"{qtd_terceirizadas} atualizados"))

    def suja_modulos_emails_terceirizadas(self):
        terceirizadas_modulos_emails = EmailTerceirizadaPorModulo.objects.exclude(
            Q(email__isnull=True)
            | Q(email="")
            | Q(email__icontains="fake_")
            | Q(email__icontains="@admin.com")
            | Q(email__icontains="@amcom.com")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Atualizando {terceirizadas_modulos_emails.count()} "
                "terceirizadas no campo email nos módulos"
            )
        )
        qtd_terceirizadas = terceirizadas_modulos_emails.update(
            email=Concat(Value("fake_"), "email")
        )
        self.stdout.write(self.style.SUCCESS(f"{qtd_terceirizadas} atualizados"))
