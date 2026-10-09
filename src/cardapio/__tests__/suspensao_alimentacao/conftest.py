import datetime
from types import SimpleNamespace

import pytest
from model_bakery import baker

from src.cardapio.suspensao_alimentacao.api.serializers import (
    SuspensaoAlimentacaoSerializer,
)
from src.cardapio.suspensao_alimentacao.api.serializers_create import (
    GrupoSuspensaoAlimentacaoCreateSerializer,
)
from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from src.dados_comuns.fluxo_status import InformativoPartindoDaEscolaWorkflow


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
def grupo_suspensao_alimentacao_outra_dre(escola_dre_guaianases):
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


@pytest.fixture
def contexto_request():
    usuario = baker.make("perfil.Usuario")
    return {"request": SimpleNamespace(user=usuario)}


@pytest.fixture
def periodo_escolar_suspensao():
    return baker.make("PeriodoEscolar")


@pytest.fixture
def tipo_alimentacao_suspensao():
    return baker.make("TipoAlimentacao")


@pytest.fixture
def dados_base(
    escola,
    motivo_suspensao_alimentacao,
    periodo_escolar_suspensao,
    tipo_alimentacao_suspensao,
):
    return {
        "escola": escola,
        "periodo": periodo_escolar_suspensao,
        "tipo": tipo_alimentacao_suspensao,
        "motivo": motivo_suspensao_alimentacao,
    }


@pytest.fixture
def monta_payload(dados_base):
    """Factory: devolve o payload; aceita sobrescrever campos de dados_base e a data."""

    def _monta(data="30/10/2026", **overrides):
        d = {**dados_base, **overrides}
        return {
            "escola": str(d["escola"].uuid),
            "quantidades_por_periodo": [
                {
                    "numero_alunos": "1",
                    "periodo_escolar": str(d["periodo"].uuid),
                    "tipos_alimentacao": [str(d["tipo"].uuid)],
                }
            ],
            "suspensoes_alimentacao": [
                {"data": data, "motivo": str(d["motivo"].uuid), "outro_motivo": ""}
            ],
        }

    return _monta


@pytest.fixture
def serializer_create(contexto_request):
    """Factory: cria o serializer já com o contexto."""

    def _cria(data, instance=None):
        return GrupoSuspensaoAlimentacaoCreateSerializer(
            instance=instance, data=data, context=contexto_request
        )

    return _cria


@pytest.fixture
def grupo_criado_informado(monta_payload, serializer_create):
    ser = serializer_create(monta_payload())
    assert ser.is_valid(), ser.errors
    grupo = ser.save()
    # RASCUNHO libera duplicidade; INFORMADO bloqueia
    GrupoSuspensaoAlimentacao.objects.filter(pk=grupo.pk).update(
        status=InformativoPartindoDaEscolaWorkflow.INFORMADO
    )
    return grupo
