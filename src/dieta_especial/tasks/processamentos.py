from celery import shared_task

from src.perfil.models import Usuario

from .utils.processamentos import (
    cancela_dietas_ativas_automaticamente,
    cancela_dietas_pendente_autorizacao,
    inicia_dietas_temporarias,
    termina_dietas_especiais,
)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_dietas_especiais_task():
    usuario_admin = Usuario.objects.get(pk=1)
    inicia_dietas_temporarias()
    termina_dietas_especiais(usuario=usuario_admin)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def cancela_dietas_ativas_automaticamente_task():
    cancela_dietas_ativas_automaticamente()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def cancela_dietas_pendente_autorizacao_task():
    cancela_dietas_pendente_autorizacao()
