import io

import pytest
from freezegun import freeze_time
from pypdf import PdfReader

from src.medicao_inicial.services.relatorio_adesao_pdf import (
    _formata_filtros,
    gera_relatorio_adesao_pdf,
)
from src.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf(mock_exportacao_relatorio_adesao):
    resultados, query_params = mock_exportacao_relatorio_adesao
    pdf = gera_relatorio_adesao_pdf(resultados, query_params)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "RELATÓRIO DE ADESÃO DAS ALIMENTAÇÕES SERVIDAS" in texto
    assert (
        "Março 2025 | Lote 01, Lote 02, Lote 03 - DRE DIRETORIA REGIONAL IPIRANGA | EMEF TESTE | PERÍODO DE LANÇAMENTO: DE 05/03/2025 ATÉ 15/03/2025"
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
        "Março 2025 | Lote 01, Lote 02, Lote 03 - DRE DIRETORIA REGIONAL IPIRANGA | EMEF TESTE | "
        "PERÍODO DE LANÇAMENTO: DE 05/03/2025 ATÉ 15/03/2025"
    )


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf_por_escola_uma_pagina_por_escola(
    mock_exportacao_relatorio_adesao,
):
    resultados_agregados, query_params = mock_exportacao_relatorio_adesao
    resultados_por_escola = [
        {
            "escola": {"nome": "EMEF TESTE A", "codigo_eol": "123456"},
            "resultados": resultados_agregados,
        },
        {
            "escola": {"nome": "EMEF TESTE B", "codigo_eol": "654321"},
            "resultados": resultados_agregados,
        },
    ]

    pdf = gera_relatorio_adesao_pdf(resultados_por_escola, query_params)
    assert isinstance(pdf, bytes)

    pdf_reader = PdfReader(io.BytesIO(pdf))
    assert len(pdf_reader.pages) == 2

    texto_por_pagina = [
        page.extract_text().replace("\n", " ") for page in pdf_reader.pages
    ]
    assert "EMEF TESTE A" in texto_por_pagina[0]
    assert "EMEF TESTE B" in texto_por_pagina[1]

    assert "EMEF TESTE A" not in texto_por_pagina[1]
    assert "EMEF TESTE B" not in texto_por_pagina[0]

    for texto_pagina in texto_por_pagina:
        assert "RELATÓRIO DE ADESÃO DAS ALIMENTAÇÕES SERVIDAS" in texto_pagina
        assert "PERÍODO DE LANÇAMENTO: DE 05/03/2025 ATÉ 15/03/2025" in texto_pagina
        assert "Data do Relatório: 20/07/2025" in texto_pagina


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf_por_escola_filtros_por_pagina(
    mock_exportacao_relatorio_adesao,
):
    _, query_params = mock_exportacao_relatorio_adesao
    resultados_por_escola = [
        {
            "escola": {"nome": "EMEF TESTE A", "codigo_eol": "123456"},
            "resultados": {
                "MANHA": {
                    "LANCHE": {
                        "total_servido": 140,
                        "total_frequencia": 755,
                        "total_adesao": 0.1854,
                    }
                }
            },
        },
        {
            "escola": {"nome": "EMEF TESTE B", "codigo_eol": "654321"},
            "resultados": {
                "TARDE": {
                    "REFEIÇÃO": {
                        "total_servido": 130,
                        "total_frequencia": 745,
                        "total_adesao": 0.1745,
                    }
                }
            },
        },
    ]

    pdf = gera_relatorio_adesao_pdf(resultados_por_escola, query_params)
    pdf_reader = PdfReader(io.BytesIO(pdf))
    assert len(pdf_reader.pages) == 2

    texto_por_pagina = [
        page.extract_text().replace("\n", " ") for page in pdf_reader.pages
    ]

    assert (
        "EMEF TESTE A | PERÍODO DE LANÇAMENTO: DE 05/03/2025 ATÉ 15/03/2025"
        in texto_por_pagina[0]
    )
    assert (
        "EMEF TESTE B | PERÍODO DE LANÇAMENTO: DE 05/03/2025 ATÉ 15/03/2025"
        in texto_por_pagina[1]
    )
    assert "MANHA" in texto_por_pagina[0]
    assert "LANCHE" in texto_por_pagina[0]
    assert "TARDE" in texto_por_pagina[1]
    assert "REFEIÇÃO" in texto_por_pagina[1]


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf_por_escola_uma_escola(
    mock_exportacao_relatorio_adesao,
):
    resultados_agregados, query_params = mock_exportacao_relatorio_adesao
    resultados_por_escola = [
        {
            "escola": {"nome": "EMEF TESTE A", "codigo_eol": "123456"},
            "resultados": resultados_agregados,
        }
    ]

    pdf = gera_relatorio_adesao_pdf(resultados_por_escola, query_params)
    pdf_reader = PdfReader(io.BytesIO(pdf))
    assert len(pdf_reader.pages) == 1

    texto = extrair_texto_de_pdf(pdf)
    assert "EMEF TESTE A" in texto


@freeze_time("2025-07-20")
def test_gera_relatorio_adesao_pdf_por_escola_sem_frequencia(
    mock_exportacao_relatorio_adesao,
):
    _, query_params = mock_exportacao_relatorio_adesao
    resultados_por_escola = [
        {
            "escola": {"nome": "EMEF TESTE A", "codigo_eol": "123456"},
            "resultados": {
                "MANHA": {
                    "LANCHE": {
                        "total_servido": 140,
                        "total_frequencia": 0,
                        "total_adesao": 0.0,
                    }
                }
            },
        }
    ]

    pdf = gera_relatorio_adesao_pdf(resultados_por_escola, query_params)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "EMEF TESTE A" in texto
    assert "TOTAL" in texto
