import datetime

from rest_framework import status

from ...services import NovoSGPServicoLogado, NovoSGPServicoLogadoException

ENDPOINT_ALUNOS_POR_PERIODO = "quantidade-alunos-por-periodo"


ENDPOINT_LOTES = "lotes"


ENDPOINT_LISTA_DIAS = "dias-suspensao-atividades/lista-dias"


def _mock_obter_token_erro(monkeypatch):
    def _raise_login_error(self):
        raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")

    monkeypatch.setattr(NovoSGPServicoLogado, "_obter_token", _raise_login_error)


ENDPOINT_LOTES_SIMPLES = "lotes-simples"


def test_url_log_alunos_matriculados_faixa_etaria_dia(
    client_autenticado_da_escola, escola, log_alunos_matriculados_faixa_etaria_dia
):
    response = client_autenticado_da_escola.get(
        f"/log-alunos-matriculados-faixa-etaria-dia/?escola_uuid={escola.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["escola"] == escola.nome
    assert response.json()[0]["quantidade"] == 100


def test_url_endpoint_matriculados_no_mes__quantidade_por_data(
    client_autenticado_coordenador_codae,
    escola_factory,
    log_alunos_matriculados_periodo_escola_factory,
):
    escola = escola_factory.create()

    data = datetime.date.today() - datetime.timedelta(days=5)

    log_1 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=10,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )
    log_2 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=15,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )

    log_1.criado_em = data
    log_1.save(update_fields=["criado_em"])

    log_2.criado_em = data
    log_2.save(update_fields=["criado_em"])

    data_formatted = data.strftime("%Y-%m-%d")

    response = client_autenticado_coordenador_codae.get(
        f"/matriculados-no-mes/quantidade-por-data/?data={data_formatted}&escola_uuid={escola.uuid}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == 25


def test_url_endpoint_matriculados_no_mes__quantidade_por_data_dia_atual(
    client_autenticado_coordenador_codae,
    escola_factory,
    log_alunos_matriculados_periodo_escola_factory,
):
    escola = escola_factory.create()

    data = datetime.date.today()
    dia_anterior = data - datetime.timedelta(days=1)

    log_1 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=5,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )
    log_2 = log_alunos_matriculados_periodo_escola_factory.create(
        escola=escola,
        quantidade_alunos=15,
        cei_ou_emei="N/A",
        infantil_ou_fundamental="N/A",
    )

    log_1.criado_em = dia_anterior
    log_1.save(update_fields=["criado_em"])

    log_2.criado_em = dia_anterior
    log_2.save(update_fields=["criado_em"])

    data_formatted = data.strftime("%Y-%m-%d")

    response = client_autenticado_coordenador_codae.get(
        f"/matriculados-no-mes/quantidade-por-data/?data={data_formatted}&escola_uuid={escola.uuid}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == 20
