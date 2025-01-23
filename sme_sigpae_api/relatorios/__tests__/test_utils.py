from datetime import date

from django.http import HttpResponse
from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML

from ..utils import (
    extrair_texto_de_pdf,
    get_config_cabecario_relatorio_analise,
    html_to_pdf_file,
    html_to_pdf_response,
)


def test_config_cabecario_obter_cabecario_reduzido():
    filtros = {}
    config = get_config_cabecario_relatorio_analise(filtros, None, None)
    assert config["cabecario_tipo"] == "CABECARIO_REDUZIDO"


def test_config_cabecario_obter_cabecario_por_data():
    filtros = {"data_analise_inicial": date.today().strftime("%d/%m/%Y")}
    config = get_config_cabecario_relatorio_analise(filtros, None, None)
    assert config["cabecario_tipo"] == "CABECARIO_POR_DATA"

    filtros = {
        "data_analise_inicial": date.today().strftime("%d/%m/%Y"),
        "data_analise_final": date.today().strftime("%d/%m/%Y"),
    }
    assert config["cabecario_tipo"] == "CABECARIO_POR_DATA"
    config = get_config_cabecario_relatorio_analise(filtros, None, None)


def test_config_cabecario_obter_cabecario_por_nome_produto():
    filtros = {"nome_produto": "Teste"}
    config = get_config_cabecario_relatorio_analise(filtros, None, None)
    assert config["cabecario_tipo"] == "CABECARIO_POR_NOME"


def test_config_cabecario_obter_cabecario_por_nome_marca():
    filtros = {"nome_marca": "Teste"}
    config = get_config_cabecario_relatorio_analise(filtros, None, None)
    assert config["cabecario_tipo"] == "CABECARIO_POR_NOME"


def test_config_cabecario_obter_cabecario_por_nome_fabricante():
    filtros = {"nome_fabricante": "Teste"}
    config = get_config_cabecario_relatorio_analise(filtros, None, None)
    assert config["cabecario_tipo"] == "CABECARIO_POR_NOME"


def test_config_cabecario_obter_cabecario_por_nome_terceirizada():
    filtros = {"nome_terceirizada": "Teste"}
    contatos_terceirizada = [{"email": "teste@teste.com", "telefone": "1199999999"}]
    config = get_config_cabecario_relatorio_analise(
        filtros, None, contatos_terceirizada
    )
    assert config["cabecario_tipo"] == "CABECARIO_POR_NOME_TERCEIRIZADA"


def test_html_to_pdf_response():
    html_string = "<h1>Teste de PDF</h1><p>Conteúdo do PDF gerado</p>"
    nome_pdf = "teste.pdf"
    pdf = html_to_pdf_response(html_string, nome_pdf)

    assert pdf.status_code == 200
    assert pdf.headers["Content-Type"] == "application/pdf"
    assert pdf.headers["Content-Disposition"] == f'filename="{nome_pdf}"'

    texto = extrair_texto_de_pdf(pdf.content)
    assert "Teste de PDF" in texto
    assert "Conteúdo do PDF gerado" in texto
    assert texto.count("PDF") == 2


def test_extrair_texto_de_pdf():
    html_string = "<h1>Teste de PDF</h1><p>Conteúdo do PDF gerado</p>"
    pdf_file = HTML(
        string=html_string, url_fetcher=django_url_fetcher, base_url="file://abobrinha"
    ).write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    texto = extrair_texto_de_pdf(response.content)
    assert "Teste de PDF" in texto
    assert "Conteúdo do PDF gerado" in texto
    assert texto.count("PDF") == 2


def test_html_to_pdf_file_async_true():
    html_string = "<h1>Teste de PDF</h1><p>Conteúdo do PDF gerado</p>"
    nome_pdf = "teste.pdf"
    pdf = html_to_pdf_file(html_string, nome_pdf, is_async=True)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "Teste de PDF" in texto
    assert "Conteúdo do PDF gerado" in texto
    assert texto.count("PDF") == 2


def test_html_to_pdf_file_async_false():
    html_string = "<h1>Teste de PDF</h1><p>Conteúdo do PDF gerado</p>"
    nome_pdf = "teste.pdf"
    pdf = html_to_pdf_file(html_string, nome_pdf, is_async=False)

    assert pdf.status_code == 200
    assert pdf.headers["Content-Type"] == "application/pdf"
    assert pdf.headers["Content-Disposition"] == f'filename="{nome_pdf}"'

    texto = extrair_texto_de_pdf(pdf.content)
    assert "Teste de PDF" in texto
    assert "Conteúdo do PDF gerado" in texto
    assert texto.count("PDF") == 2
