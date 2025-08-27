import datetime
from unittest.mock import Mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from faker import Faker
from model_bakery import baker

from sme_sigpae_api.produto.api.serializers.serializers import (
    HomologacaoProdutoPainelGerencialSerializer,
    ProdutoReclamacaoSerializer,
    ReclamacaoDeProdutoSerializer,
)
from sme_sigpae_api.produto.api.viewsets import (
    HomologacaoProdutoPainelGerencialViewSet,
    ProdutoViewSet,
    ReclamacaoProdutoViewSet,
)

from ...dados_comuns import constants
from ...dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from ...dados_comuns.fluxo_status import (
    HomologacaoProdutoWorkflow,
    ReclamacaoProdutoWorkflow,
)
from ...dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ...escola.models import DiretoriaRegional, TipoGestao
from ...terceirizada.models import Contrato
from ..models import AnaliseSensorial, HomologacaoProduto, ProdutoEdital

fake = Faker("pt-Br")
Faker.seed(420)


@pytest.fixture
def escola():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="9640fef4-a068-474e-8979-2e1b2654357a",
    )
    contato = baker.make("Contato", email="test@test2.com")

    return baker.make(
        "Escola",
        uuid="b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd",
        lote=lote,
        diretoria_regional=diretoria_regional,
        contato=contato,
    )


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def template_homologacao_produto():
    return baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.HOMOLOGACAO_PRODUTO,
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def perfil_gpcodae():
    return baker.make("Perfil", nome=constants.ADMINISTRADOR_GESTAO_PRODUTO, ativo=True)


@pytest.fixture
def client_autenticado_vinculo_codae_produto(
    client, django_user_model, escola, codae, template_homologacao_produto
):
    email = "test2@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_produto = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_produto,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def produtos_edital_41(escola):
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 41/sme/2017",
        uuid="12288b47-9d27-4089-8c2e-48a6061d83ea",
    )
    baker.make(
        "Edital",
        numero="Edital de Pregão nº 78/sme/2016",
        uuid="b30a2102-2ae0-404d-8a56-8e5ecd73f868",
    )
    edital_3 = baker.make(
        "Edital",
        numero="Edital de Pregão nº 78/sme/2022",
        uuid="131f4000-3e31-44f1-9ba5-e7df001a8426",
    )
    marca_1 = baker.make("Marca", nome="NAMORADOS")
    marca_2 = baker.make("Marca", nome="TIO JOÃO")
    fabricante_1 = baker.make("Fabricante", nome="Fabricante 001")
    fabricante_2 = baker.make("Fabricante", nome="Fabricante 002")
    produto_1 = baker.make(
        "Produto", nome="ARROZ", marca=marca_1, fabricante=fabricante_1
    )
    produto_2 = baker.make(
        "Produto",
        nome="ARROZ",
        marca=marca_2,
        fabricante=fabricante_2,
        aditivos="aditivoA, aditivoB, aditivoC",
    )
    homologacao_p1 = baker.make(
        "HomologacaoProduto",
        produto=produto_1,
        rastro_terceirizada=escola.lote.terceirizada,
        status=HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
    )
    homologacao_p2 = baker.make(
        "HomologacaoProduto",
        produto=produto_2,
        rastro_terceirizada=escola.lote.terceirizada,
        status=HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
    )
    log = baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao_p1.uuid,
        criado_em=datetime.date(2023, 1, 1),
        status_evento=22,  # CODAE_HOMOLOGADO
        solicitacao_tipo=10,
    )  # HOMOLOGACAO_PRODUTO
    log.criado_em = datetime.date(2023, 1, 1)
    log.save()
    log_2 = baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao_p2.uuid,
        criado_em=datetime.date(2023, 2, 1),
        status_evento=22,  # CODAE_HOMOLOGADO
        solicitacao_tipo=10,
    )  # HOMOLOGACAO_PRODUTO
    log_2.criado_em = datetime.date(2023, 2, 1)
    log_2.save()
    pe_1 = baker.make(
        "ProdutoEdital",
        produto=produto_1,
        edital=edital,
        tipo_produto="Comum",
        uuid="0f81a49b-0836-42d5-af9e-12cbd7ca76a8",
    )
    baker.make(
        "ProdutoEdital",
        produto=produto_1,
        edital=edital_3,
        tipo_produto="Comum",
        uuid="e42e3b97-6853-4327-841d-34292c33963c",
    )
    pe_2 = baker.make(
        "ProdutoEdital",
        produto=produto_2,
        edital=edital,
        tipo_produto="Comum",
        uuid="38cdf4a8-6621-4248-8f5c-378d1bdbfb71",
    )
    dh_1 = baker.make(
        "DataHoraVinculoProdutoEdital", produto_edital=pe_1, suspenso=True
    )
    dh_1.criado_em = datetime.date(2023, 1, 1)
    dh_1.save()
    dh_2 = baker.make("DataHoraVinculoProdutoEdital", produto_edital=pe_2)
    dh_2.criado_em = datetime.date(2023, 2, 1)
    dh_2.save()
    dh_3 = baker.make("DataHoraVinculoProdutoEdital", produto_edital=pe_1)
    dh_3.criado_em = datetime.date(2023, 3, 1)
    dh_3.save()


@pytest.fixture
def client_autenticado_vinculo_terceirizada(
    client, django_user_model, escola, template_homologacao_produto
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888887"
    )
    perfil_admin_terceirizada = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_EMPRESA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb95e8afaf0",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=tecerizada,
        perfil=perfil_admin_terceirizada,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, user


@pytest.fixture
def user(django_user_model):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    return django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888881"
    )


@pytest.fixture
def client_autenticado_vinculo_terceirizada_homologacao(
    client, django_user_model, escola
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_diretor = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_EMPRESA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb95e8afaf0",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=tecerizada,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    produto = baker.make("Produto", criado_por=user)
    homologacao_produto = baker.make(
        "HomologacaoProduto",
        produto=produto,
        rastro_terceirizada=escola.lote.terceirizada,
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
        uuid="774ad907-d871-4bfd-b1aa-d4e0ecb6c01f",
    )
    homologacao_produto.status = (
        HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    )
    homologacao_produto.save()
    client.login(username=email, password=password)
    return client, homologacao_produto


@pytest.fixture
def protocolo1():
    return baker.make("ProtocoloDeDietaEspecial", nome="Protocolo1")


@pytest.fixture
def protocolo2():
    return baker.make("ProtocoloDeDietaEspecial", nome="Protocolo2")


@pytest.fixture
def protocolo3():
    return baker.make("ProtocoloDeDietaEspecial", nome="Protocolo3")


@pytest.fixture
def marca1():
    return baker.make("Marca", nome="Marca1")


@pytest.fixture
def marca2():
    return baker.make("Marca", nome="Marca2")


@pytest.fixture
def fabricante():
    return baker.make("Fabricante", nome="Fabricante1")


@pytest.fixture
def unidade_medida():
    return baker.make("produto.UnidadeMedida", nome="Litros")


@pytest.fixture
def embalagem_produto():
    return baker.make("EmbalagemProduto", nome="Bag")


@pytest.fixture
def terceirizada():
    return baker.make(
        "Terceirizada",
        contatos=[baker.make("dados_comuns.Contato")],
        make_m2m=True,
        nome_fantasia="Alimentos SA",
    )


@pytest.fixture
def edital():
    return baker.make(
        "Edital",
        uuid="617a8139-02a9-4801-a197-622aa20795b9",
        numero="Edital de Pregão nº 56/SME/2016",
        tipo_contratacao="Teste",
        processo="Teste",
        objeto="Teste",
    )


@pytest.fixture
def produto(user, protocolo1, protocolo2, marca1, fabricante):
    produto = baker.make(
        "Produto",
        uuid="a37bcf3f-a288-44ae-87ae-dbec181a34d4",
        criado_por=user,
        eh_para_alunos_com_dieta=True,
        componentes="Componente1, Componente2",
        tem_aditivos_alergenicos=False,
        tipo="Tipo1",
        embalagem="Embalagem X",
        prazo_validade="Alguns dias",
        info_armazenamento="Guardem bem",
        outras_informacoes="Produto do bom",
        numero_registro="123123123",
        porcao="5 cuias",
        unidade_caseira="Unidade3",
        nome="Produto1",
        fabricante=fabricante,
        marca=marca1,
        protocolos=[
            protocolo1,
            protocolo2,
        ],
    )
    return produto


@pytest.fixture
def produto_com_editais(produto, escola):
    edital = baker.make(
        "Edital",
        numero="Edital de Pregão nº 41/sme/2017",
        uuid="12288b47-9d27-4089-8c2e-48a6061d83ea",
    )
    edital_2 = baker.make(
        "Edital",
        numero="Edital de Pregão nº 78/sme/2016",
        uuid="b30a2102-2ae0-404d-8a56-8e5ecd73f868",
    )
    edital_3 = baker.make(
        "Edital",
        numero="Edital de Pregão nº 78/sme/2022",
        uuid="131f4000-3e31-44f1-9ba5-e7df001a8426",
    )
    pe1 = baker.make(
        "ProdutoEdital",
        produto=produto,
        edital=edital,
        tipo_produto="Comum",
        uuid="0f81a49b-0836-42d5-af9e-12cbd7ca76a8",
    )
    pe2 = baker.make(
        "ProdutoEdital",
        produto=produto,
        edital=edital_2,
        tipo_produto="Comum",
        uuid="e42e3b97-6853-4327-841d-34292c33963c",
    )
    pe3 = baker.make(
        "ProdutoEdital",
        produto=produto,
        edital=edital_3,
        tipo_produto="Comum",
        uuid="3b4f59eb-a686-49e9-beab-3514a93e3184",
    )
    baker.make("DataHoraVinculoProdutoEdital", produto_edital=pe1)
    baker.make("DataHoraVinculoProdutoEdital", produto_edital=pe2)
    baker.make("DataHoraVinculoProdutoEdital", produto_edital=pe3)

    baker.make(
        Contrato,
        numero="11",
        processo="42345",
        diretorias_regionais=[escola.diretoria_regional],
        edital=edital,
        lotes=[escola.lote],
    )
    baker.make(
        Contrato,
        numero="22",
        processo="42344",
        diretorias_regionais=[escola.diretoria_regional],
        edital=edital_2,
        lotes=[escola.lote],
    )
    baker.make(
        Contrato,
        numero="33",
        processo="42445",
        diretorias_regionais=[escola.diretoria_regional],
        edital=edital_3,
        lotes=[escola.lote],
    )
    return produto


@pytest.fixture
def hom_produto_com_editais(
    escola, template_homologacao_produto, user, produto_com_editais
):
    perfil_admin_terceirizada = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil_admin_terceirizada,
        data_inicial=hoje,
        ativo=True,
    )
    homologacao_produto = baker.make(
        "HomologacaoProduto",
        produto=produto_com_editais,
        rastro_terceirizada=escola.lote.terceirizada,
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao_produto.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO,
    )
    baker.make(
        "ReclamacaoDeProduto",
        uuid="dd06d200-e2f9-4be7-a304-82831ce93ee1",
        criado_por=user,
        homologacao_produto=homologacao_produto,
        escola=escola,
        status=ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO,
        reclamacao="Produto com aparência alterada",
    )

    return homologacao_produto


@pytest.fixture
def hom_produto_com_editais_suspenso(hom_produto_com_editais):
    hom_produto_com_editais.status = HomologacaoProdutoWorkflow.CODAE_SUSPENDEU
    hom_produto_com_editais.save()
    return hom_produto_com_editais


@pytest.fixture
def hom_produto_com_editais_pendente_homologacao(hom_produto_com_editais):
    hom_produto_com_editais.status = (
        HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    )
    hom_produto_com_editais.save()
    return hom_produto_com_editais


@pytest.fixture
def hom_produto_com_editais_escola_ou_nutri_reclamou(hom_produto_com_editais):
    hom_produto_com_editais.status = (
        HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
    )
    hom_produto_com_editais.save()
    return hom_produto_com_editais


@pytest.fixture
def hom_copia(hom_produto_com_editais):
    produto_copia = hom_produto_com_editais.cria_copia_produto()
    homologacao_copia = hom_produto_com_editais.cria_copia_homologacao_produto(
        produto_copia
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao_copia.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_PENDENTE_HOMOLOGACAO,
        solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO,
    )
    baker.make("AnaliseSensorial", homologacao_produto=homologacao_copia)
    resposta_analise = baker.make(
        "RespostaAnaliseSensorial", homologacao_produto=homologacao_copia
    )
    baker.make(
        "AnexoRespostaAnaliseSensorial", resposta_analise_sensorial=resposta_analise
    )
    return homologacao_copia


@pytest.fixture
def hom_copia_pendente_homologacao(hom_copia):
    hom_copia.status = HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    hom_copia.save()
    return hom_copia


@pytest.fixture
def homologacoes_produto(produto, terceirizada):
    hom = baker.make(
        "HomologacaoProduto",
        produto=produto,
        rastro_terceirizada=terceirizada,
        status=HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
    )
    baker.make("LogSolicitacoesUsuario", uuid_original=hom.uuid)
    return hom


@pytest.fixture
def vinculo_produto_edital(produto, edital):
    produto_edital = baker.make(
        "ProdutoEdital",
        uuid="fae48de3-0d2f-4eb1-8b3e-0ddf7d45ee64",
        produto=produto,
        edital=edital,
        outras_informacoes="Teste 1",
        ativo=True,
        tipo_produto=ProdutoEdital.DIETA_ESPECIAL,
    )
    return produto_edital


@pytest.fixture
def client_autenticado_da_terceirizada(client, django_user_model, terceirizada):
    email = "foo@codae.com"
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_terc = baker.make("Perfil", nome="TERCEIRIZADA", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=terceirizada,
        perfil=perfil_adm_terc,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def tipo_gestao():
    return baker.make(TipoGestao, nome="TERC TOTAL")


@pytest.fixture
def diretoria_regional(tipo_gestao):
    dre = baker.make(
        DiretoriaRegional,
        nome=fake.name(),
        uuid="d305add2-f070-4ad3-8c17-ba9664a7c655",
        make_m2m=True,
    )
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    baker.make("Escola", diretoria_regional=dre, tipo_gestao=tipo_gestao)
    return dre


@pytest.fixture
def contrato(diretoria_regional, edital):
    return baker.make(
        Contrato,
        numero="1",
        processo="12345",
        diretorias_regionais=[diretoria_regional],
        edital=edital,
    )


@pytest.fixture
def client_autenticado_da_dre(client, django_user_model, diretoria_regional):
    email = "user@dre.com"
    password = "admin@123"
    perfil_adm_dre = baker.make("Perfil", nome="ADM_DRE", ativo=True)
    usuario = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="123456"
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=diretoria_regional,
        perfil=perfil_adm_dre,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, usuario


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model, escola):
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
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client, usuario


@pytest.fixture
def info_nutricional1():
    return baker.make("InformacaoNutricional", nome="CALORIAS")


@pytest.fixture
def info_nutricional2():
    return baker.make("InformacaoNutricional", nome="LACTOSE")


@pytest.fixture
def info_nutricional3():
    return baker.make("InformacaoNutricional", nome="COLESTEROL")


@pytest.fixture
def info_nutricional_produto1(produto, info_nutricional1):
    return baker.make(
        "InformacoesNutricionaisDoProduto",
        produto=produto,
        informacao_nutricional=info_nutricional1,
        quantidade_porcao="1",
        valor_diario="2",
    )


@pytest.fixture
def info_nutricional_produto2(produto, info_nutricional2):
    return baker.make(
        "InformacoesNutricionaisDoProduto",
        produto=produto,
        informacao_nutricional=info_nutricional2,
        quantidade_porcao="3",
        valor_diario="4",
    )


@pytest.fixture
def info_nutricional_produto3(produto, info_nutricional3):
    return baker.make(
        "InformacoesNutricionaisDoProduto",
        produto=produto,
        informacao_nutricional=info_nutricional3,
        quantidade_porcao="5",
        valor_diario="6",
    )


@pytest.fixture
def especificacao_produto1(produto, unidade_medida, embalagem_produto):
    return baker.make(
        "EspecificacaoProduto",
        volume=1.5,
        produto=produto,
        unidade_de_medida=unidade_medida,
        embalagem_produto=embalagem_produto,
    )


@pytest.fixture
def produto_edital(user):
    return baker.make(
        "NomeDeProdutoEdital", nome="PRODUTO TESTE", ativo=True, criado_por=user
    )


@pytest.fixture
def produto_logistica(user):
    return baker.make(
        "NomeDeProdutoEdital",
        nome="PRODUTO TESTE",
        tipo_produto="LOGISTICA",
        ativo=True,
        criado_por=user,
    )


@pytest.fixture
def produto_edital_rascunho():
    return {
        "nome": "PRODUTO DE LOGISTICA",
        "ativo": "Ativo",
        "tipo_produto": "LOGISTICA",
    }


@pytest.fixture
def arquivo():
    return SimpleUploadedFile(
        "planilha-teste.pdf", bytes("CONTEUDO TESTE TESTE TESTE", encoding="utf-8")
    )


@pytest.fixture
def imagem_produto1(produto, arquivo):
    return baker.make(
        "ImagemDoProduto", produto=produto, nome="Imagem1", arquivo=arquivo
    )


@pytest.fixture
def imagem_produto2(produto, arquivo):
    return baker.make(
        "ImagemDoProduto", produto=produto, nome="Imagem2", arquivo=arquivo
    )


@pytest.fixture
def client_autenticado_vinculo_escola_ue(client, django_user_model, escola):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )

    perfil_diretor = baker.make(
        "Perfil",
        nome="DIRETOR_UE",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
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
    return client, user


@pytest.fixture
def client_autenticado_vinculo_escola_nutrisupervisor(
    client, django_user_model, escola
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )

    perfil_nutri = baker.make(
        "Perfil",
        nome="COORDENADOR_SUPERVISAO_NUTRICAO",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_nutri,
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
def client_autenticado_vinculo_codae_nutrisupervisor(client, django_user_model, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )

    perfil_nutri = baker.make(
        "Perfil",
        nome="COORDENADOR_SUPERVISAO_NUTRICAO",
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_nutri,
        data_inicial=hoje,
        ativo=True,
    )
    assert user.tipo_usuario == constants.TIPO_USUARIO_NUTRISUPERVISOR
    baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def homologacao_produto(escola, template_homologacao_produto, user, produto, edital):
    perfil_admin_terceirizada = baker.make(
        "Perfil", nome=constants.ADMINISTRADOR_EMPRESA, ativo=True
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil_admin_terceirizada,
        data_inicial=hoje,
        ativo=True,
    )
    homologacao_produto = baker.make(
        "HomologacaoProduto",
        produto=produto,
        rastro_terceirizada=escola.lote.terceirizada,
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
    )
    baker.make("ProdutoEdital", edital=edital, produto=produto, suspenso=False)
    return homologacao_produto


@pytest.fixture
def homologacao_produto_pendente_homologacao(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_homologado(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_homologado_com_log(homologacao_produto, user):
    homologacao_produto.inicia_fluxo(user=user)
    return homologacao_produto


@pytest.fixture
def homologacao_produto_escola_ou_nutri_reclamou(homologacao_produto):
    homologacao_produto.status = (
        HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
    )
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def reclamacao(homologacao_produto_escola_ou_nutri_reclamou, escola, user):
    reclamacao = baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=homologacao_produto_escola_ou_nutri_reclamou,
        escola=escola,
        reclamante_registro_funcional="23456789",
        reclamante_cargo="Cargo",
        reclamante_nome="Anderson",
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
    )
    return reclamacao


@pytest.fixture
def homologacao_produto_gpcodae_questionou_escola(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_gpcodae_questionou_nutrisupervisor(homologacao_produto):
    homologacao_produto.status = (
        HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR
    )
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_rascunho(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.RASCUNHO
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def reclamacao_ue(homologacao_produto_gpcodae_questionou_escola, escola, user):
    reclamacao = baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=homologacao_produto_gpcodae_questionou_escola,
        escola=escola,
        reclamante_registro_funcional="23456788",
        reclamante_cargo="Cargo",
        reclamante_nome="Arthur",
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
        status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE,
    )
    return reclamacao


@pytest.fixture
def reclamacao_nutrisupervisor(
    homologacao_produto_gpcodae_questionou_nutrisupervisor, escola, user
):
    reclamacao = baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=homologacao_produto_gpcodae_questionou_nutrisupervisor,
        escola=escola,
        reclamante_registro_funcional="8888888",
        reclamante_cargo="Cargo",
        reclamante_nome="Arthur",
        criado_por=user,
        criado_em=datetime.datetime.utcnow(),
        status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR,
    )
    return reclamacao


@pytest.fixture
def item_cadastrado_1(marca1):
    return baker.make(
        "ItemCadastro",
        tipo="MARCA",
        content_type=ContentType.objects.get(model="marca"),
        content_object=marca1,
    )


@pytest.fixture
def item_cadastrado_2(fabricante):
    return baker.make(
        "ItemCadastro",
        tipo="FABRICANTE",
        content_type=ContentType.objects.get(model="fabricante"),
        content_object=fabricante,
    )


@pytest.fixture
def item_cadastrado_3(unidade_medida):
    return baker.make(
        "ItemCadastro",
        tipo="UNIDADE_MEDIDA",
        content_type=ContentType.objects.get(
            model="unidademedida", app_label="produto"
        ),
        content_object=unidade_medida,
    )


@pytest.fixture
def item_cadastrado_4(embalagem_produto):
    return baker.make(
        "ItemCadastro",
        tipo="EMBALAGEM",
        content_type=ContentType.objects.get(model="embalagemproduto"),
        content_object=embalagem_produto,
    )


@pytest.fixture
def usuario():
    return baker.make("perfil.Usuario")


@pytest.fixture
def homologacao_produto_suspenso(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_SUSPENDEU
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def analise_sensorial(homologacao_produto_gpcodae_questionou_escola):
    analise = baker.make(
        "AnaliseSensorial",
        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA,
        homologacao_produto=homologacao_produto_gpcodae_questionou_escola,
    )
    return analise


@pytest.fixture
def reclamacao_respondido_terceirizada(
    reclamacao, homologacao_produto_gpcodae_questionou_escola, analise_sensorial
):
    reclamacao.homologacao_produto = homologacao_produto_gpcodae_questionou_escola
    reclamacao.status = ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
    reclamacao.save()
    return reclamacao


@pytest.fixture
def user_codae_produto(django_user_model, codae):
    email = "test2@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_produto = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf2",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_produto,
        data_inicial=hoje,
        ativo=True,
    )
    return user


@pytest.fixture
def mock_view_de_reclamacao_produto(
    user_codae_produto, reclamacao_respondido_terceirizada
):
    data = {"anexos": [], "justificativa": "Produto vencido."}
    mock_request = Mock()
    mock_request.data = data
    mock_request.user = user_codae_produto

    viewset = ReclamacaoProdutoViewSet()
    viewset.request = mock_request
    viewset.kwargs = {"uuid": "uuid"}
    viewset.get_object = Mock(return_value=reclamacao_respondido_terceirizada)
    viewset.get_serializer = ReclamacaoDeProdutoSerializer

    return mock_request, viewset


@pytest.fixture
def usuario_nutri_supervisao(django_user_model):
    email = "nutrisupervisao@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_supervisao_nutricao = baker.make(
        "Perfil",
        nome=constants.COORDENADOR_SUPERVISAO_NUTRICAO,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )

    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_supervisao_nutricao,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    return user


@pytest.fixture
def mock_view_de_homologacao_produto_painel_gerencial(
    client_autenticado_vinculo_terceirizada,
):
    client, usuario = client_autenticado_vinculo_terceirizada
    mock_request = Mock()
    mock_request.data = {}
    mock_request.user = usuario
    mock_request.query_params = {"page": ["1"], "page_size": ["10"]}

    viewset = HomologacaoProdutoPainelGerencialViewSet()
    viewset.request = mock_request
    viewset.kwargs = {"uuid": "uuid"}
    viewset.get_serializer = HomologacaoProdutoPainelGerencialSerializer

    return mock_request, viewset


@pytest.fixture
def homologacao_e_copia(terceirizada):
    produto_principal = baker.make("produto.Produto", nome="Produto A")
    produto_copia = baker.make("produto.Produto", nome="Produto A")

    homologacao_principal = baker.make(
        "produto.HomologacaoProduto", produto=produto_principal, eh_copia=False
    )
    homologacao_copia = baker.make(
        "produto.HomologacaoProduto", produto=produto_copia, eh_copia=True
    )

    return homologacao_principal


@pytest.fixture
def numero_editais():
    query_params = QueryDict(mutable=True)
    query_params.setlist(
        "editais[]",
        [
            "Edital de Pregão nº 78/sme/2022",
            "Edital de Pregão nº 78/sme/2016",
            "Edital de Pregão nº 41/sme/2017",
        ],
    )
    return query_params


@pytest.fixture
def mock_view_de_produtos(client_autenticado_vinculo_terceirizada, numero_editais):
    client, usuario = client_autenticado_vinculo_terceirizada
    mock_request = Mock()
    mock_request.data = {}
    mock_request.user = usuario
    mock_request.query_params = numero_editais

    viewset = ProdutoViewSet()
    viewset.request = mock_request
    # viewset.kwargs = {"uuid": "uuid"}
    viewset.get_serializer = ProdutoReclamacaoSerializer

    return mock_request, viewset


@pytest.fixture
def reclamacao_produto_pdf(user, escola, hom_produto_com_editais):
    baker.make(
        "ReclamacaoDeProduto",
        # uuid="dd06d200-e2f9-4be7-a304-82831ce93ee1",
        criado_por=user,
        homologacao_produto=hom_produto_com_editais,
        escola=escola,
        status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA,
        reclamacao="Produto com problema de qualidade.",
    )
    return hom_produto_com_editais
