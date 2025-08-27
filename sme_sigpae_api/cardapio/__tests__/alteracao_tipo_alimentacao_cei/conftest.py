import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.models import TemplateMensagem


@pytest.fixture
def alteracao_cardapio_cei(escola, template_mensagem_alteracao_cardapio):
    return baker.make(
        AlteracaoCardapioCEI,
        escola=escola,
        observacao="teste",
        data=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )


@pytest.fixture
def client_autenticado_vinculo_escola_cei_cardapio(
    client, django_user_model, escola_cei, template_mensagem_alteracao_cardapio
):
    email = "test@test.com"
    rf = "8888888"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional="8888888"
    )
    assert escola_cei.tipo_gestao.nome == "TERC TOTAL"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
        GrupoSuspensaoAlimentacao,
        criado_por=user,
        escola=escola_cei,
        rastro_escola=escola_cei,
    )
    client.login(username=rf, password=password)
    return client

@pytest.fixture
def client_autenticado_vinculo_codae_inclusao(client, django_user_model, escola, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_alimentacao,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client

@pytest.fixture
def template_inclusao_normal():
    return baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.INCLUSAO_ALIMENTACAO,
        template_html="@id @criado_em @status @link",
    )

@pytest.fixture
def client_autenticado_vinculo_dre_inclusao(
    client, django_user_model, escola, template_inclusao_normal
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_cogestor = baker.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client
