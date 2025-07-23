import pytest
from freezegun import freeze_time

from sme_sigpae_api.medicao_inicial.services.relatorio_adesao_pdf import (
    _formata_filtros,
    gera_relatorio_adesao_pdf,
)
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf(mock_exportacao_relatorio_adesao):
    resultados, query_params = mock_exportacao_relatorio_adesao
    pdf = gera_relatorio_adesao_pdf(resultados, query_params)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "RELATÓRIO DE ADESÃO DAS ALIMENTAÇÕES SERVIDAS" in texto
    assert (
        "Março - 2025 | DIRETORIA REGIONAL IPIRANGA | Lote 01, Lote 02, Lote 03 | EMEF TESTE | Período de lançamento: 05/03/2025 até 15/03/2025"
        in texto
    )
    assert "Data do Relatório: 20/07/2025" in texto
    assert texto.count("MANHA") == 1
    assert texto.count("TARDE") == 1
    assert texto.count("LANCHE") == 2
    assert texto.count("SOBREMESA") == 2
    assert texto.count("Tipo de Alimentação") == 2
    assert texto.count("Total de Alimentações Servidas") == 2
    assert texto.count("Número Total de Frequência") == 2
    assert texto.count("% de Adesão") == 2
    assert texto.count("TOTAL") == 2


def test_formata_filtros(mock_exportacao_relatorio_adesao):
    _, query_params = mock_exportacao_relatorio_adesao
    filtros = _formata_filtros(query_params)
    assert filtros == (
        "Março - 2025 | DIRETORIA REGIONAL IPIRANGA | Lote 01, Lote 02, Lote 03 | EMEF TESTE | "
        "Período de lançamento: 05/03/2025 até 15/03/2025"
    )
