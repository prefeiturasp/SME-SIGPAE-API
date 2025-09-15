import datetime

import pytest
from faker import Faker
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import TemplateMensagem

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def codae():
    return baker.make("Codae")


@pytest.fixture
def tipo_alimentacao():
    return baker.make("cardapio.TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return baker.make("cardapio.TipoAlimentacao", nome="Lanche Emergencial")


@pytest.fixture
def dre_guaianases():
    return baker.make("DiretoriaRegional", nome="DIRETORIA REGIONAL GUAIANASES")


@pytest.fixture
def escola_dre_guaianases(dre_guaianases):
    lote = baker.make("Lote")
    return baker.make("Escola", lote=lote, diretoria_regional=dre_guaianases)


@pytest.fixture
def periodo_manha():
    return baker.make(
        "escola.PeriodoEscolar",
        nome="MANHA",
        uuid="42325516-aebd-4a3d-97c0-2a77c317c6be",
    )


@pytest.fixture
def periodo_tarde():
    return baker.make(
        "escola.PeriodoEscolar",
        nome="TARDE",
        uuid="88966d6a-f9d5-4986-9ffb-25b6f41b0795",
    )


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
def escola_com_vinculo_alimentacao(
    escola, periodo_manha, tipo_alimentacao, tipo_alimentacao_lanche_emergencial
):
    baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_manha,
        tipo_unidade_escolar=escola.tipo_unidade,
        tipos_alimentacao=[tipo_alimentacao, tipo_alimentacao_lanche_emergencial],
    )
    return escola


@pytest.fixture
def escola_com_dias_letivos(escola_com_vinculo_alimentacao):
    baker.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-18",
        dia_letivo=True,
    )
    baker.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-19",
        dia_letivo=False,
    )
    return escola_com_vinculo_alimentacao


@pytest.fixture
def escola_com_dias_nao_letivos(escola_com_vinculo_alimentacao):
    baker.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-18",
        dia_letivo=False,
    )
    baker.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-19",
        dia_letivo=False,
    )
    return escola_com_vinculo_alimentacao


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
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def escola_cemei():
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = baker.make("TipoUnidadeEscolar", iniciais="CEMEI")
    contato = baker.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = baker.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )
    escola = baker.make(
        "Escola",
        lote=lote,
        nome="CEMEI JOAO MENDES",
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def escola_com_periodos_e_horarios_combos(escola):
    periodo_manha = baker.make(
        "escola.PeriodoEscolar",
        nome="MANHA",
        uuid="42325516-aebd-4a3d-97c0-2a77c317c6be",
    )
    periodo_tarde = baker.make(
        "escola.PeriodoEscolar",
        nome="TARDE",
        uuid="5d668346-ad83-4334-8fec-94c801198d99",
    )
    baker.make(
        "escola.EscolaPeriodoEscolar",
        quantidade_alunos=325,
        escola=escola,
        periodo_escolar=periodo_manha,
    )
    baker.make(
        "escola.EscolaPeriodoEscolar",
        quantidade_alunos=418,
        escola=escola,
        periodo_escolar=periodo_tarde,
    )
    return escola


@pytest.fixture
def template_mensagem_alteracao_cardapio():
    return baker.make(TemplateMensagem, tipo=TemplateMensagem.ALTERACAO_CARDAPIO)


@pytest.fixture
def tipo_unidade_escolar():
    cardapio1 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = baker.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    return baker.make(
        "TipoUnidadeEscolar",
        iniciais=fake.name()[:10],
        cardapios=[cardapio1, cardapio2],
    )


@pytest.fixture
def periodo_escolar():
    return baker.make("PeriodoEscolar")


@pytest.fixture
def faixas_etarias_ativas():
    faixas = [
        (0, 1),
        (1, 4),
        (4, 6),
        (6, 8),
        (8, 12),
        (12, 24),
        (24, 48),
        (48, 72),
    ]
    return [
        baker.make("FaixaEtaria", inicio=inicio, fim=fim, ativo=True)
        for (inicio, fim) in faixas
    ]


@pytest.fixture
def cardapio_valido():
    cardapio_valido = baker.make(
        "Cardapio",
        id=1,
        data=datetime.date(2019, 11, 29),
        uuid="7a4ec98a-18a8-4d0a-b722-1da8f99aaf4b",
        descricao="lorem ipsum",
    )
    return cardapio_valido


@pytest.fixture
def cardapio_valido2():
    cardapio_valido2 = baker.make(
        "Cardapio",
        id=2,
        data=datetime.date(2019, 12, 15),
        uuid="7a4ec98a-18a8-4d0a-b722-1da8f99aaf4c",
    )
    return cardapio_valido2


@pytest.fixture
def cardapio_valido3():
    data = datetime.datetime.now() + datetime.timedelta(days=6)
    cardapio_valido = baker.make("Cardapio", id=22, data=data.date())
    return cardapio_valido


@pytest.fixture
def motivo_alteracao_cardapio():
    return baker.make(MotivoAlteracaoCardapio, nome="Aniversariantes do mês")


@pytest.fixture
def motivo_alteracao_cardapio_lanche_emergencial():
    return baker.make(
        MotivoAlteracaoCardapio,
        nome="Lanche Emergencial",
        uuid="19d0bca9-3cfe-4542-869e-185d580fef06",
    )


@pytest.fixture
def motivo_alteracao_cardapio_inativo():
    return baker.make(MotivoAlteracaoCardapio, nome="Motivo Inativo", ativo=False)


@pytest.fixture
def client_autenticado_vinculo_escola_cardapio(
    client,
    django_user_model,
    escola,
    template_mensagem_alteracao_cardapio,
    cardapio_valido2,
    cardapio_valido3,
):
    email = "test@test.com"
    rf = "8888888"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional="8888888"
    )
    assert escola.tipo_gestao.nome == "TERC TOTAL"
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
    baker.make(
        InversaoCardapio,
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        criado_por=user,
        criado_em=datetime.date(2019, 12, 12),
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )
    baker.make(
        AlteracaoCardapio,
        criado_por=user,
        escola=escola,
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )
    baker.make(
        GrupoSuspensaoAlimentacao, criado_por=user, escola=escola, rastro_escola=escola
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_dre_cardapio(
    client, django_user_model, escola, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_cogestor = baker.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_cardapio(client, django_user_model, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
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
    baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_dieta_cardapio(
    client, django_user_model, escola, codae
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_dieta = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_DIETA_ESPECIAL,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dieta,
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
def client_autenticado_vinculo_terceirizada_cardapio(
    client, django_user_model, escola, codae
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_nutri_admin = baker.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_EMPRESA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
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
    baker.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def vinculos_alimentacao():
    baker.make(
        "TipoUnidadeEscolar", iniciais="CEI DIRET", tem_somente_integral_e_parcial=False
    )
    baker.make(
        "TipoUnidadeEscolar", iniciais="EMEF", tem_somente_integral_e_parcial=False
    )
    baker.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF P FOM",
        tem_somente_integral_e_parcial=False,
    )

    tipo_unidade = baker.make(
        "TipoUnidadeEscolar", iniciais="CEMEI", tem_somente_integral_e_parcial=True
    )
    escola = baker.make("Escola", tipo_unidade=tipo_unidade)
    periodo_escolar = baker.make(
        "PeriodoEscolar",
        nome="INTEGRAL",
    )
    escola_periodo_escolar = baker.make(
        "EscolaPeriodoEscolar",
        periodo_escolar=periodo_escolar,
        escola=escola,
        quantidade_alunos=20,
    )

    return tipo_unidade, escola, periodo_escolar, escola_periodo_escolar


@pytest.fixture
def ativa_vinculo(vinculos_alimentacao):
    tipo_unidade, escola, periodo_escolar, escola_periodo_escolar = vinculos_alimentacao
    baker.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=tipo_unidade,
        periodo_escolar=periodo_escolar,
        ativo=False,
    )
    return tipo_unidade, escola_periodo_escolar


@pytest.fixture
def escola_com_horario_vinculo_alimentacao(
    escola_dre_guaianases,
    periodo_manha,
    tipo_alimentacao,
):
    baker.make(
        "cardapio.HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar",
        periodo_escolar=periodo_manha,
        escola=escola_dre_guaianases,
        tipo_alimentacao=tipo_alimentacao,
    )
    return escola


@pytest.fixture
def escola_emei():
    escola = baker.make(
        "Escola",
        nome="EMEI JOAO MENDES",
        codigo_eol="001546",
        tipo_unidade=baker.make("TipoUnidadeEscolar", iniciais="EMEI"),
    )
    return escola


@pytest.fixture
def escola_ceu_gestao():
    escola = baker.make(
        "Escola",
        nome="CEU GESTAO JOAO MENDES",
        codigo_eol="011546",
        tipo_unidade=baker.make("TipoUnidadeEscolar", iniciais="CEU GESTAO"),
    )
    return escola


@pytest.fixture
def escola_cieja():
    escola = baker.make(
        "Escola",
        nome="CIEJA JOAO MENDES",
        codigo_eol="111546",
        tipo_unidade=baker.make("TipoUnidadeEscolar", iniciais="CIEJA"),
    )
    return escola


@pytest.fixture
def escola_emebs():
    escola = baker.make(
        "Escola",
        nome="EMEBS JOAO MENDES",
        codigo_eol="211546",
        tipo_unidade=baker.make("TipoUnidadeEscolar", iniciais="EMEBS"),
    )
    return escola


@pytest.fixture
def escola_cca():
    escola = baker.make(
        "Escola",
        nome="CCA JOAO MENDES",
        codigo_eol="121546",
        tipo_unidade=baker.make("TipoUnidadeEscolar", iniciais="CCA"),
    )
    return escola
