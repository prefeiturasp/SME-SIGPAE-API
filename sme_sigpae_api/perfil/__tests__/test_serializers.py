import pytest

from sme_sigpae_api.escola.__tests__.conftest import mocked_response

from ...dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from ..__tests__.conftest import mocked_request_api_eol
from ..api.serializers import UsuarioUpdateSerializer
from ..models import Usuario

pytestmark = pytest.mark.django_db


def test_usuario_serializer(usuario_serializer):
    assert usuario_serializer.data is not None


def test_usuario_update_serializer_partial_update(
    monkeypatch, usuario_update_serializer, usuario_3
):
    dados_usuario = {
        "password": DJANGO_ADMIN_PASSWORD,
        "confirmar_password": DJANGO_ADMIN_PASSWORD,
        "email": "nome.completo@sme.prefeitura.sp.gov.br",
        "registro_funcional": "7654321",
        "cpf": "22222222222",
    }
    monkeypatch.setattr(Usuario, "pode_efetuar_cadastro", lambda: True)
    usuario = usuario_update_serializer.partial_update(usuario_3, dados_usuario)
    assert usuario.cpf == "22222222222"
    assert usuario.email == "nome.completo@sme.prefeitura.sp.gov.br"
    assert usuario.registro_funcional == "7654321"


def test_usuario_update_serializer_create(monkeypatch):
    monkeypatch.setattr(
        UsuarioUpdateSerializer,
        "get_dados_usuario",
        lambda p1, p2: mocked_response(mocked_request_api_eol(), 200),
    )
    data = {"registro_funcional": "5858585", "instituicao": "IRAPARA"}
    usuario = UsuarioUpdateSerializer(data).create(validated_data=data)
    assert isinstance(usuario, Usuario)
    assert usuario.registro_funcional == "5858585"
    assert usuario.is_active is False
    assert usuario.cpf == "34811126025"
