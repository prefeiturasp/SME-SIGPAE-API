from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
)
from src.escola.models import Codae


class PermissaoTermoRecebimentoDefinitivo(BasePermission):
    """Base das permissões do Termo de Recebimento Definitivo.

    Exige usuário autenticado, com vínculo ativo na CODAE e perfil
    presente em ``PERFIS_PERMITIDOS``, definido nas subclasses.
    """

    PERFIS_PERMITIDOS = []

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaCadastrarTermoRecebimentoDefinitivo(
    PermissaoTermoRecebimentoDefinitivo
):
    """Permissão para cadastrar Termo de Recebimento Definitivo.

    Apenas os perfis DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA
    podem cadastrar termos.
    """

    PERFIS_PERMITIDOS = [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]


class PermissaoParaVisualizarTermoRecebimentoDefinitivo(
    PermissaoTermoRecebimentoDefinitivo
):
    """Permissão para listar e detalhar Termo de Recebimento Definitivo.

    Além dos perfis que cadastram, os perfis DILOG_QUALIDADE (fiscais do
    termo) e DILOG_DIRETORIA podem visualizar os termos.
    """

    PERFIS_PERMITIDOS = [
        DILOG_CRONOGRAMA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_QUALIDADE,
        DILOG_DIRETORIA,
    ]
