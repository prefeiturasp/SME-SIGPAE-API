import json
from datetime import date, timedelta
from django.utils import timezone
from typing import Any

import pytest
from django.test import Client
from model_bakery import baker
from rest_framework import status

from src.escola.dias_letivos.fixtures.factories.dias_letivos_factory import (
    DiaLetivoSIGPAEFactory,
)
from src.escola.dias_letivos.models import DiaLetivoSIGPAE
from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar
from src.terceirizada.models import Contrato, Edital

pytestmark = pytest.mark.django_db


def _build_payload(
    periodos: list[PeriodoEscolar],
    lotes: list[Lote],
    tipos_unidades: list[TipoUnidadeEscolar],
    escolas: list[Escola] | None = None,
) -> dict[str, Any]:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
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


def test_create_dias_letivos_unauthenticated(client: Client) -> None:
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


def test_list_dias_letivos_com_unidades(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao
    edital = baker.make(Edital, numero="123/2026")
    contrato = baker.make(Contrato, edital=edital, encerrado=False)
    lote = baker.make(Lote, nome="Lote A", iniciais="LA")
    lote.contratos_do_lote.add(contrato)
    periodo = baker.make(PeriodoEscolar, nome="Manhã")
    tipo_ue = baker.make(TipoUnidadeEscolar, iniciais="EMEF")
    escola = baker.make(Escola, nome="EMEF Teste", lote=lote)

    DiaLetivoSIGPAEFactory(
        data=date(2026, 6, 22),
        lotes=[lote],
        tipos_unidade_escolar=[tipo_ue],
        periodos_escolares=[periodo],
        escolas=[escola],
    )

    response = client.get("/dias-letivos/", {"mes": 6, "ano": 2026})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    item = data[0]
    assert item["data"] == "22/06/2026"
    assert len(item["lotes"]) == 1
    assert item["lotes"][0]["nome"] == lote.nome
    assert item["lotes"][0]["iniciais"] == lote.iniciais
    assert len(item["tipos_unidade_escolar"]) == 1
    assert item["tipos_unidade_escolar"][0]["iniciais"] == "EMEF"
    assert len(item["periodos_escolares"]) == 1
    assert item["periodos_escolares"][0]["nome"] == "Manhã"
    assert item["unidades_escolares"] == "EMEF Teste"
    assert item["editais_numeros"] == ["123/2026"]


def test_list_dias_letivos_sem_unidades(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao
    edital = baker.make(Edital, numero="456/2026")
    contrato = baker.make(Contrato, edital=edital, encerrado=False)
    lote = baker.make(Lote, nome="Lote B", iniciais="LB")
    lote.contratos_do_lote.add(contrato)
    periodo = baker.make(PeriodoEscolar, nome="Tarde")
    tipo_ue = baker.make(TipoUnidadeEscolar, iniciais="CEI")

    DiaLetivoSIGPAEFactory(
        data=date(2026, 6, 23),
        lotes=[lote],
        tipos_unidade_escolar=[tipo_ue],
        periodos_escolares=[periodo],
    )

    response = client.get("/dias-letivos/", {"mes": 6, "ano": 2026})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    item = data[0]
    assert item["data"] == "23/06/2026"
    assert len(item["lotes"]) == 1
    assert item["lotes"][0]["nome"] == lote.nome
    assert item["lotes"][0]["iniciais"] == lote.iniciais
    assert len(item["tipos_unidade_escolar"]) == 1
    assert item["tipos_unidade_escolar"][0]["iniciais"] == "CEI"
    assert len(item["periodos_escolares"]) == 1
    assert item["periodos_escolares"][0]["nome"] == "Tarde"
    assert item["unidades_escolares"] is None
    assert item["editais_numeros"] == ["456/2026"]


def test_list_dias_letivos_filtro_mes_obrigatorio(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao

    response = client.get("/dias-letivos/", {"ano": 2026})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "mes" in response.json()


def test_list_dias_letivos_filtro_ano_obrigatorio(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao

    response = client.get("/dias-letivos/", {"mes": 6})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ano" in response.json()


def test_retrieve_dia_letivo_success(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao
    dia = DiaLetivoSIGPAEFactory()

    response = client.get(f"/dias-letivos/{dia.uuid}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(dia.uuid)
    # Verifica se retornou as listas de UUIDs conforme o DetailSerializer
    assert isinstance(response.json()["lotes"], list)


def test_update_dia_letivo_success(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao
    dia = DiaLetivoSIGPAEFactory()
    novo_lote = baker.make(Lote)
    periodo = baker.make(PeriodoEscolar)
    tipo = baker.make(TipoUnidadeEscolar)

    payload = {
        "lotes": [str(novo_lote.uuid)],
        "tipos_unidades": [str(tipo.uuid)],
        "unidades_educacionais": [],
        "periodos_escolares": [str(periodo.uuid)]
    }

    response = client.put(
        f"/dias-letivos/{dia.uuid}/",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK
    dia.refresh_from_db()
    assert dia.lotes.filter(uuid=novo_lote.uuid).exists()


def test_update_dia_letivo_duplicate_error(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao

    lote = baker.make("escola.Lote")
    tipo_unidade = baker.make("escola.TipoUnidadeEscolar")
    periodo = baker.make("escola.PeriodoEscolar")

    future_date = date.today() + timedelta(days=30)

    dia_1 = DiaLetivoSIGPAEFactory(data=future_date)
    dia_1.lotes.add(lote)
    dia_1.tipos_unidade_escolar.add(tipo_unidade)
    dia_1.periodos_escolares.add(periodo)

    dia_2 = DiaLetivoSIGPAEFactory(data=future_date)
    dia_2.lotes.add(lote)
    dia_2.tipos_unidade_escolar.add(tipo_unidade)
    periodo_2 = baker.make("escola.PeriodoEscolar")
    dia_2.periodos_escolares.add(periodo_2)

    payload = {
        "lotes": [str(lote.uuid)],
        "tipos_unidades": [str(tipo_unidade.uuid)],
        "unidades_educacionais": [],
        "periodos_escolares": [str(periodo.uuid)],
    }

    response = client.put(
        f"/dias-letivos/{dia_2.uuid}/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe um DiaLetivo" in str(response.json())


def test_delete_dia_letivo_success(
    client_autenticado_codae_gestao_alimentacao: Client,
) -> None:
    client = client_autenticado_codae_gestao_alimentacao
    dia = DiaLetivoSIGPAEFactory()

    response = client.delete(f"/dias-letivos/{dia.uuid}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not DiaLetivoSIGPAE.objects.filter(uuid=dia.uuid).exists()


def test_delete_dia_letivo_unauthorized(client: Client) -> None:
    dia = DiaLetivoSIGPAEFactory()

    response = client.delete(f"/dias-letivos/{dia.uuid}/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
