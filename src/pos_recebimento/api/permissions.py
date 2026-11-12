from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    ADMINISTRADOR_UE,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    DIRETOR_UE,
)
from src.escola.models import Codae, Escola


class PermissaoTermoRecebimentoProvisorio(BasePermission):
    """Base das permissões do Termo de Recebimento Provisório.

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


class PermissaoParaCadastrarTermoRecebimentoProvisorio(
    PermissaoTermoRecebimentoProvisorio
):
    """Permissão para cadastrar Termo de Recebimento Provisório.

    Apenas os perfis DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA
    podem cadastrar termos.
    """

    PERFIS_PERMITIDOS = [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]


class PermissaoParaAssinarTermoRecebimentoProvisorio(
    PermissaoTermoRecebimentoProvisorio
):
    """Permissão para o Fiscal do Contrato assinar o termo.

    Apenas o perfil DILOG_QUALIDADE pode assinar. A checagem de que o
    usuário é um dos três fiscais do termo é feita na action.
    """

    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]


class PermissaoParaAcessarPainelAssinaturas(PermissaoTermoRecebimentoProvisorio):
    """Permissão para o Painel de Assinaturas, exclusiva de DILOG_QUALIDADE."""

    PERFIS_PERMITIDOS = [DILOG_QUALIDADE]


class PermissaoParaVisualizarTermoRecebimentoProvisorio(
    PermissaoTermoRecebimentoProvisorio
):
    """Permissão para listar e detalhar Termo de Recebimento Provisório.

    Além dos perfis que cadastram, os perfis DILOG_QUALIDADE (fiscais do
    termo) e DILOG_DIRETORIA podem visualizar os termos.
    """

    PERFIS_PERMITIDOS = [
        DILOG_CRONOGRAMA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_QUALIDADE,
        DILOG_DIRETORIA,
    ]


class PermissaoParaGerarPdfTermoRecebimentoProvisorio(
    PermissaoTermoRecebimentoProvisorio
):
    """Permissão para gerar o PDF do Termo de Recebimento Provisório.

    Apenas os perfis contemplados na história (DILOG_QUALIDADE,
    DILOG_DIRETORIA, DILOG_CRONOGRAMA e COORDENADOR_CODAE_DILOG_LOGISTICA)
    podem baixar o documento. Empresas fornecedoras não têm acesso.
    """

    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        DILOG_DIRETORIA,
        DILOG_CRONOGRAMA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
    ]


class PermissaoParaRegistrarMemorandoOcorrencia(BasePermission):
    """Permissão para registrar ocorrências pelo Memorando de Ocorrências.

    Apenas os perfis DIRETOR_UE e ADMINISTRADOR_UE vinculados a uma Escola
    podem registrar ocorrências. A escola do registro é derivada do vínculo
    do usuário autenticado.
    """

    message = "O seu perfil não tem permissão para registrar ocorrências."

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE, ADMINISTRADOR_UE]
        )
