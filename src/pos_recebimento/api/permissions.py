from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
)
from src.escola.models import Codae


class PermissaoParaCadastrarTermoRecebimentoDefinitivo(BasePermission):
    """Permissão para cadastrar/visualizar Termo de Recebimento Definitivo.

    Apenas os perfis DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA
    (vinculados à CODAE) podem acessar as funcionalidades do módulo
    Pós-Recebimento.
    """

    PERFIS_PERMITIDOS = [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )
