import datetime
import os
import uuid

import pandas as pd
import pytest
import pytz
from faker import Faker
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.paineis_consolidados.api import constants as consts_pc
from sme_sigpae_api.paineis_consolidados.api.serializers import (
    SolicitacoesExportXLSXSerializer,
)
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesCODAE

from ...cardapio.models import AlteracaoCardapio, SuspensaoAlimentacaoDaCEI
from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from ...dieta_especial.models import SolicitacaoDietaEspecial
from ...inclusao_alimentacao.models import (
    DiasMotivosInclusaoDeAlimentacaoCEI,
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
)
from ...kit_lanche.models import (
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
)

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def diretoria_regional():
    return mommy.make("DiretoriaRegional", nome="DRE X")


@pytest.fixture
def escola(diretoria_regional):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make(
        "Lote",
        nome="LOTE 1",
        diretoria_regional=diretoria_regional,
        terceirizada=terceirizada,
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")
    return mommy.make(
        "Escola",
        diretoria_regional=diretoria_regional,
        lote=lote,
        tipo_gestao=tipo_gestao,
        uuid="fdf23c84-c9ff-4811-adff-e70df5378466",
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def escola_outro_lote(diretoria_regional):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make(
        "Lote",
        nome="LOTE 2",
        diretoria_regional=diretoria_regional,
        terceirizada=terceirizada,
    )
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais="CEU GESTAO")
    return mommy.make(
        "Escola",
        diretoria_regional=diretoria_regional,
        lote=lote,
        tipo_gestao=tipo_gestao,
        uuid="452fe369-7887-4340-8a38-310318eeeb7b",
        tipo_unidade=tipo_unidade_escolar,
    )


@pytest.fixture
def diretoria_regional2():
    return mommy.make("DiretoriaRegional")


@pytest.fixture
def escola2(diretoria_regional2):
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    contato = mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    return mommy.make(
        "Escola", diretoria_regional=diretoria_regional2, lote=lote, contato=contato
    )


@pytest.fixture
def templates():
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.ALTERACAO_CARDAPIO)
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.SOLICITACAO_KIT_LANCHE_AVULSA)
    mommy.make(TemplateMensagem, tipo=TemplateMensagem.INCLUSAO_ALIMENTACAO_CONTINUA)


@pytest.fixture
def alteracoes_cardapio(escola):
    alteracao_cardapio_1 = mommy.make(
        AlteracaoCardapio,
        escola=escola,
        criado_em=datetime.date(2019, 10, 1),
        data_inicial=datetime.date(2019, 10, 1),
    )
    alteracao_cardapio_2 = mommy.make(
        AlteracaoCardapio,
        escola=escola,
        criado_em=datetime.date(2019, 10, 10),
        data_inicial=datetime.date(2019, 10, 10),
    )
    alteracao_cardapio_3 = mommy.make(
        AlteracaoCardapio,
        escola=escola,
        criado_em=datetime.date(2019, 10, 20),
        data_inicial=datetime.date(2019, 10, 20),
    )
    return alteracao_cardapio_1, alteracao_cardapio_2, alteracao_cardapio_3


@pytest.fixture
def solicitacoes_kit_lanche(escola):
    kits = mommy.make(KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        criado_em=datetime.date(2019, 1, 1),
        data=datetime.date(2019, 1, 1),
    )
    solicitacao_kit_lanche_avulsa_1 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        uuid="ac0b6f5b-36b0-47d2-99a2-3bc9825b31fb",
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        data=datetime.date(2019, 2, 1),
        criado_em=datetime.date(2019, 2, 1),
    )
    solicitacao_kit_lanche_avulsa_2 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        uuid="d15f17d5-d4c5-47f5-a09a-55677dbc65bf",
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        data=datetime.date(2018, 2, 1),
        criado_em=datetime.date(2019, 2, 1),
    )
    solicitacao_kit_lanche_avulsa_3 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        uuid="c9715ddb-7e95-4156-91a5-c60c8621806b",
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        criado_em=datetime.date(2019, 2, 1),
        data=datetime.date(2020, 2, 1),
    )
    solicitacao_kit_lanche_avulsa_4 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        uuid="8827b394-ef39-4757-8136-6e09d5c7c486",
    )
    return (
        solicitacao_kit_lanche_avulsa_1,
        solicitacao_kit_lanche_avulsa_2,
        solicitacao_kit_lanche_avulsa_3,
        solicitacao_kit_lanche_avulsa_4,
    )


@pytest.fixture
def solicitacoes_kit_lanche_autorizadas(solicitacoes_kit_lanche):
    (
        solicitacao_kit_lanche_avulsa_1,
        solicitacao_kit_lanche_avulsa_2,
        solicitacao_kit_lanche_avulsa_3,
        solicitacao_kit_lanche_avulsa_4,
    ) = solicitacoes_kit_lanche

    solicitacao_kit_lanche_avulsa_1.status = "CODAE_AUTORIZADO"
    solicitacao_kit_lanche_avulsa_1.save()
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_kit_lanche_avulsa_1.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_AVULSA,
    )

    solicitacao_kit_lanche_avulsa_2.status = "CODAE_AUTORIZADO"
    solicitacao_kit_lanche_avulsa_2.save()
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_kit_lanche_avulsa_2.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_AVULSA,
    )

    solicitacao_kit_lanche_avulsa_3.status = "CODAE_AUTORIZADO"
    solicitacao_kit_lanche_avulsa_3.save()
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_kit_lanche_avulsa_3.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_AVULSA,
    )

    solicitacao_kit_lanche_avulsa_4.status = "CODAE_AUTORIZADO"
    solicitacao_kit_lanche_avulsa_4.save()
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao_kit_lanche_avulsa_4.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_KIT_LANCHE_AVULSA,
    )


@pytest.fixture
def inclusoes_de_alimentacao_continua(escola):
    inclusao_continua_1 = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=datetime.date(2019, 5, 1),
        data_final=datetime.date(2019, 6, 1),
        criado_em=datetime.date(2019, 5, 1),
        escola=escola,
    )
    inclusao_continua_2 = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=datetime.date(2019, 6, 1),
        criado_em=datetime.date(2019, 6, 1),
        data_final=datetime.date(2019, 7, 1),
        escola=escola,
    )
    inclusao_continua_3 = mommy.make(
        InclusaoAlimentacaoContinua,
        criado_em=datetime.date(2019, 7, 1),
        data_inicial=datetime.date(2019, 7, 1),
        data_final=datetime.date(2019, 8, 1),
        escola=escola,
    )
    return inclusao_continua_1, inclusao_continua_2, inclusao_continua_3


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
def users_diretor_escola(
    client,
    django_user_model,
    request,
    escola,
    templates,
    alteracoes_cardapio,
    solicitacoes_kit_lanche,
    inclusoes_de_alimentacao_continua,
):
    email, password, rf, cpf = request.param
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    client.login(username=email, password=password)
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
    alt1, alt2, alt3 = alteracoes_cardapio
    alt1.inicia_fluxo(user=user)

    alt2.inicia_fluxo(user=user)
    alt3.inicia_fluxo(user=user)
    solkit1, solkit2, solkit3, solkit4 = solicitacoes_kit_lanche
    solkit1.inicia_fluxo(user=user)
    solkit2.inicia_fluxo(user=user)
    solkit3.inicia_fluxo(user=user)
    solkit4.inicia_fluxo(user=user)
    inc_continua_1, inc_continua_2, inc_continua_3 = inclusoes_de_alimentacao_continua
    inc_continua_1.inicia_fluxo(user=user)
    inc_continua_2.inicia_fluxo(user=user)
    inc_continua_3.inicia_fluxo(user=user)

    inc_continua_1.criado_em = datetime.datetime(
        year=2019, month=1, day=15, tzinfo=pytz.UTC
    )
    inc_continua_1.save()
    inc_continua_2.criado_em = datetime.datetime(
        year=2019, month=2, day=15, tzinfo=pytz.UTC
    )
    inc_continua_2.save()
    inc_continua_3.criado_em = datetime.datetime(
        year=2019, month=3, day=15, tzinfo=pytz.UTC
    )
    inc_continua_3.save()

    k1 = solkit1.solicitacao_kit_lanche
    k1.criado_em = datetime.datetime(year=2019, month=4, day=15, tzinfo=pytz.UTC)
    k1.save()
    k2 = solkit2.solicitacao_kit_lanche
    k2.criado_em = datetime.datetime(year=2019, month=5, day=15, tzinfo=pytz.UTC)
    k2.save()
    k3 = solkit3.solicitacao_kit_lanche
    k3.criado_em = datetime.datetime(year=2019, month=6, day=15, tzinfo=pytz.UTC)
    k3.save()
    k4 = solkit4.solicitacao_kit_lanche
    k4.criado_em = datetime.datetime(year=2019, month=7, day=15, tzinfo=pytz.UTC)
    k4.save()

    alt1.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt1.save()
    alt2.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt2.save()
    alt3.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt3.save()

    return client, email, password, rf, cpf, user


@pytest.fixture
def alteracoes_cardapio_dre(escola2):
    alteracao_cardapio_1 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 3, 1),
        data_inicial=datetime.date(2019, 3, 1),
    )
    alteracao_cardapio_2 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 2, 10),
        data_inicial=datetime.date(2019, 2, 10),
    )
    alteracao_cardapio_3 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 1, 20),
        data_inicial=datetime.date(2019, 1, 20),
    )
    return alteracao_cardapio_1, alteracao_cardapio_2, alteracao_cardapio_3


@freeze_time("2020-02-03")  # Segunda
@pytest.fixture
def alteracoes_cardapio_dre_atual(escola2):
    alteracao_cardapio_1 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 3, 1),
        data_inicial=datetime.date.today() + datetime.timedelta(days=1),
    )
    alteracao_cardapio_2 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 2, 10),
        data_inicial=datetime.date.today() + datetime.timedelta(days=5),
    )
    alteracao_cardapio_3 = mommy.make(
        AlteracaoCardapio,
        escola=escola2,
        criado_em=datetime.date(2019, 1, 20),
        data_inicial=datetime.date.today() + datetime.timedelta(days=20),
    )
    return alteracao_cardapio_1, alteracao_cardapio_2, alteracao_cardapio_3


@pytest.fixture
def solicitacoes_kit_lanche_dre(escola2):
    kits = mommy.make(KitLanche, _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        criado_em=datetime.date(2019, 5, 1),
        data=datetime.date(2019, 5, 1),
    )
    solicitacao_kit_lanche_avulsa_1 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola2,
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        data=datetime.date(2019, 2, 1),
        criado_em=datetime.date(2019, 2, 1),
    )
    solicitacao_kit_lanche_avulsa_2 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola2,
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        data=datetime.date(2018, 2, 1),
        criado_em=datetime.date(2019, 2, 1),
    )
    solicitacao_kit_lanche_avulsa_3 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola2,
    )
    solicitacao_kit_lanche = mommy.make(
        SolicitacaoKitLanche,
        kits=kits,
        criado_em=datetime.date(2019, 7, 1),
        data=datetime.date(2020, 7, 1),
    )
    solicitacao_kit_lanche_avulsa_4 = mommy.make(
        SolicitacaoKitLancheAvulsa,
        local=fake.text()[:160],
        quantidade_alunos=300,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola2,
    )
    return (
        solicitacao_kit_lanche_avulsa_1,
        solicitacao_kit_lanche_avulsa_2,
        solicitacao_kit_lanche_avulsa_3,
        solicitacao_kit_lanche_avulsa_4,
    )


@pytest.fixture
def inclusoes_de_alimentacao_continua_dre(escola2):
    inclusao_continua_1 = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=datetime.date(2019, 5, 1),
        data_final=datetime.date(2019, 6, 1),
        escola=escola2,
    )
    inclusao_continua_2 = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=datetime.date(2019, 6, 1),
        data_final=datetime.date(2019, 7, 1),
        escola=escola2,
    )
    inclusao_continua_3 = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=datetime.date(2019, 12, 1),
        data_final=datetime.date(2019, 12, 9),
        escola=escola2,
    )
    return inclusao_continua_1, inclusao_continua_2, inclusao_continua_3


@pytest.fixture(
    params=[
        # email, senha, rf, cpf
        ("DREADM_1@sme.prefeitura.sp.gov.br", "adminadmin", "0000001", "44426575052"),
        ("DREADM_2@sme.prefeitura.sp.gov.br", "aasdsadsadff", "0000002", "56789925031"),
        ("DREADM_3@sme.prefeitura.sp.gov.br", "98as7d@@#", "0000147", "86880963099"),
        ("DREADM_4@sme.prefeitura.sp.gov.br", "##$$csazd@!", "0000441", "13151715036"),
        ("DREADM_5@sme.prefeitura.sp.gov.br", "!!@##FFG121", "0005551", "40296233013"),
    ]
)
def solicitacoes_ano_dre(
    client,
    django_user_model,
    request,
    diretoria_regional2,
    templates,
    alteracoes_cardapio_dre,
    solicitacoes_kit_lanche_dre,
    inclusoes_de_alimentacao_continua_dre,
):
    email, password, rf, cpf = request.param
    user_dre = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf, cpf=cpf
    )
    user_codae = django_user_model.objects.create_user(
        username="xxx@email.com",
        password=constants.DJANGO_ADMIN_PASSWORD,
        email="xxx@email.com",
        registro_funcional="9987634",
        cpf="12oiu3123",
    )
    user_escola = django_user_model.objects.create_user(
        username="user@escola.com",
        password=constants.DJANGO_ADMIN_PASSWORD,
        email="user@escola.com",
        registro_funcional="123123",
        cpf="12312312332",
    )
    client.login(username=email, password=password)

    perfil_adm_dre = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)

    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user_dre,
        instituicao=diretoria_regional2,
        perfil=perfil_adm_dre,
        data_inicial=hoje,
        ativo=True,
    )

    alt1, alt2, alt3 = alteracoes_cardapio_dre
    alt1.inicia_fluxo(user=user_escola)
    alt2.inicia_fluxo(user=user_escola)
    alt3.inicia_fluxo(user=user_escola)
    solkit1, solkit2, solkit3, solkit4 = solicitacoes_kit_lanche_dre
    solkit1.inicia_fluxo(user=user_escola)
    solkit2.inicia_fluxo(user=user_escola)
    solkit3.inicia_fluxo(user=user_escola)
    solkit4.inicia_fluxo(user=user_escola)

    (
        inc_continua_1,
        inc_continua_2,
        inc_continua_3,
    ) = inclusoes_de_alimentacao_continua_dre
    inc_continua_1.inicia_fluxo(user=user_escola)
    inc_continua_2.inicia_fluxo(user=user_escola)
    inc_continua_3.inicia_fluxo(user=user_escola)

    inc_continua_1.criado_em = datetime.datetime(
        year=2019, month=1, day=15, tzinfo=pytz.UTC
    )
    inc_continua_1.save()
    inc_continua_2.criado_em = datetime.datetime(
        year=2019, month=1, day=15, tzinfo=pytz.UTC
    )
    inc_continua_2.save()
    inc_continua_3.criado_em = datetime.datetime(
        year=2019, month=1, day=15, tzinfo=pytz.UTC
    )
    inc_continua_3.save()

    k1 = solkit1.solicitacao_kit_lanche
    k1.criado_em = datetime.datetime(year=2019, month=2, day=15, tzinfo=pytz.UTC)
    k1.save()
    k2 = solkit2.solicitacao_kit_lanche
    k2.criado_em = datetime.datetime(year=2019, month=2, day=15, tzinfo=pytz.UTC)
    k2.save()
    k3 = solkit3.solicitacao_kit_lanche
    k3.criado_em = datetime.datetime(year=2019, month=4, day=15, tzinfo=pytz.UTC)
    k3.save()
    k4 = solkit4.solicitacao_kit_lanche
    k4.criado_em = datetime.datetime(year=2019, month=4, day=15, tzinfo=pytz.UTC)
    k4.save()

    alt1.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt1.save()
    alt2.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt2.save()
    alt3.criado_em = datetime.datetime(year=2019, month=12, day=15, tzinfo=pytz.UTC)
    alt3.save()

    alt1, alt2, alt3 = alteracoes_cardapio_dre
    alt1.dre_valida(user=user_dre)
    alt2.dre_valida(user=user_dre)
    alt3.dre_valida(user=user_dre)
    solkit1, solkit2, solkit3, solkit4 = solicitacoes_kit_lanche_dre
    solkit1.dre_valida(user=user_dre)
    solkit2.dre_valida(user=user_dre)
    solkit3.dre_valida(user=user_dre)
    solkit4.dre_valida(user=user_dre)
    (
        inc_continua_1,
        inc_continua_2,
        inc_continua_3,
    ) = inclusoes_de_alimentacao_continua_dre
    inc_continua_1.dre_valida(user=user_dre)
    inc_continua_2.dre_valida(user=user_dre)
    inc_continua_3.dre_valida(user=user_dre)
    inc_continua_1.codae_nega(user=user_codae)
    return client, email, password, rf, cpf, user_dre


@pytest.fixture
def client_autenticado_painel_consolidados(client_autenticado, django_user_model):
    user = django_user_model.objects.get(email="test@test.com")
    diretoria_regional = mommy.make(
        "escola.DiretoriaRegional", usuarios=[user], make_m2m=True
    )
    escola = mommy.make("escola.Escola", diretoria_regional=diretoria_regional)
    mommy.make(
        AlteracaoCardapio,
        escola=escola,
        status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
    )
    return client_autenticado


@pytest.fixture
def solicitacoes_dieta_especial():
    statuses = [
        DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
        DietaEspecialWorkflow.CODAE_AUTORIZADO,
        DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO,
    ]
    saida = []

    for status in statuses:
        saida += mommy.make(SolicitacaoDietaEspecial, status=status, _quantity=2)

    return saida


@pytest.fixture(
    params=[
        [DietaEspecialWorkflow.CODAE_A_AUTORIZAR, "pendentes-autorizacao"],
        [DietaEspecialWorkflow.CODAE_AUTORIZADO, "autorizados"],
        [DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO, "negados"],
    ]
)
def status_and_endpoint(request):
    return request.param


@pytest.fixture
def client_autenticado_dre_paineis_consolidados(
    client,
    django_user_model,
    diretoria_regional2,
    templates,
    alteracoes_cardapio_dre_atual,
):
    email = "test@test.com"
    email2 = "user@escola.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    user_escola = django_user_model.objects.create_user(
        username=email2,
        password=password,
        email=email2,
        registro_funcional="123123",
        cpf="12312312332",
    )
    perfil_cogestor = mommy.make("Perfil", nome=constants.COGESTOR_DRE, ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=diretoria_regional2,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    alt1, alt2, alt3 = alteracoes_cardapio_dre_atual
    alt1.inicia_fluxo(user=user_escola)
    alt2.inicia_fluxo(user=user_escola)
    alt3.inicia_fluxo(user=user_escola)
    return client


@pytest.fixture
def client_autenticado_codae_paineis_consolidados(client, django_user_model):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
    )
    codae = mommy.make("Codae")
    hoje = datetime.date.today()
    mommy.make(
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
def motivo_inclusao_normal():
    return mommy.make("MotivoInclusaoNormal", nome=fake.name())


@pytest.fixture
def periodo_escolar_manha():
    return mommy.make("PeriodoEscolar", nome="MANHA")


@pytest.fixture
def tipo_alimentacao_refeicao():
    return mommy.make("TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche():
    return mommy.make("TipoAlimentacao", nome="Lanche")


@pytest.fixture
def inclusoes_normais(
    escola,
    motivo_inclusao_normal,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
):
    grupo_inclusao_normal = mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola,
        status="CODAE_AUTORIZADO",
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_lote=escola.lote,
        uuid="a4639e26-f4fd-43e9-a8cc-2d0da995c8ef",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=grupo_inclusao_normal.uuid,
        status_evento=1,
        solicitacao_tipo=4,
    )
    mommy.make(
        "InclusaoAlimentacaoNormal",
        data=datetime.date(2023, 7, 1),
        grupo_inclusao=grupo_inclusao_normal,
    )
    mommy.make(
        "InclusaoAlimentacaoNormal",
        data=datetime.date(2023, 7, 2),
        motivo=motivo_inclusao_normal,
        grupo_inclusao=grupo_inclusao_normal,
    )
    qp = mommy.make(
        "QuantidadePorPeriodo",
        numero_alunos=100,
        periodo_escolar=periodo_escolar_manha,
        grupo_inclusao_normal=grupo_inclusao_normal,
    )
    qp.tipos_alimentacao.add(tipo_alimentacao_lanche)
    qp.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    qp.save()


@pytest.fixture
def solicitacao_medicao_inicial(escola, periodo_escolar_manha):
    tipo_contagem = mommy.make("TipoContagemAlimentacao", nome="Fichas")
    solicitacao_medicao = mommy.make(
        "SolicitacaoMedicaoInicial",
        uuid="bed4d779-2d57-4c5f-bf9c-9b93ddac54d9",
        mes="08",
        ano="2023",
        escola=escola,
    )
    solicitacao_medicao.tipos_contagem_alimentacao.set([tipo_contagem])
    medicao = mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_escolar_manha,
    )
    periodo_integral = mommy.make("PeriodoEscolar", nome="INTEGRAL")
    mommy.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao,
        periodo_escolar=periodo_integral,
    )
    mommy.make("ValorMedicao", medicao=medicao)
    return solicitacao_medicao


@pytest.fixture
def client_autenticado_escola_paineis_consolidados(
    client,
    django_user_model,
    escola,
    templates,
    inclusoes_normais,
    solicitacao_medicao_inicial,
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_diretor = mommy.make("Perfil", nome=constants.DIRETOR_UE, ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def inclusao_alimentacao_continua_entre_dois_meses(escola, periodo_escolar_manha):
    data_inicial = datetime.date(2023, 3, 20)
    data_final = datetime.date(2023, 4, 10)
    inclusao_continua = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        rastro_escola=escola,
        status="CODAE_AUTORIZADO",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=inclusao_continua.uuid,
        status_evento=1,
        solicitacao_tipo=7,
    )
    mommy.make(
        "QuantidadePorPeriodo",
        numero_alunos=50,
        inclusao_alimentacao_continua=inclusao_continua,
        periodo_escolar=periodo_escolar_manha,
        dias_semana=[0, 1, 2, 3, 4, 5, 6],
    )
    return inclusao_continua


@pytest.fixture
def inclusao_alimentacao_continua_unico_mes(escola, periodo_escolar_manha):
    data_inicial = datetime.date(2023, 2, 5)
    data_final = datetime.date(2023, 2, 25)
    inclusao_continua = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        rastro_escola=escola,
        status="CODAE_AUTORIZADO",
        uuid="ec27137e-9b8f-419c-adaa-7ed238d40bae",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=inclusao_continua.uuid,
        status_evento=1,
        solicitacao_tipo=7,
    )
    mommy.make(
        "QuantidadePorPeriodo",
        numero_alunos=100,
        inclusao_alimentacao_continua=inclusao_continua,
        periodo_escolar=periodo_escolar_manha,
        dias_semana=[],
    )
    return inclusao_continua


@pytest.fixture
def inclusao_alimentacao_continua_varios_meses(escola, periodo_escolar_manha):
    data_inicial = datetime.date(2023, 5, 13)
    data_final = datetime.date(2023, 8, 13)
    inclusao_continua = mommy.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        rastro_escola=escola,
        status="CODAE_AUTORIZADO",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=inclusao_continua.uuid,
        status_evento=1,
        solicitacao_tipo=7,
    )
    mommy.make(
        "QuantidadePorPeriodo",
        numero_alunos=75,
        inclusao_alimentacao_continua=inclusao_continua,
        periodo_escolar=periodo_escolar_manha,
        dias_semana=[0, 1, 2, 3, 4, 5, 6],
    )
    return inclusao_continua


@pytest.fixture
def periodo_escolar_integral():
    return mommy.make("PeriodoEscolar", nome="INTEGRAL")


@pytest.fixture()
def inclusao_alimentacao_cei(
    motivo_inclusao_normal, escola, periodo_escolar_manha, periodo_escolar_integral
):
    inclusao_cei = mommy.make(
        InclusaoAlimentacaoDaCEI,
        escola=escola,
        rastro_escola=escola,
        periodo_escolar=periodo_escolar_manha,
        status="CODAE_AUTORIZADO",
        uuid="50830aed-33ad-442a-8890-5b508e54a0d8",
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=inclusao_cei.uuid,
        status_evento=1,
        solicitacao_tipo=5,
    )
    mommy.make(
        DiasMotivosInclusaoDeAlimentacaoCEI,
        inclusao_cei=inclusao_cei,
        motivo=motivo_inclusao_normal,
        data=datetime.date(2023, 8, 10),
    )
    faixa_etaria = mommy.make("FaixaEtaria", inicio=48, fim=73, ativo=True)
    mommy.make(
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
        inclusao_alimentacao_da_cei=inclusao_cei,
        faixa_etaria=faixa_etaria,
        quantidade_alunos=25,
        periodo=periodo_escolar_manha,
        periodo_externo=periodo_escolar_integral,
    )
    return inclusao_cei


@pytest.fixture
def motivo_suspensao():
    return mommy.make("MotivoSuspensao", nome=fake.name())


@pytest.fixture()
def suspensoes_alimentacao_cei(
    motivo_suspensao,
    escola,
    periodo_escolar_manha,
    periodo_escolar_integral,
    tipo_alimentacao_lanche,
    tipo_alimentacao_refeicao,
):
    suspensao_cei = mommy.make(
        SuspensaoAlimentacaoDaCEI,
        escola=escola,
        rastro_escola=escola,
        motivo=motivo_suspensao,
        status="INFORMADO",
        data=datetime.date(2023, 7, 15),
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=suspensao_cei.uuid,
        status_evento=0,
        solicitacao_tipo=6,
    )
    suspensao_cei.periodos_escolares.add(periodo_escolar_manha)
    suspensao_cei.periodos_escolares.add(periodo_escolar_integral)
    suspensao_cei.save()

    grupo_suspensao_alimentacao = mommy.make(
        "GrupoSuspensaoAlimentacao",
        escola=escola,
        status="INFORMADO",
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )
    mommy.make(
        "LogSolicitacoesUsuario",
        uuid_original=grupo_suspensao_alimentacao.uuid,
        status_evento=1,
        solicitacao_tipo=2,
    )
    mommy.make(
        "SuspensaoAlimentacao",
        data=datetime.date(2023, 8, 3),
        motivo=motivo_suspensao,
        grupo_suspensao=grupo_suspensao_alimentacao,
    )
    mommy.make(
        "SuspensaoAlimentacao",
        data=datetime.date(2023, 8, 13),
        motivo=motivo_suspensao,
        grupo_suspensao=grupo_suspensao_alimentacao,
    )
    qp_suspensao_manha = mommy.make(
        "QuantidadePorPeriodoSuspensaoAlimentacao",
        numero_alunos=75,
        periodo_escolar=periodo_escolar_manha,
        grupo_suspensao=grupo_suspensao_alimentacao,
    )
    qp_suspensao_manha.tipos_alimentacao.add(tipo_alimentacao_lanche)
    qp_suspensao_manha.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    qp_suspensao_manha.save()
    qp_suspensao_integral = mommy.make(
        "QuantidadePorPeriodoSuspensaoAlimentacao",
        numero_alunos=50,
        periodo_escolar=periodo_escolar_integral,
        grupo_suspensao=grupo_suspensao_alimentacao,
    )
    qp_suspensao_integral.tipos_alimentacao.add(tipo_alimentacao_lanche)
    qp_suspensao_integral.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    qp_suspensao_integral.save()

    return suspensao_cei, grupo_suspensao_alimentacao


@pytest.fixture
def solicitacao_unificada(escola):
    kits = mommy.make("KitLanche", _quantity=3)
    solicitacao_kit_lanche = mommy.make(
        "SolicitacaoKitLanche",
        data=datetime.date(2019, 10, 14),
        tempo_passeio=2,
        kits=kits,
    )
    escolas_quantidades = mommy.make(
        "EscolaQuantidade", escola=escola, quantidade_alunos=100
    )
    solicitacao_unificada = mommy.make(
        "SolicitacaoKitLancheUnificada",
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        outro_motivo=fake.text(),
        diretoria_regional=escola.lote.diretoria_regional,
        rastro_dre=escola.lote.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        uuid="d0d3ec92-a2db-4060-a4da-b7ed9d88a7c3",
    )
    solicitacao_unificada.escolas_quantidades.add(escolas_quantidades)
    solicitacao_unificada.save()
    return solicitacao_unificada


@pytest.fixture
def inclusao_alimentacao_cemei(escola):
    inclusao_cemei = mommy.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        uuid="ba5551b3-b770-412b-a923-b0e78301d1fd",
    )
    return inclusao_cemei


@pytest.fixture
def kit_lanche_cei(escola):
    mommy.make("escola.EscolaPeriodoEscolar", escola=escola, quantidade_alunos=500)
    kits = mommy.make("KitLanche", _quantity=3)
    mommy.make("FaixaEtaria", _quantity=3, ativo=True)
    solicitacao_kit_lanche = mommy.make(
        "SolicitacaoKitLanche", kits=kits, data=datetime.date(2000, 1, 1)
    )
    return mommy.make(
        "SolicitacaoKitLancheCEIAvulsa",
        local=fake.text()[:160],
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        uuid="318ca781-943a-4121-b970-70ac4d4ccc8a",
    )


@pytest.fixture
def kit_lanche_cemei():
    kit_lanche_cemei = mommy.make(
        "SolicitacaoKitLancheCEMEI",
        local="Parque do Ibirapuera",
        data="2022-10-25",
        uuid="2fdb22fe-370c-4379-94f4-a52478c03e6e",
    )

    mommy.make("KitLanche", nome="KIT 1")
    mommy.make("KitLanche", nome="KIT 2")
    mommy.make("KitLanche", nome="KIT 3")
    kits = KitLanche.objects.all()

    solicitacao_cei = mommy.make(
        "SolicitacaoKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cemei=kit_lanche_cemei,
        kits=kits,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )
    mommy.make(
        "FaixasQuantidadesKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
    )

    mommy.make(
        "SolicitacaoKitLancheEMEIdaCEMEI",
        solicitacao_kit_lanche_cemei=kit_lanche_cemei,
        quantidade_alunos=10,
        matriculados_quando_criado=20,
        kits=kits,
    )

    return kit_lanche_cemei


@pytest.fixture
def vinculo_periodo_alimentacao(escola, periodo_escolar_manha):
    vinculo_alimentacao = mommy.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=escola.tipo_unidade,
        periodo_escolar=periodo_escolar_manha,
    )
    tipo_alimentacao_refeicao = mommy.make("TipoAlimentacao", nome="Refeição")
    vinculo_alimentacao.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    vinculo_alimentacao.save()


@pytest.fixture
def dados_para_geracao_excel_e_pdf(
    users_diretor_escola,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    quantidade_por_periodo_factory,
    log_solicitacoes_usuario_factory,
):
    _, _, _, _, _, usuario = users_diretor_escola
    instituicao = usuario.vinculo_atual.instituicao

    # Alimentacao Normal
    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.ESCOLA_CANCELOU,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        usuario=usuario,
    )

    data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    queryset = [s for s in SolicitacoesCODAE.objects.all()]
    serializer = SolicitacoesExportXLSXSerializer(
        queryset,
        context={
            "instituicao": dados_para_geracao_excel_e_pdf,
            "status": data.get("status").upper(),
        },
        many=True,
    )

    return instituicao, queryset, serializer, data


@pytest.fixture
def dados_para_montar_excel():
    linhas = [
        consts_pc.ROW_IDX_TITULO_ARQUIVO,
        consts_pc.ROW_IDX_FILTROS_PT1,
        consts_pc.ROW_IDX_FILTROS_PT2,
        consts_pc.ROW_IDX_HEADER_CAMPOS,
    ]
    colunas = [
        consts_pc.COL_IDX_N,
        consts_pc.COL_IDX_LOTE,
        consts_pc.COL_IDX_UNIDADE_EDUCACIONAL,
        consts_pc.COL_IDX_TIPO_DE_SOLICITACAO,
        consts_pc.COL_IDX_ID_SOLICITACAO,
        consts_pc.COL_IDX_DATA_EVENTO,
        consts_pc.COL_IDX_DIA_DA_SEMANA,
        consts_pc.COL_IDX_PERIODO,
        consts_pc.COL_IDX_TIPO_DE_ALIMENTACAO,
        consts_pc.COL_IDX_TIPO_DE_ALTERACAO,
        consts_pc.COL_IDX_NUMERO_DE_ALUNOS,
        consts_pc.COL_IDX_NUMERO_TOTAL_KITS,
        consts_pc.COL_IDX_OBSERVACOES,
        consts_pc.COL_IDX_DATA_LOG,
    ]
    output_file = f"/tmp/{uuid.uuid4()}.xlsx"
    nome_aba = "Relatório"

    xlwriter = pd.ExcelWriter(output_file, engine="xlsxwriter")
    workbook = xlwriter.book
    worksheet = workbook.add_worksheet(nome_aba)
    xlwriter.sheets["Relatório"] = worksheet

    worksheet.set_row(linhas[0], 50)
    worksheet.set_row(linhas[1], 30)
    columns_width = {
        "A:A": 5,
        "B:B": 8,
        "C:C": 40,
        "D:D": 30,
        "E:E": 15,
        "F:G": 30,
        "H:H": 10,
        "I:J": 30,
        "K:K": 13,
        "L:L": 15,
        "M:M": 30,
        "N:N": 20,
    }
    for col, width in columns_width.items():
        worksheet.set_column(col, width)
    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})

    # return linhas, colunas, output_file, xlwriter, workbook, worksheet, single_cell_format, nome_aba
    try:
        yield linhas, colunas, output_file, xlwriter, workbook, worksheet, single_cell_format, nome_aba
    finally:
        xlwriter.close()
        if os.path.exists(output_file):
            os.remove(output_file)
