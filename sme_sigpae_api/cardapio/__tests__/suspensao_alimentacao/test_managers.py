import pytest
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-4")
def test_manager_suspensao_alimentacao_deste_mes(
    suspensao_alimentacao_parametros_mes, escola
):
    data_evento, _ = suspensao_alimentacao_parametros_mes
    grupo_suspensoes = mommy.make(GrupoSuspensaoAlimentacao, escola=escola)
    mommy.make(SuspensaoAlimentacao, data=data_evento, grupo_suspensao=grupo_suspensoes)
    assert grupo_suspensoes in GrupoSuspensaoAlimentacao.deste_mes.all()


@freeze_time("2019-10-4")
def test_manager_suspensao_alimentacao_desta_semana(
    suspensao_alimentacao_parametros_semana, escola
):
    data_evento, _ = suspensao_alimentacao_parametros_semana
    grupo_suspensoes = mommy.make(GrupoSuspensaoAlimentacao, escola=escola)
    mommy.make(SuspensaoAlimentacao, data=data_evento, grupo_suspensao=grupo_suspensoes)
    assert grupo_suspensoes in GrupoSuspensaoAlimentacao.desta_semana.all()
