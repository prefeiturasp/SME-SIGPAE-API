import datetime

import pytest
from faker import Faker
from model_mommy import mommy
from rest_framework.test import APIClient

from ...perfil.models import Perfil, Usuario
from ..api.serializers.serializers import (
    ContratoSerializer,
    EditalContratosSerializer,
    EditalSerializer,
    EditalSimplesSerializer,
    TerceirizadaSimplesSerializer,
    VigenciaContratoSerializer
)
from ..models import Contrato, Edital, Nutricionista, Terceirizada, VigenciaContrato

fake = Faker('pt_BR')
fake.seed(420)


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def client_autenticado_terceiro(client_autenticado, ):
    terceirizada = mommy.make(Terceirizada,
                              contatos=[mommy.make('dados_comuns.Contato')],
                              make_m2m=True
                              )

    mommy.make(Nutricionista,
               terceirizada=terceirizada,
               contatos=[mommy.make('dados_comuns.Contato')],
               )
    mommy.make(Contrato, terceirizada=terceirizada, edital=mommy.make(Edital), make_m2m=True)
    return client_autenticado


@pytest.fixture
def usuario_2():
    return mommy.make(
        Usuario,
        uuid='8344f23a-95c4-4871-8f20-3880529767c0',
        nome='Fulano da Silva',
        email='fulano@teste.com',
        cpf='11111111111',
        registro_funcional='1234567'
    )


@pytest.fixture(params=[
    # email, senha, rf, cpf
    ('cogestor_1@sme.prefeitura.sp.gov.br', 'adminadmin', '0000001', '44426575052'),
    ('cogestor_2@sme.prefeitura.sp.gov.br', 'aasdsadsadff', '0000002', '56789925031'),
    ('cogestor_3@sme.prefeitura.sp.gov.br', '98as7d@@#', '0000147', '86880963099'),
    ('cogestor_4@sme.prefeitura.sp.gov.br', '##$$csazd@!', '0000441', '13151715036'),
    ('cogestor_5@sme.prefeitura.sp.gov.br', '!!@##FFG121', '0005551', '40296233013')
])
def users_codae_gestao_alimentacao(client, django_user_model, request, usuario_2):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(password=password, email=email, registro_funcional=rf, cpf=cpf)
    client.login(email=email, password=password)

    codae = mommy.make('Codae', nome='CODAE', uuid='b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd')

    perfil_administrador_codae = mommy.make('Perfil', nome='ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA', ativo=True,
                                            uuid='48330a6f-c444-4462-971e-476452b328b2')
    perfil_coordenador = mommy.make('Perfil', nome='COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA', ativo=True,
                                    uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')
    mommy.make('Perfil', nome='ADMINISTRADOR_TERCEIRIZADA', ativo=True,
               uuid='11c22490-e040-4b4a-903f-54d1b1e57b08')
    mommy.make('Perfil', nome='NUTRI_ADMIN_RESPONSAVEL', ativo=True,
               uuid='564fc542-2260-430e-b29d-ddac1ef81d47')
    mommy.make('Lote', uuid='143c2550-8bf0-46b4-b001-27965cfcd107')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_administrador_codae,
               ativo=False, data_inicial=hoje, data_final=hoje + datetime.timedelta(days=30)
               )  # finalizado
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_coordenador,
               data_inicial=hoje, ativo=True)
    mommy.make('Vinculo', usuario=usuario_2, instituicao=codae, perfil=perfil_administrador_codae,
               data_inicial=hoje, ativo=True)

    return client, email, password, rf, cpf, user


@pytest.fixture
def edital():
    return mommy.make(Edital, numero='1', objeto='lorem ipsum')


@pytest.fixture
def contrato():
    return mommy.make(Contrato, numero='1', processo='12345')


@pytest.fixture
def vigencia_contrato(contrato):
    data_inicial = datetime.date(2019, 1, 1)
    data_final = datetime.date(2019, 1, 31)
    return mommy.make(VigenciaContrato, contrato=contrato, data_inicial=data_inicial, data_final=data_final)


@pytest.fixture
def vigencia_contrato_serializer(vigencia_contrato):
    return VigenciaContratoSerializer(vigencia_contrato)


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
def terceirizada():
    return mommy.make(Terceirizada,
                      contatos=[mommy.make('dados_comuns.Contato')],
                      make_m2m=True,
                      nome_fantasia='Alimentos SA'
                      )


@pytest.fixture
def nutricionista():
    return mommy.make(Nutricionista, nome='nutri')


@pytest.fixture
def perfil_distribuidor():
    return mommy.make(Perfil, nome='ADMINISTRADOR_DISTRIBUIDORA')
