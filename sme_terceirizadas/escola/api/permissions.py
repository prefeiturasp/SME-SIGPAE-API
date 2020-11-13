from rest_framework import permissions

from ...dados_comuns.constants import (
    COGESTOR,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_ESCOLA,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    SUPLENTE
)


class PodeCriarAdministradoresDaEscola(permissions.BasePermission):
    message = 'O seu perfil não tem permissao para criar administradores da escola'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            return usuario.vinculo_atual.perfil.nome == COORDENADOR_ESCOLA
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.vinculo_atual.instituicao == obj


class PodeCriarAdministradoresDaDiretoriaRegional(permissions.BasePermission):
    message = 'O seu perfil não tem permissao para criar administradores da diretoria regional'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_cogestor_ou_suplente = usuario.vinculo_atual.perfil.nome in [COGESTOR, SUPLENTE]  # noqa
            return perfil_cogestor_ou_suplente
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        tem_vinculo_que_pode_criar_administradores = user.vinculo_atual.instituicao == obj
        if tem_vinculo_que_pode_criar_administradores:
            return True
        return False


class PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada(permissions.BasePermission):
    message = 'O seu perfil não tem permissão para criar administradores da codae - gestão alimentação'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_coordenador_gestao_alimentacao = (
                usuario.vinculo_atual.perfil.nome == COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA
            )
            return perfil_coordenador_gestao_alimentacao
        return False


class PodeCriarAdministradoresDaCODAEGestaoDietaEspecial(permissions.BasePermission):
    message = 'O seu perfil não tem permissão para criar administradores da codae - dieta especial'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_coordenador_gestao_alimentacao = (
                usuario.vinculo_atual.perfil.nome == COORDENADOR_DIETA_ESPECIAL
            )
            return perfil_coordenador_gestao_alimentacao
        return False


class PodeCriarAdministradoresDaCODAEGestaoProdutos(permissions.BasePermission):
    message = 'O seu perfil não tem permissão para criar administradores da codae - gestão de produtos'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_coordenador_gestao_alimentacao = (
                usuario.vinculo_atual.perfil.nome == COORDENADOR_GESTAO_PRODUTO
            )
            return perfil_coordenador_gestao_alimentacao
        return False


class PodeCriarAdministradoresDaCODAESupervisaoNutricao(permissions.BasePermission):
    message = 'O seu perfil não tem permissão para criar administradores da codae - gestão de produtos'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_coordenador_gestao_alimentacao = (
                usuario.vinculo_atual.perfil.nome == COORDENADOR_SUPERVISAO_NUTRICAO
            )
            return perfil_coordenador_gestao_alimentacao
        return False
