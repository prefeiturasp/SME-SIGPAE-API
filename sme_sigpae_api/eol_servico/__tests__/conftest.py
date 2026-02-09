import datetime

import pytest
from faker import Faker
from model_bakery import baker

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
import sme_sigpae_api.escola.models as models

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture(
    params=[
        ("2013-06-18T00:00:00", 2013, 6, 18),
        ("2014-02-15T00:00:00", 2014, 2, 15),
        ("1989-10-02T00:00:00", 1989, 10, 2),
    ]
)
def datas_nascimento_api(request):
    return request.param


@pytest.fixture
def tipo_gestao():
    return baker.make(models.TipoGestao, nome=fake.name())


@pytest.fixture
def lote():
    return baker.make(models.Lote, nome="lote", iniciais="lt")


@pytest.fixture
def diretoria_regional():
    return baker.make(
        models.DiretoriaRegional,
        nome="DRE Teste",
        codigo_eol="123456"
    )


@pytest.fixture
def escola(lote, tipo_gestao, diretoria_regional):
    return baker.make(
        models.Escola,
        lote=lote,
        tipo_gestao=tipo_gestao,
        diretoria_regional=diretoria_regional,
        codigo_eol="000001"
    )


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model):
    email = "user@escola.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional="123456",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=baker.make(
            "Escola",
            nome=fake.name(),
        ),
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def mock_eol_response_success():
    """Mock da resposta bem-sucedida do EOL"""
    return {
        "nome": "João da Silva",
        "email": "joao.silva@email.com",
        "cpf": "12345678900",
        "rf": "9876543",
        "cargos": [
            {
                "codigoUnidade": "123456",
                "descricaoUnidade": "EMEF Teste",
                "descricaoCargo": "Professor"
            }
        ]
    }


@pytest.fixture
def mock_serializer_usuario_codae():
    """Mock do serializer para usuário CODAE"""
    return {
        "uuid": "test-uuid",
        "nome": "Usuario CODAE",
        "email": "codae@teste.com",
        "registro_funcional": "1234567",
        "vinculo_atual": {
            "perfil": {
                "visao": "CODAE"
            },
            "instituicao": {
                "codigo_eol": "123456"
            }
        }
    }


@pytest.fixture
def mock_serializer_usuario_dre():
    return {
        "uuid": "test-uuid-dre",
        "nome": "Usuario DRE",
        "email": "dre@teste.com",
        "registro_funcional": "7654321",
        "vinculo_atual": {
            "perfil": {
                "visao": "DRE"
            },
            "instituicao": {
                "codigo_eol": "123456"
            }
        }
    }

