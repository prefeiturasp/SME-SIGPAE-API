import datetime

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from model_mommy import mommy

from ...dados_comuns import constants
from ...dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow, ReclamacaoProdutoWorkflow
from ...dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ...escola.models import DiretoriaRegional, TipoGestao
from ...terceirizada.models import Contrato
from ..models import ProdutoEdital

fake = Faker('pt-Br')
fake.seed(420)


@pytest.fixture
def escola():
    terceirizada = mommy.make('Terceirizada')
    lote = mommy.make('Lote', terceirizada=terceirizada)
    diretoria_regional = mommy.make('DiretoriaRegional', nome='DIRETORIA REGIONAL IPIRANGA',
                                    uuid='9640fef4-a068-474e-8979-2e1b2654357a')
    contato = mommy.make('Contato', email='test@test2.com')

    return mommy.make('Escola', uuid='b00b2cf4-286d-45ba-a18b-9ffe4e8d8dfd', lote=lote,
                      diretoria_regional=diretoria_regional, contato=contato)


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
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_gestao_produto = mommy.make('Perfil', nome=constants.ADMINISTRADOR_GESTAO_PRODUTO,
                                             ativo=True,
                                             uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_admin_gestao_produto,
               data_inicial=hoje, ativo=True)
    client.login(username=email, password=password)
    return client


@pytest.fixture
def produtos_edital_41(escola):
    edital = mommy.make('Edital', numero='Edital de Pregão nº 41/sme/2017', uuid='12288b47-9d27-4089-8c2e-48a6061d83ea')
    mommy.make('Edital', numero='Edital de Pregão nº 78/sme/2016', uuid='b30a2102-2ae0-404d-8a56-8e5ecd73f868')
    edital_3 = mommy.make('Edital', numero='Edital de Pregão nº 78/sme/2022',
                          uuid='131f4000-3e31-44f1-9ba5-e7df001a8426')
    marca_1 = mommy.make('Marca', nome='NAMORADOS')
    marca_2 = mommy.make('Marca', nome='TIO JOÃO')
    produto_1 = mommy.make('Produto', nome='ARROZ', marca=marca_1)
    produto_2 = mommy.make('Produto', nome='ARROZ', marca=marca_2)
    homologacao_p1 = mommy.make('HomologacaoProduto',
                                produto=produto_1,
                                rastro_terceirizada=escola.lote.terceirizada,
                                status=HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO)
    homologacao_p2 = mommy.make('HomologacaoProduto',
                                produto=produto_2,
                                rastro_terceirizada=escola.lote.terceirizada,
                                status=HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO)
    mommy.make('LogSolicitacoesUsuario',
               uuid_original=homologacao_p1.uuid,
               status_evento=22,  # CODAE_HOMOLOGADO
               solicitacao_tipo=10)  # HOMOLOGACAO_PRODUTO
    mommy.make('LogSolicitacoesUsuario',
               uuid_original=homologacao_p2.uuid,
               status_evento=22,  # CODAE_HOMOLOGADO
               solicitacao_tipo=10)  # HOMOLOGACAO_PRODUTO
    mommy.make('ProdutoEdital', produto=produto_1, edital=edital, tipo_produto='Comum',
               uuid='0f81a49b-0836-42d5-af9e-12cbd7ca76a8')
    mommy.make('ProdutoEdital', produto=produto_1, edital=edital_3, tipo_produto='Comum',
               uuid='e42e3b97-6853-4327-841d-34292c33963c')
    mommy.make('ProdutoEdital', produto=produto_2, edital=edital, tipo_produto='Comum',
               uuid='38cdf4a8-6621-4248-8f5c-378d1bdbfb71')


@pytest.fixture
def client_autenticado_vinculo_terceirizada(client, django_user_model, escola, template_homologacao_produto):
    email = 'test@test.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_terceirizada = mommy.make('Perfil', nome=constants.ADMINISTRADOR_EMPRESA,
                                           ativo=True,
                                           uuid='41c20c8b-7e57-41ed-9433-ccb95e8afaf0')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=tecerizada, perfil=perfil_admin_terceirizada,
               data_inicial=hoje, ativo=True)
    client.login(username=email, password=password)
    return client


@pytest.fixture
def user(django_user_model):
    email = 'test@test1.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    return django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888881')


@pytest.fixture
def client_autenticado_vinculo_terceirizada_homologacao(client, django_user_model, escola):
    email = 'test@test.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    tecerizada = escola.lote.terceirizada
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_diretor = mommy.make('Perfil', nome=constants.ADMINISTRADOR_EMPRESA,
                                ativo=True,
                                uuid='41c20c8b-7e57-41ed-9433-ccb95e8afaf0')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=tecerizada, perfil=perfil_diretor,
               data_inicial=hoje, ativo=True)
    produto = mommy.make('Produto', criado_por=user)
    homologacao_produto = mommy.make('HomologacaoProduto',
                                     produto=produto,
                                     rastro_terceirizada=escola.lote.terceirizada,
                                     criado_por=user,
                                     criado_em=datetime.datetime.utcnow(),
                                     uuid='774ad907-d871-4bfd-b1aa-d4e0ecb6c01f')
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    homologacao_produto.save()
    client.login(username=email, password=password)
    return client, homologacao_produto


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
    return mommy.make('Fabricante', nome='Fabricante1')


@pytest.fixture
def unidade_medida():
    return mommy.make('UnidadeMedida', nome='Litros')


@pytest.fixture
def embalagem_produto():
    return mommy.make('EmbalagemProduto', nome='Bag')


@pytest.fixture
def terceirizada():
    return mommy.make('Terceirizada',
                      contatos=[mommy.make('dados_comuns.Contato')],
                      make_m2m=True,
                      nome_fantasia='Alimentos SA'
                      )


@pytest.fixture
def edital():
    return mommy.make('Edital',
                      uuid='617a8139-02a9-4801-a197-622aa20795b9',
                      numero='Edital de Pregão nº 56/SME/2016',
                      tipo_contratacao='Teste',
                      processo='Teste',
                      objeto='Teste')


@pytest.fixture
def produto(user, protocolo1, protocolo2, marca1, fabricante):
    produto = mommy.make('Produto',
                         uuid='a37bcf3f-a288-44ae-87ae-dbec181a34d4',
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
    return produto


@pytest.fixture
def produto_com_editais(produto):
    edital = mommy.make('Edital', numero='Edital de Pregão nº 41/sme/2017', uuid='12288b47-9d27-4089-8c2e-48a6061d83ea')
    edital_2 = mommy.make('Edital', numero='Edital de Pregão nº 78/sme/2016',
                          uuid='b30a2102-2ae0-404d-8a56-8e5ecd73f868')
    edital_3 = mommy.make('Edital', numero='Edital de Pregão nº 78/sme/2022',
                          uuid='131f4000-3e31-44f1-9ba5-e7df001a8426')
    mommy.make('ProdutoEdital', produto=produto, edital=edital, tipo_produto='Comum',
               uuid='0f81a49b-0836-42d5-af9e-12cbd7ca76a8')
    mommy.make('ProdutoEdital', produto=produto, edital=edital_2, tipo_produto='Comum',
               uuid='e42e3b97-6853-4327-841d-34292c33963c')
    mommy.make('ProdutoEdital', produto=produto, edital=edital_3, tipo_produto='Comum',
               uuid='3b4f59eb-a686-49e9-beab-3514a93e3184')
    return produto


@pytest.fixture
def hom_produto_com_editais(escola, template_homologacao_produto, user, produto_com_editais):
    perfil_admin_terceirizada = mommy.make('Perfil', nome=constants.ADMINISTRADOR_EMPRESA,
                                           ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil_admin_terceirizada,
               data_inicial=hoje, ativo=True)
    homologacao_produto = mommy.make('HomologacaoProduto',
                                     produto=produto_com_editais,
                                     rastro_terceirizada=escola.lote.terceirizada,
                                     criado_por=user,
                                     criado_em=datetime.datetime.utcnow())
    mommy.make('LogSolicitacoesUsuario',
               uuid_original=homologacao_produto.uuid,
               status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
               solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO)
    mommy.make('ReclamacaoDeProduto',
               homologacao_produto=homologacao_produto,
               escola=escola)
    return homologacao_produto


@pytest.fixture
def hom_copia(hom_produto_com_editais):
    produto_copia = hom_produto_com_editais.cria_copia_produto()
    homologacao_copia = hom_produto_com_editais.cria_copia_homologacao_produto(produto_copia)
    mommy.make('LogSolicitacoesUsuario',
               uuid_original=homologacao_copia.uuid,
               status_evento=LogSolicitacoesUsuario.CODAE_PENDENTE_HOMOLOGACAO,
               solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO)
    mommy.make('AnaliseSensorial',
               homologacao_produto=homologacao_copia)
    resposta_analise = mommy.make(
        'RespostaAnaliseSensorial',
        homologacao_produto=homologacao_copia
    )
    mommy.make('AnexoRespostaAnaliseSensorial',
               resposta_analise_sensorial=resposta_analise)
    return homologacao_copia


@pytest.fixture
def hom_copia_pendente_homologacao(hom_copia):
    hom_copia.status = HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    hom_copia.save()
    return hom_copia


@pytest.fixture
def homologacoes_produto(produto, terceirizada):
    hom = mommy.make('HomologacaoProduto',
                     produto=produto,
                     rastro_terceirizada=terceirizada,
                     status=HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO)
    mommy.make('LogSolicitacoesUsuario', uuid_original=hom.uuid)
    return hom


@pytest.fixture
def vinculo_produto_edital(produto, edital):
    produto_edital = mommy.make('ProdutoEdital',
                                uuid='fae48de3-0d2f-4eb1-8b3e-0ddf7d45ee64',
                                produto=produto,
                                edital=edital,
                                outras_informacoes='Teste 1',
                                ativo=True,
                                tipo_produto=ProdutoEdital.DIETA_ESPECIAL)
    return produto_edital


@pytest.fixture
def client_autenticado_da_terceirizada(client, django_user_model, terceirizada):
    email = 'foo@codae.com'
    password = DJANGO_ADMIN_PASSWORD
    perfil_adm_terc = mommy.make('Perfil', nome='TERCEIRIZADA', ativo=True)
    usuario = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                    registro_funcional='123456')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=usuario, instituicao=terceirizada, perfil=perfil_adm_terc,
               data_inicial=hoje, ativo=True)
    client.login(username=email, password=password)
    return client


@pytest.fixture
def tipo_gestao():
    return mommy.make(TipoGestao,
                      nome='TERC TOTAL')


@pytest.fixture
def diretoria_regional(tipo_gestao):
    dre = mommy.make(DiretoriaRegional,
                     nome=fake.name(),
                     uuid='d305add2-f070-4ad3-8c17-ba9664a7c655',
                     make_m2m=True)
    mommy.make('Escola', diretoria_regional=dre, tipo_gestao=tipo_gestao)
    mommy.make('Escola', diretoria_regional=dre, tipo_gestao=tipo_gestao)
    mommy.make('Escola', diretoria_regional=dre, tipo_gestao=tipo_gestao)
    return dre


@pytest.fixture
def contrato(diretoria_regional, edital):
    return mommy.make(Contrato, numero='1', processo='12345', diretorias_regionais=[diretoria_regional], edital=edital)


@pytest.fixture
def client_autenticado_da_dre(client, django_user_model, diretoria_regional):
    email = 'user@dre.com'
    password = 'admin@123'
    perfil_adm_dre = mommy.make('Perfil', nome='ADM_DRE', ativo=True)
    usuario = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                    registro_funcional='123456')
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=usuario, instituicao=diretoria_regional, perfil=perfil_adm_dre,
               data_inicial=hoje, ativo=True)
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_da_escola(client, django_user_model, escola):
    email = 'user@escola.com'
    password = DJANGO_ADMIN_PASSWORD
    perfil_diretor = mommy.make('Perfil', nome='DIRETOR_UE', ativo=True)
    usuario = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                    registro_funcional='123456',
                                                    )
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=usuario, instituicao=escola, perfil=perfil_diretor,
               data_inicial=hoje, ativo=True)
    client.login(username=email, password=password)
    return client


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
def especificacao_produto1(produto, unidade_medida, embalagem_produto):
    return mommy.make('EspecificacaoProduto',
                      volume=1.5,
                      produto=produto,
                      unidade_de_medida=unidade_medida,
                      embalagem_produto=embalagem_produto)


@pytest.fixture
def produto_edital(user):
    return mommy.make('NomeDeProdutoEdital',
                      nome='PRODUTO TESTE',
                      ativo=True,
                      criado_por=user)


@pytest.fixture
def produto_logistica(user):
    return mommy.make('NomeDeProdutoEdital',
                      nome='PRODUTO TESTE',
                      tipo_produto='LOGISTICA',
                      ativo=True,
                      criado_por=user)


@pytest.fixture
def arquivo():
    return SimpleUploadedFile(f'planilha-teste.pdf', bytes(f'CONTEUDO TESTE TESTE TESTE', encoding='utf-8'))


@pytest.fixture
def imagem_produto1(produto, arquivo):
    return mommy.make('ImagemDoProduto', produto=produto, nome='Imagem1', arquivo=arquivo)


@pytest.fixture
def imagem_produto2(produto, arquivo):
    return mommy.make('ImagemDoProduto', produto=produto, nome='Imagem2', arquivo=arquivo)


@pytest.fixture
def client_autenticado_vinculo_escola_ue(client, django_user_model, escola):
    email = 'test@test.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')

    perfil_diretor = mommy.make('Perfil', nome='DIRETOR_UE', ativo=True, uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')

    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola, perfil=perfil_diretor,
               data_inicial=hoje, ativo=True)
    mommy.make(TemplateMensagem, assunto='TESTE',
               tipo=TemplateMensagem.DIETA_ESPECIAL,
               template_html='@id @criado_em @status @link')
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_escola_nutrisupervisor(
        client,
        django_user_model,
        escola):

    email = 'test@test.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')

    perfil_nutri = mommy.make('Perfil', nome='COORDENADOR_SUPERVISAO_NUTRICAO',
                              ativo=True, uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')

    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola, perfil=perfil_nutri,
               data_inicial=hoje, ativo=True)
    mommy.make(TemplateMensagem, assunto='TESTE',
               tipo=TemplateMensagem.DIETA_ESPECIAL,
               template_html='@id @criado_em @status @link')
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_nutrisupervisor(
        client,
        django_user_model,
        codae):

    email = 'test@test.com'
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(username=email, password=password, email=email,
                                                 registro_funcional='8888888')

    perfil_nutri = mommy.make('Perfil', nome='COORDENADOR_SUPERVISAO_NUTRICAO',
                              ativo=True, uuid='41c20c8b-7e57-41ed-9433-ccb92e8afaf1')

    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_nutri,
               data_inicial=hoje, ativo=True)
    assert user.tipo_usuario == constants.TIPO_USUARIO_NUTRISUPERVISOR
    mommy.make(TemplateMensagem, assunto='TESTE',
               tipo=TemplateMensagem.DIETA_ESPECIAL,
               template_html='@id @criado_em @status @link')
    client.login(username=email, password=password)
    return client


@pytest.fixture
def homologacao_produto(escola, template_homologacao_produto, user, produto):
    perfil_admin_terceirizada = mommy.make('Perfil', nome=constants.ADMINISTRADOR_EMPRESA,
                                           ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil_admin_terceirizada,
               data_inicial=hoje, ativo=True)
    homologacao_produto = mommy.make('HomologacaoProduto',
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
def reclamacao(homologacao_produto_escola_ou_nutri_reclamou, escola, user):
    reclamacao = mommy.make('ReclamacaoDeProduto',
                            homologacao_produto=homologacao_produto_escola_ou_nutri_reclamou,
                            escola=escola,
                            reclamante_registro_funcional='23456789',
                            reclamante_cargo='Cargo',
                            reclamante_nome='Anderson',
                            criado_por=user,
                            criado_em=datetime.datetime.utcnow())
    return reclamacao


@pytest.fixture
def homologacao_produto_gpcodae_questionou_escola(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_UE
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_gpcodae_questionou_nutrisupervisor(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_QUESTIONOU_NUTRISUPERVISOR
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def homologacao_produto_rascunho(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.RASCUNHO
    homologacao_produto.save()
    return homologacao_produto


@pytest.fixture
def reclamacao_ue(homologacao_produto_gpcodae_questionou_escola, escola, user):
    reclamacao = mommy.make('ReclamacaoDeProduto',
                            homologacao_produto=homologacao_produto_gpcodae_questionou_escola,
                            escola=escola,
                            reclamante_registro_funcional='23456788',
                            reclamante_cargo='Cargo',
                            reclamante_nome='Arthur',
                            criado_por=user,
                            criado_em=datetime.datetime.utcnow(),
                            status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE)
    return reclamacao


@pytest.fixture
def reclamacao_nutrisupervisor(homologacao_produto_gpcodae_questionou_nutrisupervisor, escola, user):
    reclamacao = mommy.make('ReclamacaoDeProduto',
                            homologacao_produto=homologacao_produto_gpcodae_questionou_nutrisupervisor,
                            escola=escola,
                            reclamante_registro_funcional='8888888',
                            reclamante_cargo='Cargo',
                            reclamante_nome='Arthur',
                            criado_por=user,
                            criado_em=datetime.datetime.utcnow(),
                            status=ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR)
    return reclamacao


@pytest.fixture
def item_cadastrado_1(marca1):
    return mommy.make('ItemCadastro',
                      tipo='MARCA',
                      content_type=ContentType.objects.get(model='marca'),
                      content_object=marca1)


@pytest.fixture
def item_cadastrado_2(fabricante):
    return mommy.make('ItemCadastro',
                      tipo='FABRICANTE',
                      content_type=ContentType.objects.get(model='fabricante'),
                      content_object=fabricante)


@pytest.fixture
def item_cadastrado_3(unidade_medida):
    return mommy.make('ItemCadastro',
                      tipo='UNIDADE_MEDIDA',
                      content_type=ContentType.objects.get(model='unidademedida'),
                      content_object=unidade_medida)


@pytest.fixture
def item_cadastrado_4(embalagem_produto):
    return mommy.make('ItemCadastro',
                      tipo='EMBALAGEM',
                      content_type=ContentType.objects.get(model='embalagemproduto'),
                      content_object=embalagem_produto)


@pytest.fixture
def usuario():
    return mommy.make('perfil.Usuario')


@pytest.fixture
def homologacao_produto_suspenso(homologacao_produto):
    homologacao_produto.status = HomologacaoProdutoWorkflow.CODAE_SUSPENDEU
    homologacao_produto.save()
    return homologacao_produto
