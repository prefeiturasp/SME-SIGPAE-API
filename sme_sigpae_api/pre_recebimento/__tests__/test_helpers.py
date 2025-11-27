from datetime import date

import pytest

from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.helpers import (
    extrair_numero_quantidade,
    filtrar_etapas,
    parse_date,
    passa_filtro_data_etapa,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.helpers import (
    formata_cnpj_ficha_tecnica,
    formata_telefone_ficha_tecnica,
)


@pytest.mark.parametrize(
    "input_quantidade,expected_output",
    [
        ("10.000,50 kg", "10.000,50"),
        ("1.500,75 L", "1.500,75"),
        ("2.000 unidades", "2.000"),
        ("500,25", "500,25"),
        ("123", "123"),
        ("", ""),
        (None, ""),
        ("sem números", "sem números"),
    ],
)
def test_extrair_numero_quantidade(input_quantidade, expected_output):
    result = extrair_numero_quantidade(input_quantidade)
    assert result == expected_output


def test_filtrar_etapas_sem_filtros(cronogramas_serialized_data):
    filtros = {}
    result = filtrar_etapas(cronogramas_serialized_data, filtros)
    assert result == cronogramas_serialized_data


def test_filtrar_etapas_filtro_data_inicial(cronogramas_serialized_data):
    filtros = {"data_inicial": "01/01/2024"}
    result = filtrar_etapas(cronogramas_serialized_data, filtros)

    for cronograma in result:
        for etapa in cronograma["etapas"]:
            data_etapa = parse_date(etapa["data_programada"])
            if data_etapa:
                assert data_etapa >= date(2024, 1, 1)


def test_filtrar_etapas_filtro_situacao_recebido(cronogramas_com_fichas_data):
    filtros = {"situacao": ["Recebido"]}
    result = filtrar_etapas(cronogramas_com_fichas_data, filtros)

    for cronograma in result:
        for etapa in cronograma["etapas"]:
            if etapa.get("fichas_recebimento"):
                assert all(
                    ficha["houve_ocorrencia"] is False
                    for ficha in etapa["fichas_recebimento"]
                )


@pytest.mark.parametrize(
    "date_str,expected",
    [
        ("01/01/2024", date(2024, 1, 1)),
        ("15/06/2023", date(2023, 6, 15)),
        ("invalid_date", None),
        ("", None),
    ],
)
def test_parse_date(date_str, expected):
    result = parse_date(date_str)
    assert result == expected


def test_passa_filtro_data_etapa():
    etapa_data = {"data_programada": "15/01/2024"}
    data_inicio = date(2024, 1, 1)
    data_fim = date(2024, 12, 31)

    assert passa_filtro_data_etapa(etapa_data, data_inicio, data_fim) is True

    data_inicio_futuro = date(2024, 2, 1)
    assert passa_filtro_data_etapa(etapa_data, data_inicio_futuro, data_fim) is False


@pytest.mark.parametrize(
    "cnpj, cnpj_formatado",
    [
        ("12345678000195", "12.345.678/0001-95"),
        ("12.345.678/0001-95", "12.345.678/0001-95"),
        ("1234567800019", "1234567800019"),
        ("", ""),
        (None, ""),
        ("00000000000000", "00.000.000/0000-00"),
        ("12.345.678/0001-9", "1234567800019"),
        ("12a345b678c0001d95", "12.345.678/0001-95"),
    ],
)
def test_formata_cnpj_ficha_tecnica(cnpj, cnpj_formatado):
    assert formata_cnpj_ficha_tecnica(cnpj) == cnpj_formatado


@pytest.mark.parametrize(
    "telefone, telefone_formatado",
    [
        ("11987654321", "11 98765 4321"),
        ("11 98765-4321", "11 98765 4321"),
        ("1198765432", "11 9876 5432"),
        ("(11) 98765-4321", "11 98765 4321"),
        ("(11)987654321", "11 98765 4321"),
        ("(11) 9876-5432", "11 9876 5432"),
        ("119876543", "119876543"),
        ("", ""),
        (None, ""),
        ("abc11987654321xyz", "11 98765 4321"),
        ("1234567890", "12 3456 7890"),
        ("12345678901", "12 34567 8901"),
        ("12345", "12345"),
    ],
)
def test_formata_telefone_ficha_tecnica(telefone, telefone_formatado):
    assert formata_telefone_ficha_tecnica(telefone) == telefone_formatado
