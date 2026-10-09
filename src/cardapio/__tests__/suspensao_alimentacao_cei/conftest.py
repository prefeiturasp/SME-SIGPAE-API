import datetime
import pytest

from types import SimpleNamespace
from unittest.mock import patch
from model_bakery import baker

from src.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns.constants import StringsCaminhoModelos
from src.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    SuspensaoAlimentacaodeCEICreateSerializer,
)

MODULO_SERIALIZER = "src.cardapio.suspensao_alimentacao_cei.api.serializers_create"
DATA_CEI = datetime.date(2026, 10, 30)

@pytest.fixture(
    params=[
        # data_create , data_update
        (datetime.date(2019, 10, 17), datetime.date(2019, 10, 18)),
    ]
)
def suspensao_alimentacao_cei_params(request):
    motivo = baker.make(
        "cardapio.MotivoSuspensao",
        nome="outro",
        uuid="478b09e1-4c14-4e50-a446-fbc0af727a08",
    )

    data_create, data_update = request.param
    return motivo, data_create, data_update


@pytest.fixture
def suspensao_alimentacao_de_cei(escola):
    motivo = baker.make(MotivoSuspensao, nome="Suspensão de aula")
    periodos_escolares = baker.make(
        StringsCaminhoModelos.MODEL_PERIODOESCOLAR.value, _quantity=2
    )
    return baker.make(
        SuspensaoAlimentacaoDaCEI,
        escola=escola,
        motivo=motivo,
        periodos_escolares=periodos_escolares,
        data=datetime.date(2020, 4, 20),
    )


@pytest.fixture
def contexto_request():
    return {"request": SimpleNamespace(user=baker.make(StringsCaminhoModelos.MODEL_USUARIO.value))}


@pytest.fixture(autouse=True)
def sem_validacao_de_data():
    """Neutraliza as regras de data para isolar a regra de duplicidade."""
    with patch(f"{MODULO_SERIALIZER}.nao_pode_ser_no_passado"), patch(
        f"{MODULO_SERIALIZER}.deve_pedir_com_antecedencia"
    ), patch(f"{MODULO_SERIALIZER}.deve_ser_no_mesmo_ano_corrente"):
        yield


@pytest.fixture
def periodo_escolar_cei():
    return baker.make(StringsCaminhoModelos.MODEL_PERIODOESCOLAR.value)


@pytest.fixture
def motivo_cei():
    return baker.make(MotivoSuspensao, nome="Não vai ter aula")


@pytest.fixture
def monta_payload_cei(escola, motivo_cei, periodo_escolar_cei):
    def _monta(data=DATA_CEI, **overrides):
        base = {
            "escola": escola,
            "motivo": motivo_cei,
            "periodos_escolares": [periodo_escolar_cei],
        }
        d = {**base, **overrides}
        return {
            "escola": str(d["escola"].uuid),
            "motivo": str(d["motivo"].uuid),
            "periodos_escolares": [str(p.uuid) for p in d["periodos_escolares"]],
            "data": data.strftime("%Y-%m-%d"),
        }

    return _monta


@pytest.fixture
def serializer_cei(contexto_request):
    def _cria(data, instance=None):
        return SuspensaoAlimentacaodeCEICreateSerializer(
            instance=instance, data=data, context=contexto_request
        )

    return _cria


@pytest.fixture
def cria_suspensao_cei(escola, motivo_cei):
    def _cria(status="INFORMADO", **kwargs):
        kwargs.setdefault("escola", escola)
        kwargs.setdefault("motivo", motivo_cei)
        kwargs.setdefault("data", DATA_CEI)
        return baker.make(SuspensaoAlimentacaoDaCEI, status=status, **kwargs)

    return _cria
