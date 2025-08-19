import datetime

import pytest
from faker import Faker
from model_bakery import baker

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD

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
