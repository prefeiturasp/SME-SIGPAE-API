import datetime

import pytest
from model_mommy import mommy

from ...dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from ...dados_comuns.models import TemplateMensagem
from ...dieta_especial.models import SolicitacaoDietaEspecial
from ...escola.models import Aluno
from ...perfil.models import Usuario
from ..relatorios import relatorio_dieta_especial_protocolo


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
def template_mensagem_dieta_especial():
    return mommy.make(TemplateMensagem, tipo=TemplateMensagem.DIETA_ESPECIAL, assunto='TESTE DIETA ESPECIAL',
                      template_html='@id @criado_em @status @link')


@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(client, escola, template_mensagem_dieta_especial):
    email = 'escola@admin.com'
    password = DJANGO_ADMIN_PASSWORD
    rf = '1545933'
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf)
    client.login(username=email, password=password)

    perfil_professor = mommy.make(
        'perfil.Perfil', nome='ADMINISTRADOR_UE', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola, perfil=perfil_professor,
               data_inicial=datetime.date.today(), ativo=True)  # ativo

    aluno = mommy.make(Aluno, nome='Roberto Alves da Silva',
                       codigo_eol='123456', data_nascimento='2000-01-01')
    solic = mommy.make(SolicitacaoDietaEspecial,
                       rastro_escola=escola,
                       rastro_terceirizada=escola.lote.terceirizada,
                       aluno=aluno,
                       criado_por=user)
    solic.inicia_fluxo(user=user)

    return solic


@pytest.fixture
def solicitacao_dieta_especial_autorizada(client, escola, solicitacao_dieta_especial_a_autorizar):
    email = 'terceirizada@admin.com'
    password = DJANGO_ADMIN_PASSWORD
    rf = '4545454'
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf)
    client.login(username=email, password=password)

    perfil = mommy.make('perfil.Perfil', nome='TERCEIRIZADA', ativo=False)
    mommy.make('perfil.Vinculo', usuario=user, instituicao=escola.lote.terceirizada, perfil=perfil,
               data_inicial=datetime.date.today(), ativo=True)

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar


@pytest.mark.django_db
def test_relatorio_dieta_especial_protocolo(solicitacao_dieta_especial_autorizada):
    html_string = relatorio_dieta_especial_protocolo(None, solicitacao_dieta_especial_autorizada)

    assert ('Orientações Gerais' in html_string) is True
    assert (solicitacao_dieta_especial_autorizada.orientacoes_gerais in html_string) is True
