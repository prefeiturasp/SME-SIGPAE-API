from celery import shared_task

from sme_sigpae_api.dieta_especial.utils import (
    cancela_dietas_ativas_automaticamente,
    inicia_dietas_temporarias,
    termina_dietas_especiais,
)
from sme_sigpae_api.perfil.models import Usuario


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_dietas_especiais_task():
    usuario_admin = Usuario.objects.get(pk=1)
    inicia_dietas_temporarias(usuario=usuario_admin)
    termina_dietas_especiais(usuario=usuario_admin)


@shared_task
def cancela_dietas_ativas_automaticamente_task():
    cancela_dietas_ativas_automaticamente()
