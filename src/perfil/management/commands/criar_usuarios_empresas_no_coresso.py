import logging
import time

import environ
from django.core.management import BaseCommand

from src.eol_servico.utils import EOLServicoSGP
from src.perfil.models import Usuario, Vinculo

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
        self.cria_usuarios_empresa_no_coresso()

    def cria_usuarios_empresa_no_coresso(self):
        logger.info("Inicia criação/atribuição de usuários empresas no CoreSSO.")
        uuids_usuarios = (
            Vinculo.objects.filter(
                content_type__model="terceirizada", usuario__is_active=True, ativo=True
            )
            .exclude(usuario__cpf=None)
            .values_list("usuario__uuid", flat=True)
        )
        usuarios = Usuario.objects.filter(uuid__in=uuids_usuarios)
        logger.info(
            f"Foram encontrados {usuarios.count()} usuários para serem criados/atribuidos no CoreSSO."
        )

        usuarios_qtd = 0
        atribuidos_qtd = 0
        for usuario in usuarios:
            try:
                existe_core_sso = EOLServicoSGP.usuario_existe_core_sso(
                    login=usuario.username
                )
                if not existe_core_sso:
                    EOLServicoSGP.cria_usuario_core_sso(
                        login=usuario.username,
                        nome=usuario.nome,
                        email=usuario.email,
                        e_servidor=False,
                    )
                    usuarios_qtd += 1
                    logger.info(f"Usuario {usuario.username} criado no CoreSSO.")

                if usuario.vinculo_atual.perfil:
                    perfil = usuario.vinculo_atual.perfil.nome
                    EOLServicoSGP.atribuir_perfil_coresso(
                        login=usuario.username, perfil=perfil
                    )
                    atribuidos_qtd += 1

                usuario.last_login = None
                usuario.save()
                time.sleep(3)

            except Exception as e:
                msg = f"Erro ao tentar criar/atribuir usuário {usuario.username} no CoreSSO/SIGPAE: {str(e)}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))

        logger.info(
            f"{usuarios_qtd} usuarios foram criados e tiveram perfis atribuidos no CoreSSO SIGPAE."
        )
