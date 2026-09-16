"""Permissões da API do módulo de recebimento."""

from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
)


class PermissaoParaVisualizarQuestoesConferencia(BasePermission):
    """Permite visualizar as questões de conferência.

    Apenas usuários com perfil ``DILOG_QUALIDADE``.
    """

    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]

    def has_permission(self, request, view):
        """Verifica se o usuário autenticado possui perfil permitido."""
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaCadastrarFichaRecebimento(BasePermission):
    """Permite cadastrar fichas de recebimento.

    Apenas usuários com perfil ``DILOG_QUALIDADE``.
    """

    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]

    def has_permission(self, request, view):
        """Verifica se o usuário autenticado possui perfil permitido."""
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaVisualizarFichaRecebimento(BasePermission):
    """Permite visualizar fichas de recebimento.

    Perfis permitidos: ``DILOG_QUALIDADE``,
    ``COORDENADOR_CODAE_DILOG_LOGISTICA``, ``DILOG_CRONOGRAMA``,
    ``DILOG_DIRETORIA`` e ``DILOG_ABASTECIMENTO``.
    """

    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        DILOG_DIRETORIA,
        DILOG_ABASTECIMENTO,
    ]

    def has_permission(self, request, view):
        """Verifica se o usuário autenticado possui perfil permitido."""
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )
