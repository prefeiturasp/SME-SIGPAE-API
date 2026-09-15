from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    USUARIO_EMPRESA,
)
from src.escola.models import Codae
from src.terceirizada.models import Terceirizada


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


def usuario_vinculado_a_empresa_fornecedor(usuario):
    """Retorna True quando o usuário possui vínculo ativo em empresa do
    tipo fornecedor (FORNECEDOR ou FORNECEDOR_E_DISTRIBUIDOR)."""
    vinculo = usuario.vinculo_atual
    return (
        not usuario.is_anonymous
        and vinculo is not None
        and isinstance(vinculo.instituicao, Terceirizada)
        and vinculo.instituicao.eh_fornecedor
    )


class PermissaoParaVisualizarTermoRecebimentoDefinitivoEmpresa(BasePermission):
    """Permissão para o fornecedor visualizar os termos da sua empresa.

    Perfis ADMINISTRADOR_EMPRESA e USUARIO_EMPRESA com vínculo ativo em
    empresa fornecedora podem listar e detalhar os Termos de Recebimento
    Definitivo. O escopo de dados (apenas os termos da própria empresa)
    é aplicado no ``get_queryset`` do ViewSet.
    """

    message = "O seu perfil não tem permissão para visualizar os termos."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario_vinculado_a_empresa_fornecedor(usuario):
            return False

        return usuario.vinculo_atual.perfil.nome in [
            ADMINISTRADOR_EMPRESA,
            USUARIO_EMPRESA,
        ]


class PermissaoParaVisualizarTermoRecebimentoDefinitivo(
    PermissaoTermoRecebimentoDefinitivo
):
    """Permissão para listar e detalhar Termo de Recebimento Definitivo.

    Além dos perfis que cadastram, os perfis DILOG_QUALIDADE (fiscais do
    termo) e DILOG_DIRETORIA podem visualizar os termos. Os perfis de
    empresa fornecedora (ADMINISTRADOR_EMPRESA e USUARIO_EMPRESA) também
    podem visualizar, limitados aos termos da própria empresa.
    """

    PERFIS_PERMITIDOS = [
        DILOG_CRONOGRAMA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_QUALIDADE,
        DILOG_DIRETORIA,
    ]

    def has_permission(self, request, view):
        return super().has_permission(
            request, view
        ) or PermissaoParaVisualizarTermoRecebimentoDefinitivoEmpresa().has_permission(
            request, view
        )
