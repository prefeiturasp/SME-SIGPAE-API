import datetime
import json
from random import randint, sample

import pytest
from faker import Faker
from model_mommy import mommy

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.models import TemplateMensagem
from ...dados_comuns.utils import convert_base64_to_contentfile
from ...eol_servico.utils import EOLService
from ...escola.models import Aluno
from ...perfil.models import Usuario
from ...produto.models import Produto
from ..models import AlergiaIntolerancia, Alimento, Anexo, ClassificacaoDieta, MotivoNegacao, SolicitacaoDietaEspecial

fake = Faker('pt_BR')
fake.seed(420)


@pytest.fixture
def usuario_admin():
    return mommy.make('Usuario', email='admin@admin.com', is_superuser=True)


@pytest.fixture
def codae():
    return mommy.make('Codae')


@pytest.fixture
def dre_guaianases():
    return mommy.make('DiretoriaRegional', nome='DIRETORIA REGIONAL GUAIANASES')


@pytest.fixture
def escola_dre_guaianases(dre_guaianases):
    lote = mommy.make('Lote')
    return mommy.make('Escola', lote=lote, diretoria_regional=dre_guaianases)


@pytest.fixture
def arquivo_docx_base64():
    return "data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,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"  # noqa


@pytest.fixture
def aluno():
    return mommy.make(Aluno, nome='Roberto Alves da Silva', codigo_eol='123456', data_nascimento='2000-01-01')


@pytest.fixture
def solicitacao_dieta_especial(escola, aluno):
    return mommy.make(SolicitacaoDietaEspecial,
                      rastro_escola=escola,
                      aluno=aluno)


@pytest.fixture
def solicitacao_dieta_especial_outra_dre(escola_dre_guaianases, aluno):
    return mommy.make(SolicitacaoDietaEspecial,
                      rastro_escola=escola_dre_guaianases,
                      aluno=aluno)


@pytest.fixture
def anexo_docx(arquivo_docx_base64, solicitacao_dieta_especial):
    return mommy.make(Anexo,
                      solicitacao_dieta_especial=solicitacao_dieta_especial,
                      arquivo=convert_base64_to_contentfile(
                          arquivo_docx_base64),
                      nome='arquivo-supimpa.docx')


@pytest.fixture(scope='function', params=[
    'teste.jpg',
    'borboleta.png',
    'arquivo_bacana.pdf',
    'arquivo_top.docx',
    'arquivo_legal.doc'
])
def nomes_arquivos_validos(request):
    return request.param


@pytest.fixture(scope='function', params=[
    'teste.zip',
    'borboleta.py',
    'arquivo_bacana.js',
    'arquivo_top.tar.gz',
    'arquivo_legal.exe'
])
def nomes_arquivos_invalidos(request):
    return request.param


@pytest.fixture
def alergias_intolerancias():
    mommy.make(AlergiaIntolerancia, _quantity=2)
    return AlergiaIntolerancia.objects.all()


@pytest.fixture
def classificacoes_dieta():
    mommy.make(ClassificacaoDieta, _quantity=3)
    return ClassificacaoDieta.objects.all()


@pytest.fixture
def motivos_negacao():
    mommy.make(MotivoNegacao, _quantity=4)
    return MotivoNegacao.objects.all()


@pytest.fixture
def alimentos():
    mommy.make(Alimento, _quantity=6)
    return Alimento.objects.all()


@pytest.fixture
def produtos():
    mommy.make(Produto, _quantity=6)
    return Produto.objects.all()


@pytest.fixture
def substituicoes(alimentos, produtos):
    substituicoes = []
    ids_produtos = [p.uuid for p in produtos]
    for _ in range(randint(3, 5)):
        substituicoes.append({
            'alimento': alimentos[randint(0, len(alimentos) - 1)].id,
            'tipo': 'I' if randint(0, 1) == 1 else 'S',
            'substitutos': sample(ids_produtos, randint(1, 4))
        })
    return substituicoes


@pytest.fixture
def payload_autorizar(alergias_intolerancias, classificacoes_dieta, substituicoes, protocolo_padrao_dieta_especial):
    return {
        'classificacao': classificacoes_dieta[0].id,
        'alergias_intolerancias': [
            alergias_intolerancias[0].id
        ],
        'registro_funcional_nutricionista':
            'ELABORADO por USUARIO NUTRICIONISTA CODAE - CRN null',
        'substituicoes': substituicoes,
        'informacoes_adicionais': 'Um texto bem grandão',
        'protocolo_padrao': protocolo_padrao_dieta_especial.uuid,
        'nome_protocolo': protocolo_padrao_dieta_especial.nome_protocolo,
        'orientacoes_gerais': 'Um texto grande aqui'
    }


@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(client, escola, template_mensagem_dieta_especial):
    email = 'escola@admin.com'
    password = 'adminadmin'
    rf = '1545933'
    user = Usuario.objects.create_user(
        password=password, email=email, registro_funcional=rf)
    client.login(email=email, password=password)

    perfil_professor = mommy.make(
        'perfil.Perfil', nome='ADMINISTRADOR_ESCOLA', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola, perfil=perfil_professor,
               data_inicial=datetime.date.today(), ativo=True)  # ativo

    aluno = mommy.make(Aluno, nome='Roberto Alves da Silva',
                       codigo_eol='123456', data_nascimento='2000-01-01')
    solic = mommy.make(SolicitacaoDietaEspecial,
                       rastro_escola=escola,
                       aluno=aluno,
                       criado_por=user)
    solic.inicia_fluxo(user=user)

    return solic


@pytest.fixture
def solicitacao_dieta_especial_autorizada(client, escola, solicitacao_dieta_especial_a_autorizar):
    email = 'terceirizada@admin.com'
    password = 'adminadmin'
    rf = '4545454'
    user = Usuario.objects.create_user(
        password=password, email=email, registro_funcional=rf)
    client.login(email=email, password=password)

    perfil = mommy.make('perfil.Perfil', nome='TERCEIRIZADA', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil,
               data_inicial=datetime.date.today(), ativo=True)

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.fixture
def solicitacao_dieta_especial_escola_solicitou_inativacao(client, escola, solicitacao_dieta_especial_autorizada):
    email = 'terceirizada2@admin.com'
    password = 'adminadmin'
    rf = '4545455'
    user = Usuario.objects.create_user(
        password=password, email=email, registro_funcional=rf)
    client.login(email=email, password=password)

    perfil = mommy.make('perfil.Perfil', nome='TERCEIRIZADA', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil,
               data_inicial=datetime.date.today(), ativo=True)

    solicitacao_dieta_especial_autorizada.inicia_fluxo_inativacao(user=user)

    return solicitacao_dieta_especial_autorizada


@pytest.fixture
def solicitacao_dieta_especial_codae_autorizou_inativacao(client,
                                                          escola,
                                                          solicitacao_dieta_especial_escola_solicitou_inativacao):
    email = 'terceirizada3@admin.com'
    password = 'adminadmin'
    rf = '4545456'
    user = Usuario.objects.create_user(
        password=password, email=email, registro_funcional=rf)
    client.login(email=email, password=password)

    perfil = mommy.make('perfil.Perfil', nome='TERCEIRIZADA', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil,
               data_inicial=datetime.date.today(), ativo=True)

    solicitacao_dieta_especial_escola_solicitou_inativacao.codae_autoriza_inativacao(
        user=user)

    return solicitacao_dieta_especial_escola_solicitou_inativacao


@pytest.fixture
def template_mensagem_dieta_especial():
    return mommy.make(TemplateMensagem, tipo=TemplateMensagem.DIETA_ESPECIAL, assunto='TESTE DIETA ESPECIAL',
                      template_html='@id @criado_em @status @link')


@pytest.fixture
def escola():
    terceirizada = mommy.make('Terceirizada')
    lote = mommy.make('Lote', terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        'DiretoriaRegional', nome='DIRETORIA REGIONAL IPIRANGA')
    escola = mommy.make(
        'Escola',
        lote=lote,
        nome='EMEF JOAO MENDES',
        codigo_eol='000546',
        diretoria_regional=diretoria_regional
    )
    return escola


@pytest.fixture
def client_autenticado_vinculo_escola_dieta(client, django_user_model, escola, template_mensagem_dieta_especial):
    email = 'test@test.com'
    password = 'bar'
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_diretor = mommy.make('Perfil', nome='DIRETOR', ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola, perfil=perfil_diretor,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_dieta(client, django_user_model, escola, codae, template_mensagem_dieta_especial):
    email = 'test@test.com'
    password = 'bar'
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_dieta_especial = mommy.make('Perfil', nome=constants.ADMINISTRADOR_DIETA_ESPECIAL,
                                             ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_admin_dieta_especial,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_gestao_alimentacao_dieta(client, django_user_model, escola, codae,
                                                              template_mensagem_dieta_especial):
    email = 'test@test.com'
    password = 'bar'
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_admin_gestao_alimentacao = mommy.make('Perfil', nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                                                 ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=codae, perfil=perfil_admin_gestao_alimentacao,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_terceirizada_dieta(client, django_user_model, escola, codae,
                                                  template_mensagem_dieta_especial):
    email = 'test@test.com'
    password = 'bar'
    user = django_user_model.objects.create_user(password=password, email=email,
                                                 registro_funcional='8888888')
    perfil_nutri_admin = mommy.make('Perfil', nome=constants.NUTRI_ADMIN_RESPONSAVEL,
                                    ativo=True)
    hoje = datetime.date.today()
    mommy.make('Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil_nutri_admin,
               data_inicial=hoje, ativo=True)
    client.login(email=email, password=password)
    return client


@pytest.fixture
def solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas(escola, aluno):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)

    return [
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
                   aluno=aluno,
                   rastro_escola=escola),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO, rastro_escola=escola),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
                   aluno=aluno,
                   rastro_escola=escola),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
                   rastro_escola=escola,
                   aluno=aluno,
                   data_termino=ontem),
        mommy.make(SolicitacaoDietaEspecial,
                   rastro_escola=escola,
                   aluno=aluno,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
                   rastro_escola=escola,
                   aluno=aluno,
                   data_termino=ontem)
    ]


@pytest.fixture(params=[
    DietaEspecialWorkflow.CODAE_AUTORIZADO,
    DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
    DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
    DietaEspecialWorkflow.CODAE_NEGOU_INATIVACAO
])
def solicitacao_dieta_especial_autorizada_ativa(request, aluno, escola):
    return mommy.make(SolicitacaoDietaEspecial,
                      status=request.param,
                      rastro_escola=escola,
                      aluno=aluno)


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior(aluno, escola):
    hoje = datetime.date.today()
    amanha = hoje + datetime.timedelta(days=1)
    return [
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=hoje),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=hoje),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=hoje),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=amanha),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=amanha),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=amanha),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem_ativas(aluno, escola):
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    return [
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
                   ativo=True,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                   ativo=True,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
                   ativo=True,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem_inativas(aluno, escola):
    ontem = datetime.date.today() - datetime.timedelta(days=1)
    return [
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.CODAE_AUTORIZADO,
                   ativo=False,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                   ativo=False,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
        mommy.make(SolicitacaoDietaEspecial,
                   status=DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
                   ativo=False,
                   aluno=aluno,
                   rastro_escola=escola,
                   data_termino=ontem),
    ]


@pytest.fixture
def solicitacoes_dieta_especial_dt_termino_ontem(solicitacoes_dieta_especial_dt_termino_ontem_ativas,
                                                 solicitacoes_dieta_especial_dt_termino_ontem_inativas):
    return solicitacoes_dieta_especial_dt_termino_ontem_ativas + solicitacoes_dieta_especial_dt_termino_ontem_inativas


@pytest.fixture
def solicitacoes_dieta_especial_com_data_termino(solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior,
                                                 solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas,
                                                 solicitacoes_dieta_especial_dt_termino_ontem):
    solicitacoes = [] + solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas
    solicitacoes += solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior
    solicitacoes += solicitacoes_dieta_especial_dt_termino_ontem
    return solicitacoes


@pytest.fixture
def periodo_escolar_integral():
    return mommy.make('PeriodoEscolar', nome='INTEGRAL')


@pytest.fixture
def eolservice_get_informacoes_escola_turma_aluno(monkeypatch):
    js_path = 'sme_terceirizadas/dieta_especial/__tests__/massa_eolservice_get_informacoes_escola_turma_aluno.json'
    with open(js_path) as jsfile:
        js = json.load(jsfile)
    return monkeypatch.setattr(
        EOLService,
        'get_informacoes_escola_turma_aluno',
        lambda x: js['results']
    )


@pytest.fixture
def log_dietas_ativas_canceladas_automaticamente(solicitacao_dieta_especial_autorizada_ativa):
    return mommy.make(
        'LogDietasAtivasCanceladasAutomaticamente',
        dieta=solicitacao_dieta_especial_autorizada_ativa,
        codigo_eol_aluno='6595803',
        nome_aluno='GUILHERME RODRIGUES DA HORA',
        codigo_eol_escola_origem='019871',
        nome_escola_origem='EMEF PERICLES EUGENIO DA SILVA RAMOS',
        codigo_eol_escola_destino='018210',
        nome_escola_destino='EMEFM DARCY RIBEIRO',
    )


@pytest.fixture
def protocolo_padrao_dieta_especial():
    return mommy.make(
        'ProtocoloPadraoDietaEspecial',
        nome_protocolo='ALERGIA A AVEIA',
        status='LIBERADO',
    )
