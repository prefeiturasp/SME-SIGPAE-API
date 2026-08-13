import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
from datetime import date
from src.pre_recebimento.cronograma_semanal.models import CronogramaSemanal, ProgramacaoEntregaSemanal

pytestmark = pytest.mark.django_db


def test_list_cronogramas_semanais_filtro_periodo(
    client_autenticado_vinculo_dilog_cronograma,
    cronograma_ponto_a_ponto_assinado,
):
    client, _ = client_autenticado_vinculo_dilog_cronograma
    url = "/cronogramas-semanais/"

    params = {
        "data_inicial": "01/01/2026",
        "data_final": "26/07/2026",
    }

    # 1. Cronograma DENTRO do período (Março)
    cs_dentro = baker.make(CronogramaSemanal, cronograma_mensal=cronograma_ponto_a_ponto_assinado)
    baker.make(
        ProgramacaoEntregaSemanal,
        cronograma_semanal=cs_dentro,
        data_inicio=date(2026, 3, 1),
        data_fim=date(2026, 3, 5)
    )

    # 2. Cronograma TOTALMENTE ANTES (Dezembro/2025)
    cs_antes = baker.make(CronogramaSemanal, cronograma_mensal=cronograma_ponto_a_ponto_assinado)
    baker.make(
        ProgramacaoEntregaSemanal,
        cronograma_semanal=cs_antes,
        data_inicio=date(2025, 12, 1),
        data_fim=date(2025, 12, 10)
    )

    # 3. Cronograma TOTALMENTE DEPOIS (Agosto/2026)
    cs_depois = baker.make(CronogramaSemanal, cronograma_mensal=cronograma_ponto_a_ponto_assinado)
    baker.make(
        ProgramacaoEntregaSemanal,
        cronograma_semanal=cs_depois,
        data_inicio=date(2026, 8, 1),
        data_fim=date(2026, 8, 10)
    )

    # 4. Cronograma com duas programações, mas nenhuma no período
    cs_misto_fora = baker.make(CronogramaSemanal, cronograma_mensal=cronograma_ponto_a_ponto_assinado)
    baker.make(ProgramacaoEntregaSemanal, cronograma_semanal=cs_misto_fora,
               data_inicio=date(2025, 1, 1), data_fim=date(2025, 1, 1))
    baker.make(ProgramacaoEntregaSemanal, cronograma_semanal=cs_misto_fora,
               data_inicio=date(2027, 1, 1), data_fim=date(2027, 1, 1))

    response = client.get(url, params)

    assert response.status_code == status.HTTP_200_OK

    # Extrair UUIDs retornados
    results = response.data.get('results', response.data)
    uuids_retornados = [item['uuid'] for item in results]

    assert str(cs_dentro.uuid) in uuids_retornados, "Cronograma dentro do prazo deveria listar"
    assert str(cs_antes.uuid) not in uuids_retornados, "Cronograma passado não deveria listar"
    assert str(cs_depois.uuid) not in uuids_retornados, "Cronograma futuro não deveria listar"
    assert str(cs_misto_fora.uuid) not in uuids_retornados, "Cronograma sem interseção real não deveria listar"
    assert len(uuids_retornados) == 1
