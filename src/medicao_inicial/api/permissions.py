from rest_framework import permissions

from src.dados_comuns.constants import (
    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    ADMINISTRADOR_MEDICAO,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
)


class EhAdministradorMedicaoInicial(permissions.BasePermission):
    message = "O seu perfil não tem permissão para criar administradores da codae - gestão alimentação"

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            perfil_administrador_medicao_inicial = (
                usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_MEDICAO
            )
            return perfil_administrador_medicao_inicial
        return False


class EhAdministradorMedicaoInicialOuGestaoAlimentacao(permissions.BasePermission):
    message = "O seu perfil não tem permissão para criar administradores da codae - gestão alimentação"

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_anonymous:
            return (
                usuario.tipo_usuario == "escola"
                or usuario.vinculo_atual.perfil.nome
                in [
                    ADMINISTRADOR_MEDICAO,
                    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ]
            )
        return False
