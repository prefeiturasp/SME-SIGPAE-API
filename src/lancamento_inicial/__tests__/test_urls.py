from datetime import date

from rest_framework import status

from ..utils import eh_feriado_ou_fds


def test_get_lancamentos_por_mes(
    client_autenticado_da_escola, escola_periodo_escolar, lancamentos
):
    response = client_autenticado_da_escola.get(
        "/lancamento-diario/por-mes/",
        {"escola_periodo_escolar": escola_periodo_escolar.uuid, "mes": "10/2020"},
    )
    assert response.status_code == status.HTTP_200_OK

    dia_atual = 1
    uuid_lancamentos = [lancamento.uuid for lancamento in lancamentos]

    for dados_dia in response.json():
        assert dados_dia["dia"] == dia_atual
        objeto_data_atual = date(2020, 10, dia_atual)
        assert dados_dia["eh_feriado_ou_fds"] == eh_feriado_ou_fds(objeto_data_atual)
        if dia_atual <= 4:
            assert dados_dia["lancamento"]["uuid"] == str(
                uuid_lancamentos[dia_atual - 1]
            )
            assert dados_dia["lancamento"]["data"] == objeto_data_atual.strftime(
                "%d/%m/%Y"
            )
            assert (
                dados_dia["lancamento"]["escola_periodo_escolar"]
                == escola_periodo_escolar.id
            )

        dia_atual += 1
