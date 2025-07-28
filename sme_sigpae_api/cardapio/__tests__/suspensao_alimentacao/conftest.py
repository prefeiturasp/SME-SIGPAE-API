import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers import (
    SuspensaoAlimentacaoSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.dados_comuns.fluxo_status import InformativoPartindoDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import TemplateMensagem


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 5), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 10), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 20), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 25), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 31), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 3), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 4), datetime.date(2019, 12, 31)),
    ]
)
def suspensao_alimentacao_parametros_mes(request):
    return request.param


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 4)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 5)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 6)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 7)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 8)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 9)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 10)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 11)),
    ]
)
def suspensao_alimentacao_parametros_semana(request):
    return request.param


@pytest.fixture
def quantidade_por_periodo_suspensao_alimentacao():
    return baker.make(QuantidadePorPeriodoSuspensaoAlimentacao, numero_alunos=100)


@pytest.fixture
def suspensao_alimentacao_serializer(suspensao_alimentacao):
    return SuspensaoAlimentacaoSerializer(suspensao_alimentacao)


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de, data para
        (
            datetime.date(2019, 12, 25),
            datetime.date(2020, 1, 10),
        ),  # deve ser no ano corrente
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 20),
        ),  # nao pode ser no passado
        (
            datetime.date(2019, 10, 17),
            datetime.date(2019, 12, 20),
        ),  # nao pode ter mais de 60 dias de intervalo
        (
            datetime.date(2019, 10, 31),
            datetime.date(2019, 10, 15),
        ),  # data de nao pode ser maior que data para
    ]
)
def grupo_suspensao_alimentacao_params(request):
    return request.param


@pytest.fixture
def suspensao_alimentacao(motivo_suspensao_alimentacao):
    return baker.make(SuspensaoAlimentacao, motivo=motivo_suspensao_alimentacao)


@pytest.fixture
def suspensao_periodo_escolar(suspensao_alimentacao):
    return baker.make(
        SuspensaoAlimentacaoNoPeriodoEscolar,
        suspensao_alimentacao=suspensao_alimentacao,
    )


@pytest.fixture
def template_mensagem_suspensao_alimentacao():
    return baker.make(TemplateMensagem, tipo=TemplateMensagem.SUSPENSAO_ALIMENTACAO)


@pytest.fixture
def grupo_suspensao_alimentacao(escola):
    grupo_suspensao = baker.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola,
        rastro_escola=escola,
    )
    baker.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 29),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    baker.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 30),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    baker.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 31),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    return grupo_suspensao


@pytest.fixture
def grupo_suspensao_alimentacao_outra_dre(
    escola_dre_guaianases, template_mensagem_suspensao_alimentacao
):
    return baker.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola_dre_guaianases,
        rastro_escola=escola_dre_guaianases,
    )


@pytest.fixture
def grupo_suspensao_alimentacao_informado(grupo_suspensao_alimentacao):
    grupo_suspensao_alimentacao.status = InformativoPartindoDaEscolaWorkflow.INFORMADO
    grupo_suspensao_alimentacao.save()
    return grupo_suspensao_alimentacao


@pytest.fixture
def grupo_suspensao_alimentacao_escola_cancelou(grupo_suspensao_alimentacao):
    for (
        suspensao_alimentacao
    ) in grupo_suspensao_alimentacao.suspensoes_alimentacao.all():
        suspensao_alimentacao.cancelado = True
        suspensao_alimentacao.save()

    grupo_suspensao_alimentacao.status = (
        InformativoPartindoDaEscolaWorkflow.ESCOLA_CANCELOU
    )
    grupo_suspensao_alimentacao.save()
    return grupo_suspensao_alimentacao


@pytest.fixture
def motivo_suspensao_alimentacao():
    return baker.make(MotivoSuspensao, nome="Não vai ter aula")
