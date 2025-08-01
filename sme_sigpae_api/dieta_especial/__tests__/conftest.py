import datetime
import json
import random
from random import randint, sample

import pytest
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.dieta_especial.api.serializers import UnidadeEducacionalSerializer

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.models import TemplateMensagem
from ...dados_comuns.utils import convert_base64_to_contentfile
from ...escola.models import Aluno, FaixaEtaria, PeriodoEscolar
from ...perfil.models import Usuario
from ...produto.models import Produto
from ...terceirizada.models import Edital
from ..models import (
    AlergiaIntolerancia,
    Alimento,
    Anexo,
    ClassificacaoDieta,
    MotivoNegacao,
    SolicitacaoDietaEspecial,
)

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def usuario_admin():
    return baker.make("Usuario", email="admin@admin.com", is_superuser=True)


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def dre_guaianases():
    return baker.make("DiretoriaRegional", nome="DIRETORIA REGIONAL GUAIANASES")


@pytest.fixture
def escola_dre_guaianases(dre_guaianases):
    lote = baker.make("Lote")
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    return baker.make(
        "Escola",
        lote=lote,
        diretoria_regional=dre_guaianases,
        tipo_gestao=tipo_gestao,
        nome="Escola Guaianases",
    )


@pytest.fixture
def arquivo_docx_base64():
    return "data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,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"  # noqa


@pytest.fixture
def aluno():
    return baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
    )


@pytest.fixture
def solicitacao_dieta_especial(escola, aluno):
    return baker.make(SolicitacaoDietaEspecial, rastro_escola=escola, aluno=aluno)


@pytest.fixture
def solicitacao_dieta_especial_parceira(escola_parceira, aluno):
    return baker.make(
        SolicitacaoDietaEspecial, rastro_escola=escola_parceira, aluno=aluno
    )


@pytest.fixture
def solicitacao_dieta_especial_outra_dre(escola_dre_guaianases, aluno):
    return baker.make(
        SolicitacaoDietaEspecial, rastro_escola=escola_dre_guaianases, aluno=aluno
    )


@pytest.fixture
def anexo_docx(arquivo_docx_base64, solicitacao_dieta_especial):
    return baker.make(
        Anexo,
        solicitacao_dieta_especial=solicitacao_dieta_especial,
        arquivo=convert_base64_to_contentfile(arquivo_docx_base64),
        nome="arquivo-supimpa.docx",
    )


@pytest.fixture(
    scope="function",
    params=[
        "teste.jpg",
        "borboleta.png",
        "arquivo_bacana.pdf",
        "arquivo_top.docx",
        "arquivo_legal.doc",
    ],
)
def nomes_arquivos_validos(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        "teste.zip",
        "borboleta.py",
        "arquivo_bacana.js",
        "arquivo_top.tar.gz",
        "arquivo_legal.exe",
    ],
)
def nomes_arquivos_invalidos(request):
    return request.param


@pytest.fixture
def alergias_intolerancias():
    baker.make(AlergiaIntolerancia, _quantity=2)
    return AlergiaIntolerancia.objects.all()


@pytest.fixture
def classificacoes_dieta():
    baker.make(ClassificacaoDieta, _quantity=3)
    return ClassificacaoDieta.objects.all()


@pytest.fixture
def motivos_negacao():
    baker.make(MotivoNegacao, _quantity=4)
    return MotivoNegacao.objects.all()


@pytest.fixture
def alimentos():
    baker.make(Alimento, _quantity=6)
    return Alimento.objects.all()


@pytest.fixture
def produtos():
    baker.make(Produto, _quantity=6)
    return Produto.objects.all()


@pytest.fixture
def substituicoes(alimentos, produtos):
    substituicoes = []
    ids_produtos = [p.uuid for p in produtos]
    for _ in range(randint(3, 5)):
        substituicoes.append(
            {
                "alimento": alimentos[randint(0, len(alimentos) - 1)].id,
                "tipo": "I" if randint(0, 1) == 1 else "S",
                "substitutos": sample(ids_produtos, randint(1, 4)),
            }
        )
    return substituicoes


@pytest.fixture
def edital():
    return baker.make(
        "Edital", uuid="b7b6a0a7-b230-4783-94b6-8d3d22041ab3", numero="edital-teste-1"
    )


@pytest.fixture
def edital_parceira():
    return baker.make("Edital", numero="PARCEIRA")


@pytest.fixture
def payload_autorizar(
    alergias_intolerancias,
    classificacoes_dieta,
    substituicoes,
    protocolo_padrao_dieta_especial,
):
    return {
        "classificacao": classificacoes_dieta[0].id,
        "alergias_intolerancias": [alergias_intolerancias[0].id],
        "registro_funcional_nutricionista": "ELABORADO por USUARIO NUTRICIONISTA CODAE - CRN null",
        "substituicoes": substituicoes,
        "informacoes_adicionais": "Um texto bem grandão",
        "protocolo_padrao": protocolo_padrao_dieta_especial.uuid,
        "nome_protocolo": protocolo_padrao_dieta_especial.nome_protocolo,
        "orientacoes_gerais": "Um texto grande aqui",
    }


@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(
    client, escola, template_mensagem_dieta_especial
):
    email = "escola@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "1545933"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    baker.make(AlergiaIntolerancia, id=random.randint(1, 100000))
    perfil_professor = baker.make("perfil.Perfil", nome="ADMINISTRADOR_UE", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial=datetime.date.today(),
        ativo=True,
    )  # ativo

    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
    )
    solic = baker.make(
        SolicitacaoDietaEspecial,
        rastro_escola=escola,
        escola_destino=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        aluno=aluno,
        criado_por=user,
    )
    solic.inicia_fluxo(user=user)

    return solic


@pytest.fixture
def solicitacao_dieta_especial_autorizada(
    client, escola, solicitacao_dieta_especial_a_autorizar
):
    email = "terceirizada@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "4545454"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_aprovada_alteracao_ue(
    client, escola, motivo_alteracao_ue
):
    aluno = baker.make(
        Aluno,
        nome="Isabella Pereira da Silva",
        codigo_eol="488226",
        data_nascimento="2000-01-01",
    )
    email = "test3@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "374867"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="DIRETOR_UE", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    solicitacao_alterada = baker.make(
        "SolicitacaoDietaEspecial",
        criado_por=user,
        rastro_escola=escola,
        escola_destino=escola,
        aluno=aluno,
        data_inicio=datetime.date.today(),
        data_termino=datetime.date.today(),
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
    )
    solicitacao = baker.make(
        "SolicitacaoDietaEspecial",
        criado_por=user,
        rastro_escola=escola,
        escola_destino=escola,
        aluno=aluno,
        data_inicio=datetime.date.today(),
        data_termino=datetime.date.today(),
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        motivo_alteracao_ue=motivo_alteracao_ue,
        tipo_solicitacao="ALTERACAO_UE",
        dieta_alterada=solicitacao_alterada,
    )
    return solicitacao


@pytest.fixture
def motivo_alteracao_ue():
    return baker.make(
        "MotivoAlteracaoUE",
        uuid="26e7367e-2ef8-49c4-ab2a-9aa9f68475cb",
        nome="Dieta Especial - Recreio nas Férias",
        descricao="",
    )


@pytest.fixture
def solicitacao_dieta_especial_escola_solicitou_inativacao(
    client, escola, solicitacao_dieta_especial_autorizada
):
    email = "terceirizada2@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "4545455"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_autorizada.inicia_fluxo_inativacao(user=user)

    return solicitacao_dieta_especial_autorizada


@pytest.fixture
def solicitacao_dieta_especial_codae_autorizou_inativacao(
    client, escola, solicitacao_dieta_especial_escola_solicitou_inativacao
):
    email = "terceirizada3@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "4545456"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_escola_solicitou_inativacao.codae_autoriza_inativacao(
        user=user
    )

    return solicitacao_dieta_especial_escola_solicitou_inativacao


@pytest.fixture
def template_mensagem_dieta_especial():
    return baker.make(
        TemplateMensagem,
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        assunto="TESTE DIETA ESPECIAL",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def escola():
    terceirizada = baker.make(
        "Terceirizada", uuid="a8fefdd3-b5ff-47e0-8338-ce5d7c6d8a52"
    )
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    lote = baker.make(
        "Lote",
        terceirizada=terceirizada,
        nome="LOTE 07",
        uuid="429446c2-5b17-4ada-96ae-cce369dd4ae1",
        diretoria_regional=diretoria_regional,
    )
    tipo_gestao = baker.make(
        "TipoGestao", nome="TERC TOTAL", uuid="8bd3931b-8636-44ba-9d8e-81b29067eed1"
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
    )
    return escola


@pytest.fixture
def escola_parceira():
    tipo_gestao = baker.make("TipoGestao", nome="PARCEIRA")
    escola = baker.make(
        "Escola",
        nome="PARCEIRA",
        tipo_gestao=tipo_gestao,
    )
    return escola


@pytest.fixture
def escola_cemei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL CEMEI"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="CEMEI")
    escola_cemei = baker.make(
        "Escola",
        nome="CEMEI",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    return escola_cemei


@pytest.fixture
def escola_emebs():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL EMEBS"
    )
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais="EMEBS")
    escola_emebs = baker.make(
        "Escola",
        nome="EMEBS",
        lote=lote,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_escolar,
    )
    return escola_emebs


@pytest.fixture
def massa_dados_protocolo_padrao_test(solicitacao_dieta_especial):
    lote = solicitacao_dieta_especial.escola.lote
    edital_1 = Edital.objects.get(uuid="b7b6a0a7-b230-4783-94b6-8d3d22041ab3")
    edital_2 = Edital.objects.get(uuid="60f5a64e-8652-422d-a6e9-0a36717829c9")
    contrato_1 = baker.make("Contrato", lotes=[lote], edital=edital_1)
    contrato_2 = baker.make("Contrato", lotes=[lote], edital=edital_2)
    return {
        "editais": [edital_1.uuid, edital_2.uuid],
        "dieta_uuid": solicitacao_dieta_especial.uuid,
        "contratos": [contrato_1, contrato_2],
    }


@pytest.fixture
def client_autenticado_vinculo_escola_dieta(
    client, django_user_model, escola, template_mensagem_dieta_especial
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_vinculo_codae_dieta(
    client, django_user_model, escola, codae, template_mensagem_dieta_especial
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_dieta_especial = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_DIETA_ESPECIAL, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_dieta_especial,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_gestao_alimentacao_dieta(
    client, django_user_model, escola, codae, template_mensagem_dieta_especial
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
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
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def client_autenticado_vinculo_terceirizada_dieta(
    client, django_user_model, escola, codae, template_mensagem_dieta_especial
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_nutri_admin = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil_nutri_admin,
        data_inicial=hoje,
        ativo=True,
    )
    classificacao = baker.make(
        "ClassificacaoDieta", id=random.randint(1, 100000), nome="Tipo A"
    )
    protocolo_padrao = baker.make(
        "ProtocoloPadraoDietaEspecial",
        nome_protocolo="ALERGIA - OVO",
        uuid="5d7f80b8-7b62-441b-89da-4d5dd5c1e7e8",
    )
    baker.make(
        "SolicitacaoDietaEspecial",
        status="CODAE_AUTORIZADO",
        escola_destino=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        rastro_escola=escola,
        classificacao=classificacao,
        protocolo_padrao=protocolo_padrao,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas(escola, aluno):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)

    return [
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
            aluno=aluno,
            rastro_escola=escola,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO,
            rastro_escola=escola,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
            aluno=aluno,
            rastro_escola=escola,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
            rastro_escola=escola,
            aluno=aluno,
            data_termino=ontem,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            rastro_escola=escola,
            aluno=aluno,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
            rastro_escola=escola,
            aluno=aluno,
            data_termino=ontem,
        ),
    ]


@pytest.fixture(
    params=[
        DietaEspecialWorkflow.CODAE_AUTORIZADO,
        DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        DietaEspecialWorkflow.CODAE_NEGOU_INATIVACAO,
    ]
)
def solicitacao_dieta_especial_autorizada_ativa(request, aluno, escola):
    return baker.make(
        SolicitacaoDietaEspecial,
        status=request.param,
        rastro_escola=escola,
        aluno=aluno,
    )


@pytest.fixture
def solicitacao_dieta_especial_cancelada_automaticamente(client, escola):
    aluno = baker.make(
        Aluno,
        nome="Isabella Pereira da Silva",
        codigo_eol="488226",
        data_nascimento="2000-01-01",
    )
    email = "test3@admin.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    rf = "374867"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = baker.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    baker.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    solicitacao = baker.make(
        SolicitacaoDietaEspecial,
        rastro_escola=escola,
        escola_destino=escola,
        aluno=aluno,
        data_termino=datetime.date.today() - datetime.timedelta(days=1),
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
    )

    solicitacao.termina(user)
    return solicitacao


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior(aluno, escola):
    hoje = datetime.date.today()
    amanha = hoje + datetime.timedelta(days=1)
    return [
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=hoje,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=hoje,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=hoje,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=amanha,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=amanha,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=amanha,
        ),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem_ativas(aluno, escola):
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    return [
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            ativo=True,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            ativo=True,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
            ativo=True,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem_inativas(aluno, escola):
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    return [
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
            ativo=False,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            ativo=False,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
        baker.make(
            SolicitacaoDietaEspecial,
            status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
            ativo=False,
            aluno=aluno,
            rastro_escola=escola,
            data_termino=ontem,
        ),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem(
    solicitacoes_dieta_especial_dt_termino_ontem_ativas,
    solicitacoes_dieta_especial_dt_termino_ontem_inativas,
):
    return (
        solicitacoes_dieta_especial_dt_termino_ontem_ativas
        + solicitacoes_dieta_especial_dt_termino_ontem_inativas
    )


@pytest.fixture
def solicitacoes_dieta_especial_com_data_termino(
    solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior,
    solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas,
    solicitacoes_dieta_especial_dt_termino_ontem,
):
    solicitacoes = [] + solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas
    solicitacoes += solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior
    solicitacoes += solicitacoes_dieta_especial_dt_termino_ontem
    return solicitacoes


@pytest.fixture
def periodo_escolar_integral():
    return baker.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture
def log_dietas_ativas_canceladas_automaticamente(
    solicitacao_dieta_especial_autorizada_ativa,
):
    return baker.make(
        "LogDietasAtivasCanceladasAutomaticamente",
        dieta=solicitacao_dieta_especial_autorizada_ativa,
        codigo_eol_aluno="6595803",
        nome_aluno="GUILHERME RODRIGUES DA HORA",
        codigo_eol_escola_origem="019871",
        nome_escola_origem="EMEF PERICLES EUGENIO DA SILVA RAMOS",
        codigo_eol_escola_destino="018210",
        nome_escola_destino="EMEFM DARCY RIBEIRO",
    )


@pytest.fixture
def protocolo_padrao_dieta_especial():
    return baker.make(
        "ProtocoloPadraoDietaEspecial",
        nome_protocolo="ALERGIA A AVEIA",
        status="LIBERADO",
    )


@pytest.fixture
def protocolo_padrao_dieta_especial_2():
    edital = baker.make(
        "Edital", uuid="60f5a64e-8652-422d-a6e9-0a36717829c9", numero="edital-teste-2"
    )
    return baker.make(
        "ProtocoloPadraoDietaEspecial",
        nome_protocolo="ALERGIA A ABACAXI",
        status="LIBERADO",
        orientacoes_gerais="Orientação Geral",
        editais=[edital],
    )


@pytest.fixture
def protocolo_padrao_edital_parceira(edital_parceira):
    return baker.make(
        "ProtocoloPadraoDietaEspecial",
        status="LIBERADO",
        editais=[edital_parceira],
    )


@pytest.fixture
def substituicao_padrao_dieta_especial_2(
    alimentos, produtos, protocolo_padrao_dieta_especial_2
):
    return baker.make(
        "SubstituicaoAlimentoProtocoloPadrao",
        protocolo_padrao=protocolo_padrao_dieta_especial_2,
        alimento=alimentos[0],
        tipo="I",
        alimentos_substitutos=alimentos,
    )


@pytest.fixture
def client_autenticado_protocolo_dieta(client, django_user_model, escola, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_dieta_especial = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_DIETA_ESPECIAL, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_dieta_especial,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    baker.make("Edital", uuid="b7b6a0a7-b230-4783-94b6-8d3d22041ab3")
    baker.make("Edital", uuid="60f5a64e-8652-422d-a6e9-0a36717829c9")
    baker.make("Edital", uuid="4f7287e5-da63-4b23-8bbc-48cc6722c91e")
    baker.make("dieta_especial.Alimento", id=random.randint(1, 100000))
    baker.make(
        "dieta_especial.Alimento",
        id=random.randint(1, 100000),
        uuid="e67b6e67-7501-4d6e-8fac-ce219df3ed2b",
        tipo_listagem_protocolo="AMBOS",
    )
    return client


@pytest.fixture
def escola_cei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = baker.make("TipoUnidadeEscolar", iniciais="CEI DIRET")
    contato = baker.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="CEI DIRET JOAO MENDES",
        codigo_eol="001546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def log_aluno_integral_cei(escola_cei, periodo_escolar_integral):
    log = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
        quantidade_alunos=100,
    )
    log.criado_em = datetime.date(2025, 5, 5)
    log.save()
    return log


@pytest.fixture
def log_alunos_matriculados_integral_cei(escola_cei, periodo_escolar_integral):
    return baker.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
        quantidade_alunos=100,
    )


@pytest.fixture
def classificacoes_dietas():
    return [
        baker.make(ClassificacaoDieta, nome="Tipo A"),
        baker.make(ClassificacaoDieta, nome="Tipo A Enteral"),
        baker.make(ClassificacaoDieta, nome="Tipo B"),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_ativas(escola, classificacoes_dietas):
    periodo_manha = baker.make(PeriodoEscolar, nome="MANHA")
    baker.make(FaixaEtaria, inicio=1, fim=31)
    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno,
        rastro_escola=escola,
        escola_destino=escola,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        aluno=aluno,
        rastro_escola=escola,
        escola_destino=escola,
        classificacao=classificacoes_dietas[1],
    ),
    return SolicitacaoDietaEspecial.objects.all()


@pytest.fixture
def solicitacoes_dieta_especial_ativas_cei(escola_cei, classificacoes_dietas):
    periodo_tarde = baker.make(PeriodoEscolar, nome="TARDE")
    baker.make(FaixaEtaria, inicio=1, fim=31)
    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola_cei,
        periodo_escolar=periodo_tarde,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[1],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[0],
    )
    return SolicitacaoDietaEspecial.objects.all()


@pytest.fixture
def solicitacoes_dieta_especial_ativas_cemei(
    escola_cemei, classificacoes_dietas, periodo_escolar_integral
):
    baker.make(FaixaEtaria, inicio=1, fim=31)
    baker.make(FaixaEtaria, inicio=32, fim=88)
    aluno_a = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola_cemei,
        periodo_escolar=periodo_escolar_integral,
        serie="3B",
    )
    aluno_b = baker.make(
        Aluno,
        nome="Aluno Teste",
        codigo_eol="456789",
        data_nascimento="2017-01-01",
        escola=escola_cemei,
        periodo_escolar=periodo_escolar_integral,
        serie="6C",
    )
    aluno_c = baker.make(
        Aluno,
        nome="Aluno Teste__2",
        codigo_eol="123025",
        data_nascimento="2017-01-01",
        escola=escola_cemei,
        periodo_escolar=periodo_escolar_integral,
        serie="1A",
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno_a,
        rastro_escola=escola_cemei,
        escola_destino=escola_cemei,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno_b,
        rastro_escola=escola_cemei,
        escola_destino=escola_cemei,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno_c,
        rastro_escola=escola_cemei,
        escola_destino=escola_cemei,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        aluno=aluno_a,
        rastro_escola=escola_cemei,
        escola_destino=escola_cemei,
        classificacao=classificacoes_dietas[1],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno_b,
        rastro_escola=escola_cemei,
        escola_destino=escola_cemei,
        classificacao=classificacoes_dietas[2],
    ),
    return SolicitacaoDietaEspecial.objects.all()


@pytest.fixture
def solicitacoes_dieta_especial_ativas_emebs(escola_emebs, classificacoes_dietas):
    periodo_manha = baker.make(PeriodoEscolar, nome="MANHA")
    baker.make(FaixaEtaria, inicio=1, fim=31)
    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola_emebs,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno,
        rastro_escola=escola_emebs,
        escola_destino=escola_emebs,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        aluno=aluno,
        rastro_escola=escola_emebs,
        escola_destino=escola_emebs,
        classificacao=classificacoes_dietas[1],
    ),
    return SolicitacaoDietaEspecial.objects.all()


@pytest.fixture
def categoria_medicao():
    return baker.make("CategoriaMedicao", nome="ALIMENTAÇÃO")


@pytest.fixture
def solicitacao_medicao_inicial(escola_cei, categoria_medicao):
    tipo_contagem = baker.make("TipoContagemAlimentacao", nome="Fichas")
    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    historico = {
        "usuario": {
            "uuid": "a7f20675-50e1-46d2-a207-28543b93e19d",
            "nome": "usuario teste",
            "username": "12312312344",
            "email": "email@teste.com",
        },
        "criado_em": datetime.date.today().strftime("%Y-%m-%d %H:%M:%S"),
        "acao": "MEDICAO_CORRECAO_SOLICITADA",
        "alteracoes": [
            {
                "periodo_escolar": periodo_manha.nome,
                "tabelas_lancamentos": [
                    {
                        "categoria_medicao": "ALIMENTAÇÃO",
                        "semanas": [{"semana": "1", "dias": ["01"]}],
                    }
                ],
            },
        ],
    }
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    solicitacao_medicao = baker.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes=f"{ontem.month:02d}",
        ano=ontem.year,
        escola=escola_cei,
        ue_possui_alunos_periodo_parcial=True,
        historico=json.dumps([historico]),
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        "ValorMedicao",
        dia="01",
        semana="1",
        nome_campo="lanche",
        medicao=medicao,
        categoria_medicao=categoria_medicao,
        valor="10",
    )
    return solicitacao_medicao


@pytest.fixture
def solicitacoes_dieta_especial_ativas_cei_com_solicitacao_medicao(
    escola_cei,
    classificacoes_dietas,
    solicitacao_medicao_inicial,
    periodo_escolar_integral,
):
    baker.make(FaixaEtaria, inicio=1, fim=50)
    baker.make(ClassificacaoDieta, nome="Tipo C")
    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[0],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[1],
    ),
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[2],
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        aluno=aluno,
        rastro_escola=escola_cei,
        escola_destino=escola_cei,
        classificacao=classificacoes_dietas[2],
    )
    return SolicitacaoDietaEspecial.objects.all()


@pytest.fixture
def usuario_com_pk():
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = Usuario.objects.create_user(
        nome="Antonio Jose",
        username=email,
        password=password,
        email=email,
        registro_funcional="1545933",
        pk=1,
    )
    return user


@freeze_time("2025-1-10")
@pytest.fixture
def solicitacoes_processa_dieta_especial(escola_cei, periodo_escolar_integral):
    aluno = baker.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2022-01-01",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
    )
    dieta_alterada = baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        ativo=True,
        data_inicio=datetime.date.today(),
        tipo_solicitacao=constants.TIPO_SOLICITACAO_DIETA.get("COMUM"),
        escola_destino=escola_cei,
        aluno=aluno,
        rastro_escola=escola_cei,
    )

    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        ativo=False,
        data_inicio=datetime.date.today(),
        tipo_solicitacao=constants.TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"),
        dieta_alterada=dieta_alterada,
        escola_destino=escola_cei,
        aluno=aluno,
        rastro_escola=escola_cei,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        ativo=False,
        data_inicio=datetime.date.today(),
        tipo_solicitacao=constants.TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE"),
        dieta_alterada=dieta_alterada,
        escola_destino=escola_cei,
        aluno=aluno,
        rastro_escola=escola_cei,
    )
    baker.make(
        SolicitacaoDietaEspecial,
        status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ativo=False,
        data_inicio=datetime.date.today(),
        tipo_solicitacao=constants.TIPO_SOLICITACAO_DIETA.get("COMUM"),
        dieta_alterada=dieta_alterada,
        escola_destino=escola_cei,
        aluno=aluno,
        rastro_escola=escola_cei,
    )


@pytest.fixture
def make_periodo_escolar():
    def handle(nome: str):
        if PeriodoEscolar.objects.filter(nome=nome).exists():
            return PeriodoEscolar.objects.get(nome=nome)
        return baker.make("PeriodoEscolar", nome=nome)

    return handle


@pytest.fixture
def filtro_historico_relatorio_dietas(
    escola, escola_emebs, periodo_escolar_integral, classificacoes_dietas
):
    from django.http import QueryDict

    query_params = QueryDict(mutable=True)
    query_params.setlist(
        "unidades_educacionais_selecionadas[]",
        [
            str(escola.uuid),
            str(escola_emebs.uuid),
        ],
    )
    query_params.setlist(
        "tipos_unidades_selecionadas[]",
        [str(escola_emebs.tipo_unidade.uuid)],
    )
    query_params.setlist(
        "periodos_escolares_selecionadas[]",
        [str(periodo_escolar_integral.uuid)],
    )
    query_params.setlist(
        "classificacoes_selecionadas[]",
        [classificacao.id for classificacao in classificacoes_dietas],
    )
    query_params["tipo_gestao"] = str(escola_emebs.tipo_gestao.uuid)
    query_params["lote"] = str(escola_emebs.lote.uuid)
    query_params["data"] = "12/04/2025"

    return query_params


@pytest.fixture
def escolas_tipo_emebs():
    classificacao = {
        "Escola EMEBS": {
            "tipo_unidade": "EMEBS",
            "lote": "Lote EMEBS",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {"TARDE": 1},
                    "periodos": {},
                    "por_idade": {},
                    "turma_infantil": {},
                    "faixa_etaria": {},
                    "total": 0,
                },
            },
        }
    }

    item = {
        "infantil_ou_fundamental": "FUNDAMENTAL",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola EMEBS",
        "nome_periodo_escolar": "TARDE",
        "tipo_unidade": "EMEBS",
        "lote": "Lote EMEBS",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 5,
        "inicio": None,
        "fim": None,
    }
    item_somatorio = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola EMEBS",
        "nome_periodo_escolar": None,
        "tipo_unidade": "EMEBS",
        "lote": "Lote EMEBS",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 6,
        "inicio": None,
        "fim": None,
    }
    return item, item_somatorio, classificacao


@pytest.fixture
def escolas_tipo_emei_emef_cieja():
    classificacao = {
        "Escola EMEF": {
            "tipo_unidade": "EMEF",
            "lote": "LOTE EMEF",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {},
                    "periodos": {"TARDE": 1},
                    "por_idade": {},
                    "turma_infantil": {},
                    "faixa_etaria": {},
                    "total": 0,
                },
            },
        }
    }

    item = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola EMEF",
        "nome_periodo_escolar": "TARDE",
        "tipo_unidade": "EMEF",
        "lote": "LOTE EMEF",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 5,
        "inicio": None,
        "fim": None,
    }

    item_somatorio = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola EMEF",
        "nome_periodo_escolar": None,
        "tipo_unidade": "EMEF",
        "lote": "LOTE EMEF",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 6,
        "inicio": None,
        "fim": None,
    }
    return item, item_somatorio, classificacao


@pytest.fixture
def escolas_tipos_cmct_ceugestao():
    classificacao = {
        "Escola CEU GESTAO": {
            "tipo_unidade": "CEU GESTAO",
            "lote": "LOTE CEU GESTAO",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {},
                    "periodos": {},
                    "por_idade": {},
                    "turma_infantil": {},
                    "faixa_etaria": {},
                    "total": 5,
                },
            },
        }
    }

    item = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEU GESTAO",
        "nome_periodo_escolar": None,
        "tipo_unidade": "CEU GESTAO",
        "lote": "LOTE CEU GESTAO",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 10,
        "inicio": None,
        "fim": None,
    }

    item_somatorio = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEU GESTAO",
        "nome_periodo_escolar": None,
        "tipo_unidade": "CEU GESTAO",
        "lote": "LOTE CEU GESTAO",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 5,
        "inicio": None,
        "fim": None,
    }
    return item, item_somatorio, classificacao


@pytest.fixture
def escolas_tipo_cei():
    classificacao = {
        "Escola CEI DIRET": {
            "tipo_unidade": "CEI DIRET",
            "lote": "LOTE CEI DIRET",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {},
                    "periodos": {
                        "INTEGRAL": [
                            {"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1}
                        ]
                    },
                    "por_idade": {},
                    "turma_infantil": {},
                    "faixa_etaria": {},
                    "total": 0,
                }
            },
        }
    }

    item = {
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEI DIRET",
        "nome_periodo_escolar": "INTEGRAL",
        "tipo_unidade": "CEI DIRET",
        "lote": "LOTE CEI DIRET",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 3,
        "inicio": 7,
        "fim": 12,
        "infantil_ou_fundamental": None,
        "cei_ou_emei": None,
    }
    item_somatorio = {
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEI DIRET",
        "nome_periodo_escolar": "INTEGRAL",
        "tipo_unidade": "CEI DIRET",
        "lote": "LOTE CEI DIRET",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 4,
        "inicio": None,
        "fim": None,
        "infantil_ou_fundamental": None,
        "cei_ou_emei": None,
    }
    return item, item_somatorio, classificacao


@pytest.fixture
def escolas_tipo_cemei_por_faixa_etaria():
    classificacao = {
        "Escola CEMEI": {
            "tipo_unidade": "CEMEI",
            "lote": "LOTE CEMEI",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {},
                    "periodos": {},
                    "por_idade": {
                        "INTEGRAL": [
                            {"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1}
                        ]
                    },
                    "turma_infantil": {},
                    "faixa_etaria": {},
                    "total": 0,
                }
            },
        }
    }
    item = {
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEMEI",
        "nome_periodo_escolar": "INTEGRAL",
        "tipo_unidade": "CEMEI",
        "lote": "LOTE CEMEI",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 3,
        "inicio": 7,
        "fim": 12,
        "infantil_ou_fundamental": None,
        "cei_ou_emei": None,
    }
    item_somatorio = {
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEMEI",
        "nome_periodo_escolar": "INTEGRAL",
        "tipo_unidade": "CEMEI",
        "lote": "LOTE CEMEI",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 4,
        "inicio": None,
        "fim": None,
        "infantil_ou_fundamental": None,
        "cei_ou_emei": None,
    }
    return item, item_somatorio, classificacao


@pytest.fixture
def escolas_tipo_cemei_por_periodo():
    classificacao = {
        "Escola CEMEI": {
            "tipo_unidade": "CEMEI",
            "lote": "LOTE CEMEI",
            "data": datetime.date(2023, 12, 1),
            "classificacoes": {
                "Tipo A": {
                    "infantil": {},
                    "fundamental": {},
                    "periodos": {},
                    "por_idade": {},
                    "turma_infantil": {"INTEGRAL": 1},
                    "faixa_etaria": {},
                    "total": 0,
                }
            },
        }
    }

    item = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEMEI",
        "nome_periodo_escolar": "INTEGRAL",
        "tipo_unidade": "CEMEI",
        "lote": "LOTE CEMEI",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 3,
        "inicio": None,
        "fim": None,
    }

    item_somatorio = {
        "infantil_ou_fundamental": "N/A",
        "cei_ou_emei": "N/A",
        "data": datetime.date(2023, 12, 1),
        "nome_escola": "Escola CEMEI",
        "nome_periodo_escolar": None,
        "tipo_unidade": "CEMEI",
        "lote": "LOTE CEMEI",
        "nome_classificacao": "Tipo A",
        "quantidade_total": 4,
        "inicio": None,
        "fim": None,
    }

    return item, item_somatorio, classificacao


@pytest.fixture
def classificacao_tipo_a():
    return baker.make("ClassificacaoDieta", nome="Tipo A")


@pytest.fixture
def classificacao_tipo_b():
    return baker.make("ClassificacaoDieta", nome="Tipo B")


@pytest.fixture
def periodo_escolar_manha():
    return baker.make(PeriodoEscolar, nome="MANHA")


@pytest.fixture
def log_dietas_autorizadas(
    escola_emebs,
    escola_cemei,
    periodo_escolar_integral,
    classificacao_tipo_a,
    classificacao_tipo_b,
    periodo_escolar_manha,
):
    data = datetime.date(2024, 3, 20)

    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_emebs,
        quantidade=5,
        classificacao=classificacao_tipo_a,
        periodo_escolar=periodo_escolar_integral,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="INFANTIL",
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_emebs,
        quantidade=6,
        classificacao=classificacao_tipo_a,
        periodo_escolar=periodo_escolar_manha,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="FUNDAMENTAL",
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_emebs,
        quantidade=11,
        classificacao=classificacao_tipo_a,
        periodo_escolar=None,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
        data=data,
    )

    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_cemei,
        quantidade=7,
        classificacao=classificacao_tipo_b,
        periodo_escolar=periodo_escolar_integral,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_cemei,
        quantidade=8,
        classificacao=classificacao_tipo_b,
        periodo_escolar=periodo_escolar_manha,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola_cemei,
        quantidade=15,
        classificacao=classificacao_tipo_b,
        periodo_escolar=None,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
        data=data,
    )


@pytest.fixture
def log_dietas_autorizadas_cei(
    escola_cei,
    escola_cemei,
    periodo_escolar_integral,
    classificacao_tipo_a,
    classificacao_tipo_b,
    periodo_escolar_manha,
):
    data = data = datetime.date(2024, 3, 20)
    faixa_um = baker.make("FaixaEtaria", inicio=0, fim=6)
    faixa_dois = baker.make("FaixaEtaria", inicio=7, fim=12)
    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cei,
        quantidade=10,
        classificacao=classificacao_tipo_b,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=faixa_um,
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cei,
        quantidade=11,
        classificacao=classificacao_tipo_b,
        periodo_escolar=periodo_escolar_manha,
        faixa_etaria=faixa_dois,
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cei,
        quantidade=21,
        classificacao=classificacao_tipo_b,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=None,
        data=data,
    )

    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cemei,
        quantidade=12,
        classificacao=classificacao_tipo_a,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=faixa_um,
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cemei,
        quantidade=13,
        classificacao=classificacao_tipo_a,
        periodo_escolar=periodo_escolar_manha,
        faixa_etaria=faixa_dois,
        data=data,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cemei,
        quantidade=25,
        classificacao=classificacao_tipo_a,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=None,
        data=data,
    )


@pytest.fixture
def unidade_educacional():
    resultado = {
        "lote": "LOTE 07",
        "unidade_educacional": "CEI ANTÔNIO",
        "tipo_unidade": "CEI",
        "classificacao": "Tipo A",
        "total": 20,
        "data": "24/08/2023",
        "periodos": [
            {
                "periodo": "TARDE",
                "faixa_etaria": [
                    {"faixa": "01 a 03 meses", "autorizadas": 5},
                    {"faixa": "07 a 11 meses", "autorizadas": 2},
                    {"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1},
                    {"faixa": "04 anos a 06 anos", "autorizadas": 2},
                ],
            },
            {
                "periodo": "MANHA",
                "faixa_etaria": [
                    {"faixa": "01 a 03 meses", "autorizadas": 3},
                    {"faixa": "07 a 11 meses", "autorizadas": 2},
                    {"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 2},
                    {"faixa": "04 anos a 06 anos", "autorizadas": 3},
                ],
            },
        ],
    }

    return UnidadeEducacionalSerializer(resultado)


@pytest.fixture
def alergia_a_chocolate():
    return baker.make(AlergiaIntolerancia, descricao="Alergia a chocolate")


@pytest.fixture
def alergia_ao_trigo():
    return baker.make(AlergiaIntolerancia, descricao="Alergia a derivados do trigo")


@pytest.fixture
def relatorio_recreio_nas_ferias(
    escola,
    escola_dre_guaianases,
    escola_cemei,
    escola_parceira,
    escola_emebs,
    motivo_alteracao_ue,
    classificacao_tipo_a,
    classificacao_tipo_b,
    alergia_a_chocolate,
    alergia_ao_trigo,
):

    # Alunos Matriculados
    baker.make(
        "SolicitacaoDietaEspecial",
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        tipo_solicitacao="ALTERACAO_UE",
        motivo_alteracao_ue=motivo_alteracao_ue,
        rastro_escola=escola,
        escola_destino=escola_dre_guaianases,
        aluno=baker.make("Aluno", nome="Antonio", codigo_eol="923459"),
        alergias_intolerancias=[alergia_a_chocolate],
        classificacao=classificacao_tipo_a,
        data_inicio=datetime.date(2025, 5, 1),
        data_termino=datetime.date(2025, 5, 10),
    )
    baker.make(
        "SolicitacaoDietaEspecial",
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        tipo_solicitacao="ALTERACAO_UE",
        motivo_alteracao_ue=motivo_alteracao_ue,
        rastro_escola=escola_dre_guaianases,
        escola_destino=escola_cemei,
        aluno=baker.make("Aluno", nome="Maria", codigo_eol="823458"),
        alergias_intolerancias=[alergia_ao_trigo],
        classificacao=classificacao_tipo_b,
        data_inicio=datetime.date(2025, 5, 5),
        data_termino=datetime.date(2025, 5, 15),
    )
    # Alunos Não Matriculados
    baker.make(
        "SolicitacaoDietaEspecial",
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        tipo_solicitacao="COMUM",
        dieta_para_recreio_ferias=True,
        rastro_escola=escola_cemei,
        escola_destino=escola_parceira,
        aluno=baker.make("Aluno", nome=f"Carlos", codigo_eol="123456"),
        alergias_intolerancias=[alergia_a_chocolate],
        classificacao=classificacao_tipo_a,
        periodo_recreio_inicio=datetime.date(2025, 5, 2),
        periodo_recreio_fim=datetime.date(2025, 5, 9),
    )
    baker.make(
        "SolicitacaoDietaEspecial",
        status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
        tipo_solicitacao="COMUM",
        dieta_para_recreio_ferias=True,
        rastro_escola=escola_parceira,
        escola_destino=escola_emebs,
        aluno=baker.make("Aluno", nome="Carla", codigo_eol="723457"),
        alergias_intolerancias=[alergia_ao_trigo],
        classificacao=classificacao_tipo_b,
        periodo_recreio_inicio=datetime.date(2025, 5, 10),
        periodo_recreio_fim=datetime.date(2025, 5, 20),
    )
