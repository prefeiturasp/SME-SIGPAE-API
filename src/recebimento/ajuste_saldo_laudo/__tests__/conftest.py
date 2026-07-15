import datetime

import pytest
from faker import Faker
from model_bakery import baker

from src.dados_comuns.constants import DILOG_QUALIDADE, DJANGO_ADMIN_PASSWORD
from src.recebimento.ajuste_saldo_laudo.models import (
    AjusteSaldo,
)

fake = Faker("pt_BR")


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def client_dilog_qualidade(client, django_user_model, codae):
    email = "dilogqualidade@test.com"
    password = DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email,
        password=password,
        email=email,
        registro_funcional=str(fake.unique.random_int(min=100000, max=999999)),
    )
    perfil_dilog_qualidade = baker.make(
        "Perfil",
        nome=DILOG_QUALIDADE,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dilog_qualidade,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def ficha():
    produto = baker.make("NomeDeProdutoEdital", nome="Açucar")
    ficha_tecnica = baker.make(
        "FichaTecnicaDoProduto",
        produto=produto,
        empresa=baker.make("Terceirizada", razao_social="Razao Social LTDA"),
    )
    return ficha_tecnica


@pytest.fixture
def cronograma(ficha):
    return baker.make(
        "Cronograma",
        numero="001/2022A",
        ficha_tecnica=ficha,
        empresa=baker.make("Terceirizada", razao_social="Razao Social LTDA"),
    )


@pytest.fixture
def documento_recebimento_alimentacao_escolar(cronograma):
    unidade = baker.make(
        "pre_recebimento.UnidadeMedida", nome="QUILOGRAMA", abreviacao="kg"
    )

    return baker.make(
        "DocumentoDeRecebimento",
        cronograma=cronograma,
        numero_laudo="LAU-2024-002-ALIMENTACAO",
        unidade_medida=unidade,
        status="ENVIADO_PARA_ANALISE",
    )


@pytest.fixture
def ajuste_saldo(client_dilog_qualidade, documento_recebimento_alimentacao_escolar):
    return baker.make(
        AjusteSaldo,
        documento_recebimento=documento_recebimento_alimentacao_escolar,
    )
