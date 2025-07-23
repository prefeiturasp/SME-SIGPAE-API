import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers_create import (
    GrupoSuspensaoAlimentacaoCreateSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
)

pytestmark = pytest.mark.django_db


def test_suspensao_alimentacao_serializer(suspensao_alimentacao_serializer):
    assert suspensao_alimentacao_serializer.data is not None


def test_grupo_suspensao_alimentacao_serializer(grupo_suspensao_alimentacao_params):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    serializer_obj = GrupoSuspensaoAlimentacaoCreateSerializer(
        context={"request": FakeObject}
    )
    quantidades_por_periodo = []
    quantidades_periodo = baker.make(
        "QuantidadePorPeriodoSuspensaoAlimentacao", _quantity=3
    )
    for quantidade_periodo in quantidades_periodo:
        quantidades_por_periodo.append(
            dict(
                numero_alunos=quantidade_periodo.numero_alunos,
                periodo_escolar=quantidade_periodo.periodo_escolar,
            )
        )

    suspensoes_alimentacao = []
    suspensoes = baker.make("SuspensaoAlimentacao", _quantity=3)
    for suspensao in suspensoes:
        suspensoes_alimentacao.append(
            dict(
                prioritario=suspensao.prioritario,
                motivo=suspensao.motivo,
                data=suspensao.data,
                outro_motivo=suspensao.outro_motivo,
            )
        )
    validated_data_create = dict(
        quantidades_por_periodo=quantidades_por_periodo,
        suspensoes_alimentacao=suspensoes_alimentacao,
        escola=baker.make("Escola"),
    )
    grupo_suspensao_created = serializer_obj.create(
        validated_data=validated_data_create
    )

    assert grupo_suspensao_created.criado_por == FakeObject().user
    assert grupo_suspensao_created.quantidades_por_periodo.count() == 3
    assert grupo_suspensao_created.suspensoes_alimentacao.count() == 3
    assert isinstance(grupo_suspensao_created, GrupoSuspensaoAlimentacao)

    validated_data_update = dict(
        quantidades_por_periodo=quantidades_por_periodo[:2],
        suspensoes_alimentacao=suspensoes_alimentacao[:1],
        escola=baker.make("Escola"),
    )
    grupo_suspensao_updated = serializer_obj.update(
        instance=grupo_suspensao_created, validated_data=validated_data_update
    )
    assert grupo_suspensao_updated.criado_por == FakeObject().user
    assert grupo_suspensao_updated.quantidades_por_periodo.count() == 2
    assert grupo_suspensao_updated.suspensoes_alimentacao.count() == 1
    assert isinstance(grupo_suspensao_updated, GrupoSuspensaoAlimentacao)
