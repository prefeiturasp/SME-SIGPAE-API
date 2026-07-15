from rest_framework import permissions

from ...dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
)


class PodeAlterarTerceirizadasPermission(permissions.BasePermission):
    message = "O seu perfil não tem permissao para alterar terceirizadas"

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True


class PodeCriarAdministradoresDaTerceirizada(permissions.BasePermission):
    message = (
        "O seu perfil não tem permissao para criar administradores da terceirizada"
    )

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_nutri_admin = usuario.vinculo_atual.perfil.nome in [
                ADMINISTRADOR_EMPRESA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                COORDENADOR_DIETA_ESPECIAL,
            ]
            return perfil_nutri_admin
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        tem_vinculo_que_pode_criar_administradores = (
            user.vinculo_atual.instituicao == obj
        )
        if tem_vinculo_que_pode_criar_administradores:
            return True
        return False
