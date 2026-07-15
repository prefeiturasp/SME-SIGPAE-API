import pytest
from freezegun import freeze_time
from model_bakery import baker

from ..api.serializers.serializers_create import (
    GrupoInclusaoAlimentacaoNormalCreationSerializer,
    InclusaoAlimentacaoContinuaCreationSerializer,
    InclusaoAlimentacaoDaCEICreateSerializer,
)
from ..models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
)

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-15")
def test_inclusao_continua_serializer_validators(
    inclusao_alimentacao_continua_parametros,
):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    data_inicial, data_final = inclusao_alimentacao_continua_parametros
    attrs = dict(data_inicial=data_inicial, data_final=data_final)
    quantidades_por_periodo = []
    for _ in range(4):
        qtd = baker.make("QuantidadePorPeriodo")
        quantidades_por_periodo.append(
            dict(
                numero_alunos=qtd.numero_alunos,
                periodo_escolar=qtd.periodo_escolar,
                tipos_alimentacao=[],
            )
        )

    serializer_obj = InclusaoAlimentacaoContinuaCreationSerializer(
        context={"request": FakeObject}
    )
    resp_inicial = serializer_obj.validate_data_inicial(data_inicial)
    resp_final = serializer_obj.validate_data_final(data_final)
    resp_qtd_periodo = serializer_obj.validate_quantidades_periodo(
        quantidades_por_periodo
    )
    resp_attrs = serializer_obj.validate(attrs=attrs)

    assert resp_inicial == data_inicial
    assert resp_final == data_final
    assert resp_attrs == attrs
    assert resp_qtd_periodo == quantidades_por_periodo


@freeze_time("2019-10-15")
def test_inclusao_continua_serializer_creators(
    inclusao_alimentacao_continua_parametros, escola
):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    motivo = baker.make("MotivoInclusaoContinua")
    data_inicial, data_final = inclusao_alimentacao_continua_parametros
    quantidades_por_periodo = []
    for _ in range(4):
        qtd = baker.make("QuantidadePorPeriodo")
        quantidades_por_periodo.append(
            dict(
                numero_alunos=qtd.numero_alunos,
                periodo_escolar=qtd.periodo_escolar,
                tipos_alimentacao=[],
            )
        )

    serializer_obj = InclusaoAlimentacaoContinuaCreationSerializer(
        context={"request": FakeObject}
    )
    validated_data = dict(
        quantidades_periodo=quantidades_por_periodo,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        motivo=motivo,
    )
    validated_data_update = dict(
        quantidades_periodo=quantidades_por_periodo[:3],
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        motivo=motivo,
    )

    inclusao_continua_obj = serializer_obj.create(validated_data=validated_data)
    assert isinstance(inclusao_continua_obj, InclusaoAlimentacaoContinua)
    assert inclusao_continua_obj.data_inicial == data_inicial
    assert inclusao_continua_obj.data_final == data_final
    assert inclusao_continua_obj.escola == escola
    assert inclusao_continua_obj.motivo == motivo
    assert inclusao_continua_obj.quantidades_periodo.count() == 4
    assert inclusao_continua_obj.criado_por == FakeObject.user

    inclusao_continua_obj_updated = serializer_obj.update(
        instance=inclusao_continua_obj, validated_data=validated_data_update
    )
    assert isinstance(inclusao_continua_obj_updated, InclusaoAlimentacaoContinua)
    assert inclusao_continua_obj.quantidades_periodo.count() == 3


@freeze_time("2019-10-15")
def test_grupo_inclusao_normal_serializer_creators(
    inclusao_alimentacao_continua_parametros, escola
):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    data, _ = inclusao_alimentacao_continua_parametros
    quantidades_por_periodo = []
    for _ in range(4):
        qtd = baker.make("QuantidadePorPeriodo")
        quantidades_por_periodo.append(
            dict(
                numero_alunos=qtd.numero_alunos,
                periodo_escolar=qtd.periodo_escolar,
                tipos_alimentacao=[],
            )
        )
    inclusoes = []
    for _ in range(5):
        inclusao_normal = baker.make("InclusaoAlimentacaoNormal", data=data)
        inclusoes.append(
            dict(
                motivo=inclusao_normal.motivo,
                outro_motivo=inclusao_normal.outro_motivo,
                data=inclusao_normal.data,
            )
        )

    serializer_obj = GrupoInclusaoAlimentacaoNormalCreationSerializer(
        context={"request": FakeObject}
    )
    validated_data = dict(
        quantidades_periodo=quantidades_por_periodo, escola=escola, inclusoes=inclusoes
    )

    response_inclusao_created = serializer_obj.create(validated_data=validated_data)
    assert isinstance(response_inclusao_created, GrupoInclusaoAlimentacaoNormal)
    assert response_inclusao_created.criado_por == FakeObject.user
    assert response_inclusao_created.inclusoes.count() == 5
    assert response_inclusao_created.quantidades_periodo.count() == 4

    validated_data_update = dict(
        quantidades_periodo=quantidades_por_periodo[:1],
        escola=escola,
        inclusoes=inclusoes[:2],
    )
    response_inclusao_updated = serializer_obj.update(
        instance=response_inclusao_created, validated_data=validated_data_update
    )

    assert response_inclusao_updated.inclusoes.count() == 2
    assert response_inclusao_updated.quantidades_periodo.count() == 1


@freeze_time("2019-10-15")
def test_grupo_inclusao_alimentacao_cei(
    inclusao_alimentacao_continua_parametros, escola
):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    data, _ = inclusao_alimentacao_continua_parametros
    quantidade_alunos_por_faixas_etarias = []
    for _ in range(5):
        quantidade = baker.make(
            "QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI"
        )
        quantidade_alunos_por_faixas_etarias.append(
            dict(
                faixa_etaria=quantidade.faixa_etaria,
                quantidade_alunos=quantidade.quantidade_alunos,
            )
        )

    periodo_escolar = baker.make("escola.PeriodoEscolar")
    motivo = baker.make("MotivoInclusaoNormal")

    serializer_obj = InclusaoAlimentacaoDaCEICreateSerializer(
        context={"request": FakeObject}
    )
    validated_data = dict(
        quantidade_alunos_por_faixas_etarias=quantidade_alunos_por_faixas_etarias,
        escola=escola,
        periodo_escolar=periodo_escolar,
        dias_motivos_da_inclusao_cei=[{"motivo": motivo, "data": data}],
    )
    response_inclusao_created = serializer_obj.create(validated_data=validated_data)
    assert isinstance(response_inclusao_created, InclusaoAlimentacaoDaCEI)

    validated_data_update = dict(
        quantidade_alunos_por_faixas_etarias=quantidade_alunos_por_faixas_etarias,
        escola=escola,
        periodo_escolar=periodo_escolar,
        dias_motivos_da_inclusao_cei=[{"motivo": motivo, "data": data}],
    )

    response_inclusao_updated = serializer_obj.update(
        instance=response_inclusao_created, validated_data=validated_data_update
    )

    assert response_inclusao_updated.quantidade_alunos_por_faixas_etarias.count() == 5
