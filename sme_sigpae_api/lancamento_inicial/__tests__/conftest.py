import datetime

import pytest
from model_bakery import baker

from ...dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from ...escola.models import (
    EscolaPeriodoEscolar,
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    PeriodoEscolar,
)
from ..models import LancamentoDiario


@pytest.fixture(
    params=[
        ("09/2020", datetime.date(2020, 9, 1), datetime.date(2020, 9, 30)),
        ("12/2020", datetime.date(2020, 12, 1), datetime.date(2020, 12, 31)),
        ("02/2020", datetime.date(2020, 2, 1), datetime.date(2020, 2, 29)),
        ("02/2021", datetime.date(2021, 2, 1), datetime.date(2021, 2, 28)),
    ]
)
def faixas_de_data(request):
    return request.param


@pytest.fixture
def lote():
    return baker.make("Lote")


@pytest.fixture
def diretoria_regional():
    return baker.make("DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA")


@pytest.fixture
def escola(diretoria_regional, lote):
    return baker.make("Escola", lote=lote, diretoria_regional=diretoria_regional)


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
    return client


@pytest.fixture
def escola_periodo_escolar():
    return baker.make(EscolaPeriodoEscolar)


@pytest.fixture
def periodo_escolar():
    return baker.make(PeriodoEscolar)


@pytest.fixture
def escola_periodo_escolar_com_quantidade_de_alunos(escola, periodo_escolar):
    return baker.make(
        EscolaPeriodoEscolar,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=123,
    )


@pytest.fixture
def log_mudanca_qtde_1(escola, periodo_escolar):
    log = baker.make(
        LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos_de=121,
        quantidade_alunos_para=123,
    )
    log.criado_em = datetime.date(2020, 12, 21)
    log.save()
    return log


@pytest.fixture
def log_mudanca_qtde_2(escola, periodo_escolar):
    log = baker.make(
        LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos_de=119,
        quantidade_alunos_para=121,
    )
    log.criado_em = datetime.date(2020, 12, 11)
    log.save()
    return log


@pytest.fixture
def lancamentos(escola_periodo_escolar):
    lancamentos = []
    for dia in range(1, 5):
        lancamentos.append(
            baker.make(
                LancamentoDiario,
                escola_periodo_escolar=escola_periodo_escolar,
                data=datetime.date(2020, 10, dia),
            )
        )

    return lancamentos
