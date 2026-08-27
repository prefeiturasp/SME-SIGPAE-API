import datetime

import pytest
from model_bakery import baker

from src.dados_comuns import constants
from src.imr.models import PerfilDiretorSupervisao


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def escola():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    tipo_gestao = baker.make("TipoGestao", nome=constants.TIPOS_GESTAO.TERC_TOTAL.value)
    tipo_unidade = baker.make(
        "TipoUnidadeEscolar",
        iniciais=constants.TIPOS_UNIDADE_ESCOLAR.EMEF.value,
    )
    contato = baker.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )

    escola = baker.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def client_autenticado_diretor_escola(client, django_user_model, escola):
    email = "user@escola.com"
    password = constants.DJANGO_ADMIN_PASSWORD
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
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return {"client": client, "user": usuario}


@pytest.fixture
def client_autenticado_vinculo_nutrimanifestacao(client, django_user_model, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_nutrimanifestacao = baker.make(
        "Perfil",
        nome=constants.COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
        ativo=True,
        uuid="106f5a1a-627f-4b69-bf0b-6a44f6fa08bb",
    )

    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_nutrimanifestacao,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_administrador_supervisao_nutricao(
    client, django_user_model, codae
):
    email = "administrador.supervisao@test.com"
    senha = constants.DJANGO_ADMIN_PASSWORD
    usuario = django_user_model.objects.create_user(
        username=email,
        password=senha,
        email=email,
        registro_funcional="7654321",
        nome="Nutricionista administradora",
    )
    perfil = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_SUPERVISAO_NUTRICAO,
        ativo=True,
        uuid="4788c4ac-bce4-482b-a457-c78013b28aea",
    )
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=codae,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=senha)
    return client, usuario


@pytest.fixture
def client_autenticado_cogestor_dre(client, django_user_model):
    email = "cogestor.dre@test.com"
    senha = constants.DJANGO_ADMIN_PASSWORD
    usuario = django_user_model.objects.create_user(
        username=email,
        password=senha,
        email=email,
        registro_funcional="6543210",
        nome="Cogestor DRE",
    )
    perfil = baker.make(
        "Perfil",
        nome=constants.COGESTOR_DRE,
        ativo=True,
        uuid="44e531d8-6194-48c1-a939-f218db5b01f2",
    )
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        uuid="a1b37727-d7c8-43c7-a249-8980ea4ff44c",
    )
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=diretoria_regional,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=senha)
    return client, diretoria_regional


@pytest.fixture
def client_autenticado_terceirizada(client, django_user_model):
    email = "terceirizada.imr@test.com"
    senha = constants.DJANGO_ADMIN_PASSWORD
    usuario = django_user_model.objects.create_user(
        username=email,
        password=senha,
        email=email,
        registro_funcional="5432109",
        nome="Usuário da terceirizada",
    )
    perfil = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_EMPRESA,
        ativo=True,
        uuid="ed32f61e-a931-4eb6-aa63-3ce950d6d256",
    )
    terceirizada = baker.make(
        "Terceirizada",
        tipo_servico="TERCEIRIZADA",
        uuid="86939503-7383-464a-97af-2d62a356bcb4",
    )
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(username=email, password=senha)
    return client, terceirizada


@pytest.fixture
def tipo_ocorrencia_nutrisupervisor_com_parametrizacao(
    edital_factory,
    categoria_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    obrigacao_penalidade_factory,
):
    edital = edital_factory.create(eh_imr=True)

    categoria = categoria_ocorrencia_factory.create(
        perfis=[PerfilDiretorSupervisao.SUPERVISAO]
    )

    tipo_ocorrencia = tipo_ocorrencia_factory.create(
        edital=edital,
        descricao="Ocorrencia 1",
        perfis=[PerfilDiretorSupervisao.SUPERVISAO],
        categoria=categoria,
    )

    obrigacao_penalidade_factory.create(tipo_penalidade=tipo_ocorrencia.penalidade)

    parametrizacao_ocorrencia_factory.create(tipo_ocorrencia=tipo_ocorrencia)

    return tipo_ocorrencia
