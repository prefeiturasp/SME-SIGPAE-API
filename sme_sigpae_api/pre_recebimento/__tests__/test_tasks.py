import pytest

from sme_sigpae_api.pre_recebimento.tasks import (
    _criar_linha_base_excel,
    _deve_mostrar_linha_a_receber,
    _processar_fichas_recebimento,
)


def test_criar_linha_base_excel():
    cronograma_mock = {
        "numero": "CR-001",
        "produto": "Arroz",
        "empresa": "Empresa X",
        "marca": "Marca Y",
        "qtd_total_programada": 1000,
        "custo_unitario_produto": "5,50",
        "armazem": "Armazém Central",
        "status": "ATIVO",
    }

    etapa_mock = {
        "etapa": "1",
        "parte": "1",
        "data_programada": "15/01/2024",
        "quantidade": "500,00 kg",
        "total_embalagens": "50",
        "unidade_medida": "kg",
    }

    result = _criar_linha_base_excel(cronograma_mock, etapa_mock)

    assert result["cronograma_numero"] == "CR-001"
    assert result["etapa"] == "1"
    assert result["parte"] == "1"
    assert "quantidade" in result


def test_processar_fichas_recebimento():
    linha_base = {"etapa": "1", "parte": "1", "situacao": ""}
    etapa = {"etapa": "1", "parte": "1"}
    fichas = [
        {"situacao": "Recebido", "houve_reposicao": False},
        {"situacao": "Reposição", "houve_reposicao": True},
    ]

    result = _processar_fichas_recebimento(linha_base, etapa, fichas)

    assert len(result) == 2
    assert result[0]["situacao"] == "Recebido"
    assert result[1]["situacao"] == "Reposição"
    assert "Reposição / Pagamento" in result[1]["etapa"]


def test_deve_mostrar_linha_a_receber(parametros_deve_mostrar_linha_a_receber):
    params = parametros_deve_mostrar_linha_a_receber
    etapa = {"foi_recebida": params["foi_recebida"]}
    filtros = (
        {"situacao": params["filtros_situacao"]} if params["filtros_situacao"] else {}
    )

    result = _deve_mostrar_linha_a_receber(etapa, params["fichas_recebimento"], filtros)
    assert result == params["expected"]
