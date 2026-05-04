import datetime
import logging
import time

import environ
from django.core.management import BaseCommand

from src.eol_servico.utils import EOLServicoSGP
from src.perfil.models import Usuario

logger = logging.getLogger("sigpae.cmd_cria_usuarios_no_coresso")

env = environ.Env()


class Command(BaseCommand):
    help = "Cria ou atribui acesso ao SIGPAE a usuários servidores (que possuem RF) no CoreSSO"

    def handle(self, *args, **options):
        if env("DJANGO_ENV") != "production":
            self.stdout.write(
                self.style.ERROR(
                    "SOMENTE USUÁRIOS DE PRODUÇÃO PODEM SER CRIADOS EM MASSA NO CORESSO!"
                )
            )
            return
        self.cria_usuarios_servidores_no_coresso()

    def cria_usuarios_servidores_no_coresso(self):  # noqa
        logger.info("Inicia criação/atribuição de usuários servidores no CoreSSO.")

        usuarios = (
            Usuario.objects.exclude(is_active=False)
            .exclude(email__contains="@admin.com")
            .exclude(email__contains="@amcom.com.br")
            .exclude(registro_funcional=None)
            .exclude(registro_funcional="")
            .exclude(vinculos__isnull=True)
        )

        logger.info(
            f"Foram encontrados {usuarios.count()} usuários para serem criados/atribuidos no CoreSSO."
        )

        usuarios_qtd = 0
        atribuidos_qtd = 0
        usuarios_sem_coresso = []
        for usuario in usuarios:
            try:
                if len(usuario.registro_funcional) == 7:
                    existe_core_sso = EOLServicoSGP.usuario_existe_core_sso(
                        login=usuario.username
                    )
                    if not existe_core_sso:
                        EOLServicoSGP.cria_usuario_core_sso(
                            login=usuario.username,
                            nome=usuario.nome,
                            email=usuario.email,
                            e_servidor=True,
                        )
                        logger.info(f"Usuario {usuario.username} criado no CoreSSO.")
                        usuarios_sem_coresso.append(usuario.registro_funcional)
                        usuarios_qtd += 1
                        usuario.last_login = None
                        usuario.save()
                    else:
                        usuario.last_login = datetime.datetime.now()
                        usuario.save()
                    if usuario.vinculo_atual and usuario.vinculo_atual.perfil:
                        perfil = usuario.vinculo_atual.perfil.nome
                        EOLServicoSGP.atribuir_perfil_coresso(
                            login=usuario.username, perfil=perfil
                        )
                        atribuidos_qtd += 1
                    time.sleep(0.3)

            except Exception as e:
                msg = f"Erro ao tentar criar/atribuir usuário {usuario.username} no CoreSSO/SIGPAE: {str(e)}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))

            logger.info(
                f"{usuarios_qtd} usuarios foram criados e {atribuidos_qtd} tiveram perfis atribuidos no CoreSSO."
            )
        logger.info(usuarios_sem_coresso)
