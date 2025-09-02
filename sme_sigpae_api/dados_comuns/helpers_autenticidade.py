from rest_framework import status
from rest_framework.response import Response


def verificar_autenticidade_usuario(request, data=None):
    """
    Verifica a autenticidade do usuário com base na senha fornecida.

    Args:
        request: O objeto request do Django REST Framework
        data: Dicionário opcional contendo os dados da requisição (se None, usa request.data)

    Returns:
        Response com status 401 se a autenticação falhar, None se for bem-sucedida
    """
    data = data or request.data
    usuario = request.user
    password = data.get("password", "")

    if not usuario.verificar_autenticidade(password):
        return Response(
            {
                "Senha inválida. Em caso de esquecimento de senha, solicite a recuperação e tente novamente."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return None
