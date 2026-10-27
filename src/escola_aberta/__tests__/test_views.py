import pytest
from rest_framework import status

from src.escola_aberta.models import (
    EscolaAberta,
    EscolaAbertaUnidadeParticipante,
)

@pytest.mark.django_db
def test_criar_escola_aberta_sucesso(
    client_autenticado_coordenador_codae, setup_escola_aberta_data
):
    """Testa cadastro completo com persistência das unidades e tipos de alimentação."""
    payload = {
        "recorrencias": {
            "data_inicial": "12/10/2026",
            "data_final": "23/10/2026",
            "dias_semana": ["0", "6"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [
                    str(setup_escola_aberta_data["tipo_alim_1"].uuid),
                    str(setup_escola_aberta_data["tipo_alim_2"].uuid),
                ],
                "num_participantes": 30,
            },
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_2"].uuid),
                "tipos_alimentacao": [str(setup_escola_aberta_data["tipo_alim_1"].uuid)],
                "num_participantes": 20,
            },
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_escola_aberta_data["list_url"], payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert EscolaAberta.objects.count() == 1
    assert EscolaAbertaUnidadeParticipante.objects.count() == 2

    instance = EscolaAberta.objects.first()
    assert instance.data_inicial.strftime("%d/%m/%Y") == "12/10/2026"
    assert instance.data_final.strftime("%d/%m/%Y") == "23/10/2026"
    assert sorted(instance.dias_semana) == ["0", "6"]

    unidade_1 = instance.unidades_participantes.get(
        unidade_educacional=setup_escola_aberta_data["escola_1"]
    )
    assert unidade_1.tipos_alimentacao.count() == 2


@pytest.mark.django_db
def test_listar_escola_aberta(client_autenticado_coordenador_codae, setup_escola_aberta_data):
    """Testa listagem e campos serializados no retorno do get."""
    escola_aberta = EscolaAberta.objects.create(
        data_inicial="2026-10-12",
        data_final="2026-10-23",
        dias_semana=["0", "6"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
    )
    unidade.tipos_alimentacao.add(setup_escola_aberta_data["tipo_alim_1"])

    response = client_autenticado_coordenador_codae.get(setup_escola_aberta_data["list_url"])

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] >= 1
    assert "results" in response.data

    item = response.data["results"][0]
    assert item["uuid"] == str(escola_aberta.uuid)
    assert item["data_inicial"] == "12/10/2026"
    assert item["data_final"] == "23/10/2026"
    assert len(item["unidades_participantes"]) == 1
    assert (
        item["unidades_participantes"][0]["unidade_educacional"]
        == str(setup_escola_aberta_data["escola_1"].uuid)
    )
    assert item["unidades_participantes"][0]["lote_nome"] == (
        f"{setup_escola_aberta_data['lote'].nome} - "
        f"{setup_escola_aberta_data['lote'].diretoria_regional.iniciais}"
    )


@pytest.mark.django_db
def test_criar_escola_aberta_salva_num_participantes(
    client_autenticado_coordenador_codae, setup_escola_aberta_data
):
    payload = {
        "recorrencias": {
            "data_inicial": "12/10/2026",
            "data_final": "23/10/2026",
            "dias_semana": ["0", "6"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [
                    str(setup_escola_aberta_data["tipo_alim_1"].uuid)
                ],
                "num_participantes": 40,
            }
        ],
    }
    response = client_autenticado_coordenador_codae.post(
        setup_escola_aberta_data["list_url"], payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    unidade = EscolaAbertaUnidadeParticipante.objects.get()
    assert unidade.num_participantes == 40
    assert response.data["unidades_participantes"][0]["num_participantes"] == 40


@pytest.mark.django_db
def test_atualizar_escola_aberta_put_sucesso(
    client_autenticado_coordenador_codae, setup_escola_aberta_data
):
    """PUT altera período, dias, unidades, tipos e num_participantes."""
    escola_aberta = EscolaAberta.objects.create(
        data_inicial="2026-10-12",
        data_final="2026-10-23",
        dias_semana=["0", "6"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
    )
    unidade.tipos_alimentacao.add(setup_escola_aberta_data["tipo_alim_1"])

    payload = {
        "recorrencias": {
            "data_inicial": "14/10/2026",
            "data_final": "30/10/2026",
            "dias_semana": ["1", "3"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_2"].uuid),
                "tipos_alimentacao": [
                    str(setup_escola_aberta_data["tipo_alim_2"].uuid)
                ],
                "num_participantes": 55,
            }
        ],
    }
    url = f"{setup_escola_aberta_data['list_url']}{escola_aberta.uuid}/"
    response = client_autenticado_coordenador_codae.put(
        url, payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK
    escola_aberta.refresh_from_db()
    assert escola_aberta.data_inicial.strftime("%d/%m/%Y") == "14/10/2026"
    assert escola_aberta.data_final.strftime("%d/%m/%Y") == "30/10/2026"
    assert sorted(escola_aberta.dias_semana) == ["1", "3"]

    unidades = escola_aberta.unidades_participantes.all()
    assert unidades.count() == 1
    nova = unidades.first()
    assert nova.unidade_educacional == setup_escola_aberta_data["escola_2"]
    assert nova.num_participantes == 55
    assert list(nova.tipos_alimentacao.all()) == [
        setup_escola_aberta_data["tipo_alim_2"]
    ]
    assert EscolaAberta.objects.count() == 1


@pytest.mark.django_db
def test_criar_escola_aberta_duplicada_retorna_400(
    client_autenticado_coordenador_codae, setup_escola_aberta_data
):
    """Garante que a API retorna erro 400 com mensagem em caso de sobreposição."""
    escola_aberta = EscolaAberta.objects.create(
        data_inicial="2026-10-10",
        data_final="2026-10-20",
        dias_semana=["0", "6"],
    )
    unidade = EscolaAbertaUnidadeParticipante.objects.create(
        escola_aberta=escola_aberta,
        lote=setup_escola_aberta_data["lote"],
        unidade_educacional=setup_escola_aberta_data["escola_1"],
        num_participantes=10,
    )
    unidade.tipos_alimentacao.add(setup_escola_aberta_data["tipo_alim_1"])

    payload_conflitante = {
        "recorrencias": {
            "data_inicial": "15/10/2026",
            "data_final": "25/10/2026",
            "dias_semana": ["0"],
        },
        "unidades_participantes": [
            {
                "lote": str(setup_escola_aberta_data["lote"].uuid),
                "unidade_educacional": str(setup_escola_aberta_data["escola_1"].uuid),
                "tipos_alimentacao": [
                    str(setup_escola_aberta_data["tipo_alim_1"].uuid)
                ],
                "num_participantes": 15,
            }
        ],
    }

    response = client_autenticado_coordenador_codae.post(
        setup_escola_aberta_data["list_url"],
        payload_conflitante,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um cadastro com esta combinação de UE" in str(
        response.data.get("non_field_errors", [])
    )
