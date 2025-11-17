from rest_framework.permissions import BasePermission

from sme_sigpae_api.dados_comuns.constants import (
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
    DILOG_QUALIDADE,
)


class PermissaoParaVisualizarQuestoesConferencia(BasePermission):
    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaCadastrarFichaRecebimento(BasePermission):
    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaVisualizarFichaRecebimento(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )
