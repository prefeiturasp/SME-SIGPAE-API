import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.imr.models import PerfilDiretorSupervisao


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def escola():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = baker.make("TipoUnidadeEscolar", iniciais="EMEF")
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
