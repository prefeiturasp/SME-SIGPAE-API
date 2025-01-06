import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from utility.carga_dados.perfil.importa_dados import (
    importa_usuarios_externos_coresso,
    importa_usuarios_servidores_coresso,
    importa_usuarios_ues_parceiras_coresso,
    valida_arquivo_importacao_usuarios,
)

from ..eol_servico.utils import EOLException, EOLServicoSGP
from .models import (
    Cargo,
    ImportacaoPlanilhaUsuarioExternoCoreSSO,
    ImportacaoPlanilhaUsuarioServidorCoreSSO,
    ImportacaoPlanilhaUsuarioUEParceiraCoreSSO,
    Usuario,
)
from .utils import get_cargo_eol

logger = logging.getLogger("sigpae.taskPerfil")


def get_usuario(registro_funcional):
    usuario = Usuario.objects.filter(registro_funcional=registro_funcional).first()
    if usuario:
        return usuario


def compara_e_atualiza_dados_do_eol(response, usuario):
    nome_cargo = get_cargo_eol(response)
    if not nome_cargo:
        return
    if usuario.cargo != nome_cargo:
        usuario.desativa_cargo()
        cargo = Cargo.objects.create(usuario=usuario, nome=nome_cargo)
        cargo.ativar_cargo()
        usuario.atualizar_cargo()


@shared_task
def busca_cargo_de_usuario(registro_funcional):
    try:
        usuario = get_usuario(registro_funcional)
        response = EOLServicoSGP.get_dados_usuario(registro_funcional)
        compara_e_atualiza_dados_do_eol(response, usuario)

    except EOLException:
        logger.debug(f"Usuario com rf {registro_funcional} não esta cadastro no EOL")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_planilha_usuario_externo_coresso_async(username, arquivo_uuid):
    logger.info("Processando arquivo %s", arquivo_uuid)
    try:
        arquivo = ImportacaoPlanilhaUsuarioExternoCoreSSO.objects.get(uuid=arquivo_uuid)
        usuario = get_user_model().objects.get(username=username)
        logger.info("Arquivo encontrado %s", arquivo_uuid)

        if valida_arquivo_importacao_usuarios(arquivo=arquivo):
            importa_usuarios_externos_coresso(usuario, arquivo)
    except ObjectDoesNotExist:
        logger.info("Arquivo não encontrado %s", arquivo_uuid)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_planilha_usuario_servidor_coresso_async(username, arquivo_uuid):
    logger.info("Processando arquivo %s", arquivo_uuid)
    try:
        arquivo = ImportacaoPlanilhaUsuarioServidorCoreSSO.objects.get(
            uuid=arquivo_uuid
        )
        usuario = get_user_model().objects.get(username=username)
        logger.info("Arquivo encontrado %s", arquivo_uuid)

        if valida_arquivo_importacao_usuarios(arquivo=arquivo):
            importa_usuarios_servidores_coresso(usuario, arquivo)
    except ObjectDoesNotExist:
        logger.info("Arquivo não encontrado %s", arquivo_uuid)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def processa_planilha_usuario_ue_parceira_coresso_async(username, arquivo_uuid):
    logger.info("Processando arquivo %s", arquivo_uuid)
    try:
        arquivo = ImportacaoPlanilhaUsuarioUEParceiraCoreSSO.objects.get(
            uuid=arquivo_uuid
        )
        usuario = get_user_model().objects.get(username=username)
        logger.info("Arquivo encontrado %s", arquivo_uuid)

        if valida_arquivo_importacao_usuarios(arquivo=arquivo):
            importa_usuarios_ues_parceiras_coresso(usuario, arquivo)
    except ObjectDoesNotExist:
        logger.info("Arquivo não encontrado %s", arquivo_uuid)
