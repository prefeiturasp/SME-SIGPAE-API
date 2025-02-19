import datetime

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from model_mommy import mommy

from ...dados_comuns.constants import (
    ADMINISTRADOR_DICAE,
    DILOG_ABASTECIMENTO,
    DJANGO_ADMIN_PASSWORD,
)
from .. import models
from ..api.serializers import UsuarioSerializer, UsuarioUpdateSerializer

f = Faker(locale="pt-Br")


@pytest.fixture
def perfil():
    return mommy.make(
        models.Perfil,
        nome="título do perfil",
        uuid="d38e10da-c5e3-4dd5-9916-010fc250595a",
    )


@pytest.fixture
def perfil_distribuidor():
    return mommy.make(
        models.Perfil,
        nome="ADMINISTRADOR_EMPRESA",
        uuid="daf2c069-7cd9-4cd4-8fde-624c08f55ae7",
    )


@pytest.fixture
def perfil_escola():
    return mommy.make(
        models.Perfil,
        nome="ADMINISTRADOR_UE",
        uuid="F38e10da-c5e3-4dd5-9916-010fc250595a",
    )


@pytest.fixture
def perfis_vinculados(perfil, perfil_distribuidor, perfil_escola):
    return mommy.make(
        models.PerfisVinculados,
        perfil_master=perfil_distribuidor,
        perfis_subordinados=(perfil_distribuidor, perfil),
    )


@pytest.fixture
def escola(tipo_gestao):
    dre = mommy.make("DiretoriaRegional")
    return mommy.make(
        "Escola",
        diretoria_regional=dre,
        nome="EscolaTeste",
        codigo_eol="400221",
        uuid="230453bb-d6f1-4513-b638-8d6d150d1ac6",
        tipo_gestao=tipo_gestao,
    )


@pytest.fixture
def diretoria_regional():
    return mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL DE EDUCACAO ITAQUERA",
        uuid="7bb20934-e740-4621-a906-bccb8ea98414",
    )


@pytest.fixture
def terceirizada():
    return mommy.make(
        "Terceirizada",
        contatos=[mommy.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
        cnpj="85786774000142",
    )


@pytest.fixture
def codae(escola):
    return mommy.make("Codae", make_m2m=True)


@pytest.fixture
def usuario():
    return mommy.make(
        models.Usuario,
        nome="Fulano da Silva",
        email="fulano@teste.com",
        cpf="52347255100",
        registro_funcional="1234567",
    )


@pytest.fixture
def usuario_2():
    return mommy.make(
        models.Usuario,
        uuid="8344f23a-95c4-4871-8f20-3880529767c0",
        nome="Fulano da Silva",
        email="fulano@teste.com",
        cpf="11111111111",
        registro_funcional="1234567",
    )


@pytest.fixture
def usuario_3():
    user = mommy.make(
        models.Usuario,
        username="7654321",
        uuid="155743d3-b16d-4899-8224-efc694053055",
        nome="Siclano Souza",
        email="siclano@teste.com",
        cpf="22222222222",
        registro_funcional="7654321",
    )
    mommy.make(
        "Vinculo",
        usuario=user,
        perfil=mommy.make("Perfil"),
        ativo=True,
        data_inicial=datetime.date.today(),
        data_final=None,
    )
    return user


@pytest.fixture()
def usuario_com_rf_de_diretor(escola):
    hoje = datetime.date.today()
    perfil_diretor = mommy.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    user = mommy.make(models.Usuario, registro_funcional="6580157")
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        data_final=None,
        ativo=True,
    )  # ativo
    return user


@pytest.fixture
def usuario_serializer(usuario):
    return UsuarioSerializer(usuario)


@pytest.fixture
def vinculo(perfil, usuario):
    hoje = datetime.date.today()
    return mommy.make(
        "Vinculo",
        perfil=perfil,
        usuario=usuario,
        data_inicial=hoje,
        data_final=None,
        ativo=True,
    )


@pytest.fixture
def vinculo_aguardando_ativacao(perfil, usuario):
    return mommy.make(
        "Vinculo",
        perfil=perfil,
        usuario=usuario,
        data_inicial=None,
        data_final=None,
        ativo=False,
    )


@pytest.fixture(
    params=[
        # dataini, datafim, ativo
        (
            datetime.date(2000, 1, 12),
            datetime.date(2000, 1, 12),
            True,
        ),  # nao pode data final e ativo
        # nao pode data final sem data inicial
        (None, datetime.date(2000, 1, 12), True),
        # nao pode data final sem data inicial,
        (None, datetime.date(2000, 1, 12), False),
        # nao pode data inicio, sem data fim e inativo
        (datetime.date(2000, 1, 12), None, False),
    ]
)
def vinculo_invalido(perfil, usuario, request):
    dataini, datafim, ativo = request.param
    return mommy.make(
        "Vinculo",
        perfil=perfil,
        usuario=usuario,
        data_inicial=dataini,
        data_final=datafim,
        ativo=ativo,
    )


@pytest.fixture
def vinculo_diretoria_regional(usuario):
    return mommy.make(
        "Vinculo",
        data_inicial=datetime.date.today(),
        ativo=True,
        usuario=usuario,
        content_type=models.ContentType.objects.get(model="diretoriaregional"),
    )


@pytest.fixture
def usuario_update_serializer(usuario_2):
    return UsuarioUpdateSerializer(usuario_2)


@pytest.fixture
def tipo_gestao():
    return mommy.make("TipoGestao", nome="TERC TOTAL")


@pytest.fixture(
    params=[
        ("admin_1@sme.prefeitura.sp.gov.br", "adminadmin", "0000002"),
        ("admin_2@sme.prefeitura.sp.gov.br", "xxASD123@@", "0000013"),
        ("admin_3@sme.prefeitura.sp.gov.br", "....!!!123213#$", "0044002"),
        ("admin_4@sme.prefeitura.sp.gov.br", "XXXDDxx@@@77", "0000552"),
    ]
)
def users_admin_escola(client, django_user_model, request, tipo_gestao):
    email, password, rf = request.param
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
        codigo_eol=987656,
    )
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    tipo_unidade_escolar = mommy.make(
        "escola.TipoUnidadeEscolar",
        iniciais=f.name()[:10],
        cardapios=[cardapio1, cardapio2],
        uuid="56725de5-89d3-4edf-8633-3e0b5c99e9d4",
    )
    escola = mommy.make(
        "Escola",
        nome="EMEI NOE AZEVEDO, PROF",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        diretoria_regional=diretoria_regional,
        codigo_eol="256341",
        tipo_unidade=tipo_unidade_escolar,
        tipo_gestao=tipo_gestao,
    )
    periodo_escolar_tarde = mommy.make(
        "PeriodoEscolar", nome="TARDE", uuid="57af972c-938f-4f6f-9f4b-cf7b983a10b7"
    )
    periodo_escolar_manha = mommy.make(
        "PeriodoEscolar", nome="MANHA", uuid="d0c12dae-a215-41f6-af86-b7cd1838ba81"
    )
    mommy.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=230,
        periodo_escolar=periodo_escolar_tarde,
    )
    mommy.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=220,
        periodo_escolar=periodo_escolar_manha,
    )
    perfil_professor = mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=False)
    perfil_admin = mommy.make(
        "Perfil", nome="Admin", ativo=True, uuid="d6fd15cc-52c6-4db4-b604-018d22eeb3dd"
    )
    hoje = datetime.date.today()

    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial=hoje,
        data_final=hoje + datetime.timedelta(days=30),
        ativo=False,
    )  # finalizado
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_admin,
        data_inicial=hoje,
        ativo=True,
    )  # ativo

    return client, email, password, rf, user


@pytest.fixture(
    params=[
        # email, senha, rf, cpf
        ("diretor_1@sme.prefeitura.sp.gov.br", "adminadmin", "0000001", "44426575052"),
        (
            "diretor_2@sme.prefeitura.sp.gov.br",
            "aasdsadsadff",
            "0000002",
            "56789925031",
        ),
        ("diretor_3@sme.prefeitura.sp.gov.br", "98as7d@@#", "0000147", "86880963099"),
        ("diretor_4@sme.prefeitura.sp.gov.br", "##$$csazd@!", "0000441", "13151715036"),
        ("diretor_5@sme.prefeitura.sp.gov.br", "!!@##FFG121", "0005551", "40296233013"),
    ]
)
def users_diretor_escola(client, django_user_model, request, usuario_2, tipo_gestao):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)

    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        iniciais="IP",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
        codigo_eol=987656,
    )
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    tipo_unidade_escolar = mommy.make(
        "escola.TipoUnidadeEscolar",
        iniciais="EMEF",
        cardapios=[cardapio1, cardapio2],
        uuid="56725de5-89d3-4edf-8633-3e0b5c99e9d4",
    )
    escola = mommy.make(
        "Escola",
        nome="EMEI NOE AZEVEDO, PROF",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        diretoria_regional=diretoria_regional,
        codigo_eol="256341",
        tipo_unidade=tipo_unidade_escolar,
        tipo_gestao=tipo_gestao,
    )
    periodo_escolar_tarde = mommy.make(
        "PeriodoEscolar", nome="TARDE", uuid="57af972c-938f-4f6f-9f4b-cf7b983a10b7"
    )
    periodo_escolar_manha = mommy.make(
        "PeriodoEscolar", nome="MANHA", uuid="d0c12dae-a215-41f6-af86-b7cd1838ba81"
    )
    mommy.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=230,
        periodo_escolar=periodo_escolar_tarde,
    )
    mommy.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola,
        quantidade_alunos=220,
        periodo_escolar=periodo_escolar_manha,
    )
    perfil_professor = mommy.make(
        "Perfil",
        nome="ADMINISTRADOR_UE",
        ativo=False,
        uuid="48330a6f-c444-4462-971e-476452b328b2",
    )
    perfil_diretor = mommy.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        ativo=False,
        data_inicial=hoje,
        data_final=hoje + datetime.timedelta(days=30),
    )  # finalizado
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        "Vinculo",
        usuario=usuario_2,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial=hoje,
        ativo=True,
    )
    return client, email, password, rf, cpf, user


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
def users_cogestor_diretoria_regional(client, django_user_model, request, usuario_2):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)

    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL DE EDUCACAO CAPELA DO SOCORRO",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        codigo_eol="0002",
    )

    perfil_cogestor = mommy.make(
        "Perfil",
        nome="COGESTOR_DRE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        "Vinculo",
        usuario=usuario_2,
        instituicao=diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )

    return client, email, password, rf, cpf, user


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
    hoje = datetime.date.today()
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
def users_terceirizada(client, django_user_model, request, usuario_2):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=rf, password=password)
    mommy.make("Codae")
    terceirizada = mommy.make(
        "Terceirizada",
        nome_fantasia="Alimentos LTDA",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
    )

    perfil_nutri_admin_responsavel = mommy.make(
        "Perfil",
        nome="ADMINISTRADOR_EMPRESA",
        ativo=True,
        uuid="48330a6f-c444-4462-971e-476452b328b2",
    )
    perfil_administrador_terceirizada = mommy.make(
        "Perfil",
        nome="USUARIO_EMPRESA",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=terceirizada,
        perfil=perfil_administrador_terceirizada,
        ativo=False,
        data_inicial=hoje,
        data_final=hoje + datetime.timedelta(days=30),
    )  # finalizado
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=terceirizada,
        perfil=perfil_nutri_admin_responsavel,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        "Vinculo",
        usuario=usuario_2,
        instituicao=terceirizada,
        perfil=perfil_administrador_terceirizada,
        data_inicial=hoje,
        ativo=True,
    )

    return client, email, password, rf, cpf, user


def mocked_request_api_eol():
    return {
        "rf": "5858585",
        "cpf": "34811126025",
        "email": "fulana.silva@sme.prefeitura.sp.gov.br",
        "cargos": [
            {
                "codigoCargo": 3085,
                "descricaoCargo": "ASSISTENTE DE DIRETOR DE ESCOLA         ",
                "codigoUnidade": "019532",
                "descricaoUnidade": "CEMEI - IRAPARA",
                "codigoDre": "108100",
                "contratoExterno": False,
            }
        ],
        "nome": "FULANA DA SILVA",
        "inexistenteEol": False,
    }


def mocked_request_api_eol_usuario_diretoria_regional():
    return {
        "rf": "9090909",
        "cpf": "22406543099",
        "email": "beltrana.souza@sme.prefeitura.sp.gov.br",
        "cargos": [
            {
                "codigoCargo": 4502,
                "descricaoCargo": "AUXILIAR ADM. DE ENSINO                 ",
                "codigoUnidade": "109101",
                "descricaoUnidade": "ASSISTENCIA ADMINISTRATIVA-CE SA",
                "codigoDre": "109100",
                "contratoExterno": False,
            }
        ],
        "nome": "BELTRANA DE SOUZA",
        "inexistenteEol": False,
    }


@pytest.fixture(
    params=[
        # nome, uuid
        (f.name(), f.uuid4()),
        (f.name(), f.uuid4()),
        (f.name(), f.uuid4()),
        (f.name(), f.uuid4()),
        (f.name(), f.uuid4()),
    ]
)
def usuarios_pendentes_confirmacao(request, perfil, tipo_gestao):
    nome = "Bruno da Conceição"
    uuid = "d36fa08e-e91e-4acb-9d54-b88115147e8e"
    usuario = mommy.make(
        "Usuario",
        nome=nome,
        uuid=uuid,
        username="1234567",
        is_active=False,
        registro_funcional="1234567",
        email="GrVdXIhxqb@example.com",
    )
    hoje = datetime.date.today()

    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        iniciais="IP",
        uuid="7da9acec-48e1-430c-8a5c-1f1efc666fad",
        codigo_eol=987656,
    )
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    tipo_unidade_escolar = mommy.make(
        "escola.TipoUnidadeEscolar",
        iniciais="EMEF",
        cardapios=[cardapio1, cardapio2],
        uuid="56725de5-89d3-4edf-8633-3e0b5c99e9d4",
    )
    escola = mommy.make(
        "Escola",
        nome="EMEI NOE AZEVEDO, PROF",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        diretoria_regional=diretoria_regional,
        codigo_eol="256341",
        tipo_unidade=tipo_unidade_escolar,
        tipo_gestao=tipo_gestao,
    )

    mommy.make(
        "Vinculo",
        perfil=perfil,
        usuario=usuario,
        data_inicial=None,
        data_final=None,
        ativo=False,
        instituicao=escola,
    )  # vinculo esperando ativacao

    mommy.make(
        "Vinculo",
        perfil=perfil,
        usuario=usuario,
        data_inicial=hoje,
        data_final=hoje + datetime.timedelta(days=100),
        ativo=False,
        instituicao=escola,
    )  # vinculo finalizado

    return usuario


@pytest.fixture(
    params=[
        # email, esprado
        (
            "tebohelleb-2297@sme.prefeitura.sp.gov.br",
            "t*************7@sme.prefeitura.sp.gov.br",
        ),
        (
            "surracecyss-9018@sme.prefeitura.sp.gov.br",
            "s**************8@sme.prefeitura.sp.gov.br",
        ),
        (
            "zoffexupi-7784@sme.prefeitura.sp.gov.br",
            "z************4@sme.prefeitura.sp.gov.br",
        ),
        ("fulano157@sme.prefeitura.sp.gov.br", "f*******7@sme.prefeitura.sp.gov.br"),
        (
            "tebohelleb-2297@prefeitura.sp.gov.br",
            "t*************7@prefeitura.sp.gov.br",
        ),
        (
            "surracecyss-9018@prefeitura.sp.gov.br",
            "s**************8@prefeitura.sp.gov.br",
        ),
        ("zoffexupi-7784@prefeitura.sp.gov.br", "z************4@prefeitura.sp.gov.br"),
        ("fulano157@prefeitura.sp.gov.br", "f*******7@prefeitura.sp.gov.br"),
    ]
)
def email_list(request):
    return request.param


@pytest.fixture(
    params=[
        # email, esprado
        (
            "tebohelleb-2297@smea.prefeitura.sp.gov.br",
            "t*************7@sme.prefeitura.sp.gov.br",
        ),
        (
            "surracecyss-9018@smes.prefeitura.sp.gov.br",
            "s**************8@sme.prefeitura.sp.gov.br",
        ),
        (
            "zoffexupi-7784@smed.prefeitura.sp.gov.br",
            "z************4@sme.prefeitura.sp.gov.br",
        ),
        ("fulano157@smea.prefeitura.sp.gov.br", "f*******7@sme.prefeitura.sp.gov.br"),
        (
            "tebohelleb-2297@prefeituraa.sp.gov.br",
            "t*************7@prefeiturab.sp.gov.br",
        ),
        (
            "surracecyss-9018@prefeiturab.sp.gov.br",
            "s**************8@prefeiturac.sp.gov.br",
        ),
        (
            "zoffexupi-7784@prefeiturac.sp.gov.br",
            "z************4@prefeiturad.sp.gov.br",
        ),
        ("fulano157@prefeiturad.sp.gov.br", "f*******7@prefeiturae.sp.gov.br"),
    ]
)
def email_list_invalidos(request):
    return request.param


@pytest.fixture
def fake_user(client):
    email = "admin@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    user = models.Usuario.objects.create_user(
        email=email,
        password=password,
        nome="admin",
        cpf="0",
        registro_funcional="1234",
    )
    return user, password


@pytest.fixture
def usuario_autenticado(client):
    email = "admin@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    client.login(username=email, password=password)
    return client


@pytest.fixture
def authenticated_client(client, fake_user):
    user, password = fake_user
    client.login(username=user.email, password=password)
    return client


@pytest.fixture
def arquivo_pdf():
    type_pdf = "application/pdf"
    return SimpleUploadedFile(
        "arquivo-teste.pdf", str.encode("file_content"), content_type=type_pdf
    )


@pytest.fixture
def arquivo_xls():
    return SimpleUploadedFile(
        "arquivo.xls", bytes("Código eol,\n93238,", encoding="utf-8")
    )


@pytest.fixture
def planilha_usuario_externo(arquivo_xls):
    return mommy.make("ImportacaoPlanilhaUsuarioExternoCoreSSO", conteudo=arquivo_xls)


@pytest.fixture
def planilha_usuario_servidor(arquivo_xls):
    return mommy.make("ImportacaoPlanilhaUsuarioServidorCoreSSO", conteudo=arquivo_xls)


@pytest.fixture
def escola_cei():
    return mommy.make(
        "Escola", nome="CEI DIRET - JOSE DE MOURA, VER.", codigo_eol="400158"
    )


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model, escola, escola_cei):
    email = "user@escola.com"
    rf = "1234567"
    password = DJANGO_ADMIN_PASSWORD
    mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        nome="RONALDO DIRETOR",
        username=rf,
        password=password,
        email=email,
        registro_funcional=rf,
        cpf="93697506064",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_email_invalido(
    client, django_user_model, escola, escola_cei
):
    email = "invalido"
    rf = "1234567"
    password = DJANGO_ADMIN_PASSWORD
    mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        nome="RONALDO DIRETOR",
        username=rf,
        password=password,
        email=email,
        registro_funcional=rf,
        cpf="93697506064",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_sem_vinculo(
    client, django_user_model, escola, escola_cei
):
    email = "user@escola.com"
    rf = "1234567"
    password = DJANGO_ADMIN_PASSWORD
    mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    django_user_model.objects.create_user(
        nome="RONALDO DIRETOR",
        username=rf,
        password=password,
        email=email,
        registro_funcional=rf,
        cpf="93697506064",
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola_adm(client, django_user_model, escola, escola_cei):
    email = "user@escola.com"
    rf = "1234567"
    password = DJANGO_ADMIN_PASSWORD
    mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    perfil_adm = mommy.make("Perfil", nome="ADMINISTRADOR_UE", ativo=True)
    usuario = django_user_model.objects.create_user(
        nome="RONALDO DIRETOR",
        username=rf,
        password=password,
        email=email,
        registro_funcional=rf,
        cpf="93697506064",
    )
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil_adm,
        data_inicial=ontem,
        ativo=True,
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_da_dre(client, django_user_model, escola, escola_cei):
    email = "user@escola.com"
    rf = "1234567"
    password = DJANGO_ADMIN_PASSWORD
    perfil_dre = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        nome="RONALDO COGESTOR",
        username=rf,
        password=password,
        email=email,
        registro_funcional=rf,
        cpf="93697506064",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola.diretoria_regional,
        perfil=perfil_dre,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def setup_usuarios_command():
    usuario1 = mommy.make(
        "Usuario",
        uuid="a9469d8f-6578-4ebb-8b90-6a98fa97c188",
        email="usuario1@test.com",
        registro_funcional="1234567",
        username="usuario1",
        cpf="12345678901",
        is_active=True,
    )
    usuario2 = mommy.make(
        "Usuario",
        uuid="32d150bc-6241-4967-a21b-2f219b2d5317",
        email="usuario2@test.com",
        registro_funcional="754321",
        username="usuario2",
        cpf="98765432109",
        is_active=True,
    )
    usuario3 = mommy.make(
        "Usuario",
        uuid="cd0bc9f3-17f8-4fe6-9dac-38dd108d6223",
        email="usuario3@admin.com",
        registro_funcional="1726354",
        username="usuario3",
        cpf=None,
        is_active=True,
    )
    usuario4 = mommy.make(
        "Usuario",
        uuid="79cc6d39-5d2b-4ed8-8b02-25558db82952",
        email="usuario4@test.com",
        registro_funcional=None,
        username="usuario4",
        cpf="11122233344",
        is_active=False,
    )
    return usuario1, usuario2, usuario3, usuario4


@pytest.fixture
def setup_vinculos_e_usuarios(setup_usuarios_command):
    terceirizada_ct, created = ContentType.objects.get_or_create(
        app_label="terceirizada", model="terceirizada"
    )
    mommy.make(
        "Vinculo",
        usuario=setup_usuarios_command[0],
        ativo=True,
        content_type=terceirizada_ct,
    )
    mommy.make(
        "Vinculo",
        usuario=setup_usuarios_command[1],
        ativo=True,
        content_type=terceirizada_ct,
    )
    mommy.make(
        "Vinculo",
        usuario=setup_usuarios_command[2],
        ativo=True,
        content_type=terceirizada_ct,
    )  # Sem CPF
    mommy.make(
        "Vinculo",
        usuario=setup_usuarios_command[3],
        ativo=True,
        content_type=terceirizada_ct,
    )  # Usuário inativo


@pytest.fixture
def setup_vinculos_e_perfis(django_db_setup, django_db_blocker):
    mommy.make("Perfil", nome="DIRETOR")
    mommy.make("Perfil", nome="ADMINISTRADOR_EMPRESA")
    mommy.make("Perfil", nome="ADMINISTRADOR_TERCEIRIZADA")
    mommy.make("Perfil", nome="ADMINISTRADOR_UE")
    mommy.make("Perfil", nome="USUARIO_EMPRESA")

    mommy.make("Vinculo", perfil__nome="DIRETOR", ativo=True)
    mommy.make("Vinculo", perfil__nome="ADMINISTRADOR_TERCEIRIZADA", ativo=True)
    mommy.make("Vinculo", perfil__nome="NUTRI_ADMIN_RESPONSAVEL", ativo=True)
    mommy.make("Vinculo", perfil__nome="ADMINISTRADOR_DISTRIBUIDORA", ativo=True)
    mommy.make("Vinculo", perfil__nome="ADMINISTRADOR_FORNECEDOR", ativo=True)


@pytest.fixture
def setup_normaliza_vinculos(django_db_setup, django_db_blocker):
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        ativo=True,
        data_inicial=hoje - datetime.timedelta(days=10),
        data_final=hoje - datetime.timedelta(days=5),
        _quantity=3,
    )
    mommy.make(
        "Vinculo",
        ativo=True,
        data_inicial=None,
        data_final=None,
        _quantity=3,
    )
    mommy.make(
        "Vinculo",
        ativo=False,
        data_inicial=hoje - datetime.timedelta(days=5),
        data_final=None,
        _quantity=3,
    )
    mommy.make(
        "Vinculo",
        ativo=False,
        data_inicial=None,
        data_final=hoje - datetime.timedelta(days=2),
        _quantity=3,
    )


@pytest.fixture
def setup_unificar_perfis():
    suplente = mommy.make("Perfil", nome="SUPLENTE")
    administrador_dre = mommy.make("Perfil", nome="ADMINISTRADOR_DRE")
    cogestor = mommy.make("Perfil", nome="COGESTOR")
    cogestor_dre = mommy.make("Perfil", nome="COGESTOR_DRE")

    mommy.make("Vinculo", perfil=suplente, _quantity=2)
    mommy.make("Vinculo", perfil=administrador_dre, _quantity=2)
    mommy.make("Vinculo", perfil=cogestor, _quantity=2)

    perfil_nao_alterado = mommy.make("Perfil", nome="NAO_ALTERADO")
    mommy.make("Vinculo", perfil=perfil_nao_alterado, _quantity=2)


def mocked_response_autentica_coresso_adm_ue():
    return {
        "nome": "RONALDO DIRETOR",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "login": "1234567",
        "visoes": ["ADMINISTRADOR_UE"],
        "perfis_por_sistema": [{"sistema": 1004, "perfis": ["ADMINISTRADOR_UE"]}],
    }


def mocked_response_autentica_coresso_diretor():
    return {
        "nome": "RONALDO DIRETOR",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "login": "1234567",
        "visoes": ["DIRETOR_UE"],
        "perfis_por_sistema": [{"sistema": 1004, "perfis": ["DIRETOR_UE"]}],
    }


def mocked_response_autentica_coresso_cogestor():
    return {
        "nome": "RONALDO COGESTOR",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "login": "1234567",
        "visoes": ["COGESTOR_DRE"],
        "perfis_por_sistema": [{"sistema": 1004, "perfis": ["COGESTOR_DRE"]}],
    }


def mocked_response_autentica_coresso_diretor_login_errado():
    return {
        "nome": "RONALDO DIRETOR",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "login": "1234568",
        "visoes": ["DIRETOR_UE"],
        "perfis_por_sistema": [{"sistema": 1004, "perfis": ["DIRETOR_UE"]}],
    }


def mocked_response_get_dados_usuario_coresso():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 3360,
                "descricaoCargo": "DIRETOR DE ESCOLA                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


def mocked_response_get_dados_usuario_coresso_coordenador():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 43,
                "descricaoCargo": "COORDENADOR GERAL                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


def mocked_response_get_dados_usuario_coresso_gestor():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 515,
                "descricaoCargo": "GESTOR DE EQUIPAMENTO PÚBLICO II                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


def mocked_response_get_dados_usuario_coresso_sem_email():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": None,
        "cargos": [
            {
                "codigoCargo": 3360,
                "descricaoCargo": "DIRETOR DE ESCOLA                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


def mocked_response_get_dados_usuario_coresso_cogestor():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 2,
                "descricaoCargo": "COGESTOR                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO COGESTOR",
    }


def mocked_response_get_dados_usuario_coresso_adm_escola():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 3379,
                "descricaoCargo": "COORDENADOR PEDAGÓGICO                       ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


def mocked_response_get_dados_usuario_coresso_sem_acesso_automatico():
    return {
        "rf": "1234567",
        "cpf": "93697506064",
        "email": "user@escola.com",
        "cargos": [
            {
                "codigoCargo": 1,
                "descricaoCargo": "ATE                      ",
                "codigoUnidade": "400158",
                "descricaoUnidade": "CEI DIRET - JOSE DE MOURA, VER.",
                "codigoDre": "108600",
            }
        ],
        "nome": "RONALDO DIRETOR",
    }


@pytest.fixture
def usuario_administrador_dicae():
    usuario = mommy.make("Usuario", username="testuser")
    mommy.make("Cargo", usuario=usuario, ativo=False, nome="Gerente")
    mommy.make("Cargo", usuario=usuario, ativo=True, nome="Analista")
    codae = mommy.make("Codae", nome="Codae - Administrador Contratos")
    mommy.make(
        "Vinculo",
        usuario=usuario,
        perfil=mommy.make("Perfil", nome=ADMINISTRADOR_DICAE),
        ativo=True,
        data_inicial=datetime.date.today(),
        data_final=None,
        content_type=models.ContentType.objects.get(model="codae"),
        object_id=codae.pk,
    )

    return usuario


@pytest.fixture
def usuario_dilog_abastecimento(django_user_model):
    usuario = mommy.make("Usuario", username="testuser")
    mommy.make("Cargo", usuario=usuario, ativo=False, nome="Diretor")
    mommy.make("Cargo", usuario=usuario, ativo=True, nome="Coordenador")
    codae = mommy.make("Codae", nome="Codae - Dilog")
    mommy.make(
        "Vinculo",
        usuario=usuario,
        perfil=mommy.make("Perfil", nome=DILOG_ABASTECIMENTO),
        ativo=True,
        data_inicial=datetime.date.today(),
        data_final=None,
        content_type=models.ContentType.objects.get(model="codae"),
        object_id=codae.pk,
    )

    return usuario
