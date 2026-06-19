import json

import pytest
from model_bakery import baker
from rest_framework import status

from src.escola.dias_letivos.models import DiaLetivoSIGPAE

pytestmark = pytest.mark.django_db


def _build_payload(periodos, lotes, tipos_unidades, escolas=None):
    return {
        "recorrencias": [
            {
                "data_inicial": "22/06/2026",
                "data_final": "26/06/2026",
                "periodos_escolares": [str(p.uuid) for p in periodos],
                "dias_semana": ["0", "1", "2", "3", "4"],
            }
        ],
        "lotes": [str(l.uuid) for l in lotes],
        "tipos_unidades": [str(t.uuid) for t in tipos_unidades],
        "unidades_educacionais": ([str(e.uuid) for e in escolas] if escolas else []),
    }


def test_create_dias_letivos_success(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    periodo = baker.make("escola.PeriodoEscolar")
    lote = baker.make("escola.Lote")
    tipo_unidade = baker.make("escola.TipoUnidadeEscolar")
    escola = baker.make("escola.Escola", lote=lote)

    payload = _build_payload([periodo], [lote], [tipo_unidade], [escola])

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert DiaLetivoSIGPAE.objects.count() == 5


def test_create_dias_letivos_sem_unidades_educacionais(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    periodo = baker.make("escola.PeriodoEscolar")
    lote = baker.make("escola.Lote")
    tipo_unidade = baker.make("escola.TipoUnidadeEscolar")

    payload = _build_payload([periodo], [lote], [tipo_unidade])

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    dia = DiaLetivoSIGPAE.objects.first()
    assert dia.escolas.count() == 0


def test_create_dias_letivos_duplicate(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    periodo = baker.make("escola.PeriodoEscolar")
    lote = baker.make("escola.Lote")
    tipo_unidade = baker.make("escola.TipoUnidadeEscolar")
    escola = baker.make("escola.Escola", lote=lote)

    payload = _build_payload([periodo], [lote], [tipo_unidade], [escola])

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um DiaLetivo" in response.json()[0]


def test_create_dias_letivos_duplicate_sem_escolas(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    periodo = baker.make("escola.PeriodoEscolar")
    lote = baker.make("escola.Lote")
    tipo_unidade = baker.make("escola.TipoUnidadeEscolar")

    payload = _build_payload([periodo], [lote], [tipo_unidade])

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um DiaLetivo" in response.json()[0]


def test_create_dias_letivos_missing_lotes(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [
            {
                "data_inicial": "22/06/2026",
                "data_final": "26/06/2026",
                "periodos_escolares": [],
                "dias_semana": ["0", "1"],
            }
        ],
        "tipos_unidades": [],
        "unidades_educacionais": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "lotes" in response.json()


def test_create_dias_letivos_missing_tipos_unidades(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [
            {
                "data_inicial": "22/06/2026",
                "data_final": "26/06/2026",
                "periodos_escolares": [],
                "dias_semana": ["0", "1"],
            }
        ],
        "lotes": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tipos_unidades" in response.json()


def test_create_dias_letivos_empty_recorrencias(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [],
        "lotes": [],
        "tipos_unidades": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "recorrencias" in response.json()


def test_create_dias_letivos_invalid_date_format(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [
            {
                "data_inicial": "2026-06-22",
                "data_final": "2026-06-26",
                "periodos_escolares": [],
                "dias_semana": ["0", "1"],
            }
        ],
        "lotes": [],
        "tipos_unidades": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_dias_letivos_data_inicial_maior_que_final(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [
            {
                "data_inicial": "30/06/2026",
                "data_final": "22/06/2026",
                "periodos_escolares": [],
                "dias_semana": ["0", "1"],
            }
        ],
        "lotes": [],
        "tipos_unidades": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "data_inicial não pode ser maior" in str(response.json())


def test_create_dias_letivos_dia_semana_out_of_range(
    client_autenticado_codae_gestao_alimentacao,
):
    client = client_autenticado_codae_gestao_alimentacao
    payload = {
        "recorrencias": [
            {
                "data_inicial": "22/06/2026",
                "data_final": "26/06/2026",
                "periodos_escolares": [],
                "dias_semana": ["7", "8"],
            }
        ],
        "lotes": [],
        "tipos_unidades": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_dias_letivos_unauthenticated(client):
    payload = {
        "recorrencias": [
            {
                "data_inicial": "22/06/2026",
                "data_final": "26/06/2026",
                "periodos_escolares": [],
                "dias_semana": ["0", "1"],
            }
        ],
        "lotes": [],
        "tipos_unidades": [],
    }

    response = client.post(
        "/dias-letivos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
