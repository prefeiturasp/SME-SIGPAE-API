import datetime
from unittest.mock import MagicMock, patch

import pytest
from faker import Faker
from model_mommy import mommy
from rest_framework.test import APIClient

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_EMPRESA

from ...perfil.models import Perfil, Usuario
from ..api.serializers.serializers import (
    ContratoSerializer,
    EditalContratosSerializer,
    EditalSerializer,
    EditalSimplesSerializer,
    EmailsTerceirizadaPorModuloSerializer,
    ModalidadeSerializer,
    TerceirizadaSimplesSerializer,
    VigenciaContratoSimplesSerializer,
)
from ..models import (
    Contrato,
    Edital,
    EmailTerceirizadaPorModulo,
    Modalidade,
    Modulo,
    Nutricionista,
    Terceirizada,
    VigenciaContrato,
)

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def client_autenticado_terceiro(client_autenticado):
    terceirizada = mommy.make(
        Terceirizada, contatos=[mommy.make("dados_comuns.Contato")], make_m2m=True
    )

    mommy.make(
        Nutricionista,
        terceirizada=terceirizada,
        contatos=[mommy.make("dados_comuns.Contato")],
    )
    mommy.make(
        Contrato,
        terceirizada=terceirizada,
        edital=mommy.make(Edital),
        make_m2m=True,
        uuid="44d51e10-8999-48bb-889a-1540c9e8c895",
    )
    return client_autenticado


@pytest.fixture
def usuario_2():
    return mommy.make(
        Usuario,
        uuid="8344f23a-95c4-4871-8f20-3880529767c0",
        nome="Fulano da Silva",
        username="fulano@teste.com",
        email="fulano@teste.com",
        cpf="11111111111",
        registro_funcional="1234567",
    )


@pytest.fixture(
    params=[
        # email, senha, rf, cpf
        ("cogestor_1@sme.prefeitura.sp.gov.br", "adminadmin", "0000001", "44426575052"),
        (
            "cogestor_2@sme.prefeitura.sp.gov.br",
            "aasdsadsadff",
            "0000002",
            "56789925031",
        ),
        ("cogestor_3@sme.prefeitura.sp.gov.br", "98as7d@@#", "0000147", "86880963099"),
        (
            "cogestor_4@sme.prefeitura.sp.gov.br",
            "##$$csazd@!",
            "0000441",
            "13151715036",
        ),
        (
            "cogestor_5@sme.prefeitura.sp.gov.br",
            "!!@##FFG121",
            "0005551",
            "40296233013",
        ),
    ]
)
def users_codae_gestao_alimentacao(client, django_user_model, request, usuario_2):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)

    codae = mommy.make(
        "Codae", nome="CODAE", uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd"
    )

    perfil_administrador_codae = mommy.make(
        "Perfil",
        nome="ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        uuid="48330a6f-c444-4462-971e-476452b328b2",
    )
    perfil_coordenador = mommy.make(
        "Perfil",
        nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    mommy.make(
        "Perfil",
        nome="ADMINISTRADOR_EMPRESA",
        ativo=True,
        uuid="11c22490-e040-4b4a-903f-54d1b1e57b08",
    )
    terceirizada = mommy.make(
        Terceirizada, uuid="66c1bdd1-9cec-4f1f-a2f6-008f27713e53", ativo=True
    )
    lote1 = mommy.make("Lote", uuid="143c2550-8bf0-46b4-b001-27965cfcd107")
    lote2 = mommy.make(
        "Lote", uuid="42d3887a-517b-4a72-be78-95d96d857236", terceirizada=terceirizada
    )
    mommy.make("DiretoriaRegional", uuid="9db1e5d8-dba3-4245-b937-a94c4ea44411")
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    hoje = datetime.date.today()
    amanha = datetime.date.today() + datetime.timedelta(days=1)
    mommy.make(
        "InclusaoAlimentacaoContinua",
        data_inicial=ontem,
        data_final=hoje,
        rastro_lote=lote1,
        rastro_terceirizada=terceirizada,
        terceirizada_conferiu_gestao=True,
    )
    mommy.make(
        "InclusaoAlimentacaoContinua",
        data_inicial=hoje,
        data_final=amanha,
        rastro_lote=lote2,
        rastro_terceirizada=terceirizada,
        terceirizada_conferiu_gestao=True,
    )
    mommy.make(
        "SolicitacaoDietaEspecial",
        rastro_lote=lote1,
        rastro_terceirizada=terceirizada,
        status="CODAE_AUTORIZADO",
        conferido=True,
    )
    mommy.make(
        "SolicitacaoDietaEspecial",
        rastro_lote=lote2,
        rastro_terceirizada=terceirizada,
        status="ESCOLA_CANCELOU",
    )
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_administrador_codae,
        ativo=False,
        data_inicial=hoje,
        data_final=hoje + datetime.timedelta(days=30),
    )  # finalizado
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_coordenador,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        "Vinculo",
        usuario=usuario_2,
        instituicao=codae,
        perfil=perfil_administrador_codae,
        data_inicial=hoje,
        ativo=True,
    )

    return client, email, password, rf, cpf, user


@pytest.fixture
def edital():
    return mommy.make(Edital, numero="1", objeto="lorem ipsum")


@pytest.fixture
def modulo():
    return mommy.make(Modulo, nome="Dieta Especial")


@pytest.fixture
def emailterceirizadapormodulo(terceirizada, modulo, usuario_2):
    return mommy.make(
        EmailTerceirizadaPorModulo,
        email="teste@teste.com",
        terceirizada=terceirizada,
        modulo=modulo,
        criado_por=usuario_2,
    )


@pytest.fixture
def contrato():
    return mommy.make(Contrato, numero="1", processo="12345")


@pytest.fixture
def vigencia_contrato(contrato):
    data_inicial = datetime.date(2019, 1, 1)
    data_final = datetime.date(2019, 1, 31)
    return mommy.make(
        VigenciaContrato,
        contrato=contrato,
        data_inicial=data_inicial,
        data_final=data_final,
    )


@pytest.fixture
def vigencia_contrato_serializer(vigencia_contrato):
    return VigenciaContratoSimplesSerializer(vigencia_contrato)


@pytest.fixture
def contrato_serializer():
    contrato = mommy.make(Contrato)
    return ContratoSerializer(contrato)


@pytest.fixture
def edital_contratos_serializer():
    edital_contratos = mommy.make(Edital)
    return EditalContratosSerializer(edital_contratos)


@pytest.fixture
def edital_serializer():
    edital = mommy.make(Edital)
    return EditalSerializer(edital)


@pytest.fixture
def edital_simples_serializer():
    edital = mommy.make(Edital)
    return EditalSimplesSerializer(edital)


@pytest.fixture
def terceirizada_simples_serializer():
    terceirizada = mommy.make(Terceirizada)
    return TerceirizadaSimplesSerializer(terceirizada)


@pytest.fixture
def modalidade_serializer():
    modalidade = mommy.make(Modalidade)
    return ModalidadeSerializer(modalidade)


@pytest.fixture
def terceirizada():
    return mommy.make(
        Terceirizada,
        contatos=[mommy.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )


@pytest.fixture
def email_terceirizada_por_modulo_serializer(emailterceirizadapormodulo):
    return EmailsTerceirizadaPorModuloSerializer(emailterceirizadapormodulo)


@pytest.fixture
def nutricionista():
    return mommy.make(Nutricionista, nome="nutri")


@pytest.fixture
def perfil_distribuidor():
    return mommy.make(Perfil, nome="ADMINISTRADOR_EMPRESA")


@pytest.fixture
def modalidade():
    return mommy.make(Modalidade, nome="Pregão Eletrônico")


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.user = MagicMock()
    return request


@pytest.fixture
def mock_vinculo_atual():
    vinculo = MagicMock()
    vinculo.perfil.nome = ADMINISTRADOR_EMPRESA
    return vinculo


@pytest.fixture
def mock_form_data():
    return {
        "nome_terceirizada": "",
        "data_inicial": None,
        "data_final": None,
    }


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("Terceirizada A", "CODAE_HOMOLOGADO", 5),
        ("Terceirizada A", "CODAE_QUESTIONADO", 3),
        ("Terceirizada B", "CODAE_PEDIU_ANALISE_RECLAMACAO", 2),
    ]
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    with patch("sme_sigpae_api.terceirizada.utils.connection.cursor") as mock_conn:
        mock_conn.return_value.__enter__.return_value = mock_cursor
        yield mock_conn
