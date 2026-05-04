import pytest
from freezegun import freeze_time
from model_bakery import baker

from ..models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoNormal,
)

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-4")
def test_manager_inclusao_continua_desta_semana(
    inclusao_alimentacao_continua_parametros_semana, escola
):
    data_inicial, data_final = inclusao_alimentacao_continua_parametros_semana

    inclusao_continua = baker.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
    )
    assert inclusao_continua in InclusaoAlimentacaoContinua.desta_semana.all()


@freeze_time("2019-10-4")
def test_manager_inclusao_continua_deste_mes(
    inclusao_alimentacao_continua_parametros_mes, escola
):
    data_inicial, data_final = inclusao_alimentacao_continua_parametros_mes

    inclusao_continua = baker.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        escola=escola,
        data_final=data_final,
    )
    assert inclusao_continua in InclusaoAlimentacaoContinua.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inclusao_continua_vencidos(
    inclusao_alimentacao_continua_parametros_vencidos, escola
):
    data_inicial, data_final, status = inclusao_alimentacao_continua_parametros_vencidos

    inclusao_continua = baker.make(
        InclusaoAlimentacaoContinua,
        data_inicial=data_inicial,
        data_final=data_final,
        escola=escola,
        status=status,
    )
    assert inclusao_continua in InclusaoAlimentacaoContinua.vencidos.all()


@freeze_time("2019-10-4")
def test_manager_inclusoes_normais_desta_semana(
    inclusao_alimentacao_continua_parametros_semana, escola
):
    data_evento, _ = inclusao_alimentacao_continua_parametros_semana

    grupo_inclusoes = baker.make(GrupoInclusaoAlimentacaoNormal, escola=escola)
    baker.make(
        InclusaoAlimentacaoNormal, data=data_evento, grupo_inclusao=grupo_inclusoes
    )
    assert grupo_inclusoes in GrupoInclusaoAlimentacaoNormal.desta_semana.all()


@freeze_time("2019-10-4")
def test_manager_inclusoes_normais_deste_mes(
    inclusao_alimentacao_continua_parametros_mes, escola
):
    data_evento, _ = inclusao_alimentacao_continua_parametros_mes

    grupo_inclusoes = baker.make(GrupoInclusaoAlimentacaoNormal, escola=escola)
    baker.make(
        InclusaoAlimentacaoNormal, data=data_evento, grupo_inclusao=grupo_inclusoes
    )
    assert grupo_inclusoes in GrupoInclusaoAlimentacaoNormal.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_inclusoes_normais_vencidos(
    inclusao_alimentacao_continua_parametros_vencidos, escola
):
    data_evento, _, status = inclusao_alimentacao_continua_parametros_vencidos

    grupo_inclusoes = baker.make(
        GrupoInclusaoAlimentacaoNormal, status=status, escola=escola
    )
    baker.make(
        InclusaoAlimentacaoNormal, data=data_evento, grupo_inclusao=grupo_inclusoes
    )
    assert grupo_inclusoes in GrupoInclusaoAlimentacaoNormal.vencidos.all()
