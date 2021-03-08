import datetime

import pytest
from faker import Faker
from model_mommy import mommy

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from ...dados_comuns.models import TemplateMensagem

fake = Faker('pt-Br')
fake.seed(420)


@pytest.fixture
def escola():
    terceirizada = mommy.make('Terceirizada')
    lote = mommy.make('Lote', terceirizada=terceirizada)
    diretoria_regional = mommy.make('DiretoriaRegional', nome='DIRETORIA REGIONAL IPIRANGA',
                                    uuid='9640fef4-a068-474e-8979-2e1b2654357a')
    return mommy.make('Escola', lote=lote, diretoria_regional=diretoria_regional)


@pytest.fixture
def codae():
    return mommy.make('Codae')


@pytest.fixture
def template_homologacao_produto():
    return mommy.make(TemplateMensagem, assunto='TESTE',
                      tipo=TemplateMensagem.HOMOLOGACAO_PRODUTO,
                      template_html='@id @criado_em @status @link')


@pytest.fixture
def client_autenticado_vinculo_codae_produto(client, django_user_model, escola, codae, template_homologacao_produto):
    email = 'test@test.com'
    password = 'bar'
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_gestao_produto = mommy.make('Perfil', nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
                                             ativo=True,
                                             uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_admin_gestao_produto,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_terceirizada(client, django_user_model, escola, template_homologacao_produto):
    email = 'test@test.com'
    password = 'bar'
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_terceirizada = mommy.make('Perfil', nome=constants.ADMINISTRADOR_TERCEIRIZADA,
                                           ativo=True,
                                           uuid='41c20c8b-7e57-41ed-9433-ccb95e8afaf0')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=tecerizada, perfil=perfil_admin_terceirizada,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def user(django_user_model):
    email = 'test@test1.com'
    password = 'bar'
    return django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888881')


@pytest.fixture
def homologacao_produto(escola, template_homologacao_produto, user):
    perfil_admin_terceirizada = mommy.make('Perfil', nome=constants.ADMINISTRADOR_TERCEIRIZADA,
                                           ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil_admin_terceirizada,
               data_inicial=hoje, ativo=True)
    produto = mommy.make('Produto', criado_por=user)
    homologacao_produto = mommy.make('HomologacaoDoProduto',
                                     produto=produto,
                                     rastro_terceirizada=escola.lote.terceirizada,
                                     criado_por=user,
                                     criado_em=datetime.datetime.utcnow())
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
    homologacao_produto.status = HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def client_autenticado_vinculo_terceirizada_homologacao(client, django_user_model, escola):
    email = 'test@test.com'
    password = 'bar'
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_diretor = mommy.make('Perfil', nome=constants.ADMINISTRADOR_TERCEIRIZADA,
                                ativo=True,
                                uuid='41c20c8b-7e57-41ed-9433-ccb95e8afaf0')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=tecerizada, perfil=perfil_diretor,
               data_inicial=hoje, ativo=True)
    produto = mommy.make('Produto', criado_por=user)
    homologacao_produto = mommy.make('HomologacaoDoProduto',
                                     produto=produto,
                                     rastro_terceirizada=escola.lote.terceirizada,
                                     criado_por=user,
                                     criado_em=datetime.datetime.utcnow(),
                                     uuid='774ad907-d871-4bfd-b1aa-d4e0ecb6c01f')
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    homologacao_produto.save()

    homologacao_produto1 = mommy.make('HomologacaoDoProduto',
                                      produto=produto,
                                      rastro_terceirizada=escola.lote.terceirizada,
                                      criado_por=user,
                                      criado_em=datetime.datetime.utcnow(),
                                      uuid='774ad907-d871-4bfd-b1aa-d4e0ecb6c05a')
    homologacao_produto1.status = HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    homologacao_produto1.save()
    client.login(email=email, password=password)
    return client, homologacao_produto, homologacao_produto1


@pytest.fixture
def protocolo1():
    return mommy.make('ProtocoloDeDietaEspecial', nome='Protocolo1')


@pytest.fixture
def protocolo2():
    return mommy.make('ProtocoloDeDietaEspecial', nome='Protocolo2')


@pytest.fixture
def protocolo3():
    return mommy.make('ProtocoloDeDietaEspecial', nome='Protocolo3')


@pytest.fixture
def marca1():
    return mommy.make('Marca', nome='Marca1')


@pytest.fixture
def marca2():
    return mommy.make('Marca', nome='Marca2')


@pytest.fixture
def fabricante():
    return mommy.make('Fabricante')


@pytest.fixture
def produto(user, protocolo1, protocolo2, marca1, fabricante):
    return mommy.make('Produto',
                      criado_por=user,
                      eh_para_alunos_com_dieta=True,
                      componentes='Componente1, Componente2',
                      tem_aditivos_alergenicos=False,
                      tipo='Tipo1',
                      embalagem='Embalagem X',
                      prazo_validade='Alguns dias',
                      info_armazenamento='Guardem bem',
                      outras_informacoes='Produto do bom',
                      numero_registro='123123123',
                      porcao='5 cuias',
                      unidade_caseira='Unidade3',
                      nome='Produto1',
                      fabricante=fabricante,
                      marca=marca1,
                      protocolos=[
                          protocolo1,
                          protocolo2,
                      ])


@pytest.fixture
def info_nutricional1():
    return mommy.make('InformacaoNutricional', nome='CALORIAS')


@pytest.fixture
def info_nutricional2():
    return mommy.make('InformacaoNutricional', nome='LACTOSE')


@pytest.fixture
def info_nutricional3():
    return mommy.make('InformacaoNutricional', nome='COLESTEROL')


@pytest.fixture
def info_nutricional_produto1(produto, info_nutricional1):
    return mommy.make(
        'InformacoesNutricionaisDoProduto',
        produto=produto,
        informacao_nutricional=info_nutricional1,
        quantidade_porcao='1',
        valor_diario='2')


@pytest.fixture
def info_nutricional_produto2(produto, info_nutricional2):
    return mommy.make(
        'InformacoesNutricionaisDoProduto',
        produto=produto,
        informacao_nutricional=info_nutricional2,
        quantidade_porcao='3',
        valor_diario='4')


@pytest.fixture
def info_nutricional_produto3(produto, info_nutricional3):
    return mommy.make(
        'InformacoesNutricionaisDoProduto',
        produto=produto,
        informacao_nutricional=info_nutricional3,
        quantidade_porcao='5',
        valor_diario='6')


@pytest.fixture
def imagem_produto1(produto):
    return mommy.make('ImagemDoProduto', produto=produto, nome='Imagem1')


@pytest.fixture
def imagem_produto2(produto):
    return mommy.make('ImagemDoProduto', produto=produto, nome='Imagem2')
