from datetime import date

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML

from ..utils import (
    PDFMergeService,
    extrair_texto_de_pdf,
    get_config_cabecario_relatorio_analise,
    html_to_pdf_watermark,
    html_to_pdf_email_anexo,
    html_to_pdf_file,
    html_to_pdf_multiple,
    html_to_pdf_response,
    merge_pdf_com_string_template,
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


def test_html_to_pdf_watermark():
    html_string = "<h1>PDF Cancelado</h1><p>Conteúdo para testar marca d'água</p>"
    nome_pdf = "cancelado.pdf"

    pdf = html_to_pdf_watermark(html_string, nome_pdf, is_async=True)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "PDF Cancelado" in texto
    assert "Conteúdo para testar marca d'água" in texto


def test_html_to_pdf_watermark_async_false():
    html_string = "<h1>PDF Cancelado</h1><p>Conteúdo para testar marca d'água</p>"
    nome_pdf = "cancelado.pdf"

    response = html_to_pdf_watermark(html_string, nome_pdf, is_async=False)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == f'filename="{nome_pdf}"'

    texto = extrair_texto_de_pdf(response.content)
    assert "PDF Cancelado" in texto
    assert "Conteúdo para testar marca d'água" in texto


def test_html_to_pdf_multiple_async_true():
    lista_strings = [
        "<h1>Página 1</h1><p>Conteúdo da primeira página</p>",
        "<h1>Página 2</h1><p>Conteúdo da segunda página</p>",
    ]
    nome_pdf = "multiplo.pdf"

    pdf_bytes = html_to_pdf_multiple(lista_strings, nome_pdf, is_async=True)
    assert isinstance(pdf_bytes, bytes)

    texto = extrair_texto_de_pdf(pdf_bytes)
    assert "Página 1" in texto
    assert "Conteúdo da primeira página" in texto
    assert "Página 2" in texto
    assert "Conteúdo da segunda página" in texto


def test_html_to_pdf_multiple_async_false():
    lista_strings = [
        "<h1>Página 1</h1><p>Conteúdo da primeira página</p>",
        "<h1>Página 2</h1><p>Conteúdo da segunda página</p>",
    ]
    nome_pdf = "multiplo.pdf"

    response = html_to_pdf_multiple(lista_strings, nome_pdf, is_async=False)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == f'filename="{nome_pdf}"'

    texto = extrair_texto_de_pdf(response.content)
    assert "Página 1" in texto
    assert "Conteúdo da primeira página" in texto
    assert "Página 2" in texto
    assert "Conteúdo da segunda página" in texto


def test_html_to_pdf_email_anexo():
    html_string = (
        "<h1>Dieta Cancelada</h1><p>A dieta foi cancelada automaticamente.</p>"
    )
    nome_pdf = "cancelamento.pdf"

    pdf_bytes = html_to_pdf_email_anexo(html_string, pdf_filename=nome_pdf)
    assert isinstance(pdf_bytes, bytes)

    texto = extrair_texto_de_pdf(pdf_bytes)
    assert "Dieta Cancelada" in texto
    assert "A dieta foi cancelada automaticamente." in texto


def test_merge_pdf_com_string_template_todas_paginas(gerar_pdf_simples):
    html_template = "<div><p>Assinatura: NUTRICIONISTA</p></div>"
    resultado = merge_pdf_com_string_template(
        gerar_pdf_simples, html_template, somente_ultima_pagina=False
    )
    assert isinstance(resultado, ContentFile)

    texto = extrair_texto_de_pdf(resultado.read())
    assert "Dieta especial autorizada para o aluno Fulano1 - Página 1" in texto
    assert "Dieta especial autorizada para o aluno Fulano2 - Página 2" in texto
    assert texto.count("Assinatura: NUTRICIONISTA") == 2


def test_merge_pdf_com_string_template_todas_paginas(gerar_pdf_simples):
    html_template = "<div><p>Assinatura: NUTRICIONISTA</p></div>"
    resultado = merge_pdf_com_string_template(
        gerar_pdf_simples, html_template, somente_ultima_pagina=True
    )
    assert isinstance(resultado, ContentFile)

    texto = extrair_texto_de_pdf(resultado.read())
    assert "Dieta especial autorizada para o aluno Fulano1 - Página 1" in texto
    assert "Dieta especial autorizada para o aluno Fulano2 - Página 2" in texto
    assert texto.count("Assinatura: NUTRICIONISTA") == 1


def test_pdf_merge_service_mescla_dois_pdfs():
    service = PDFMergeService()
    pdf_1 = HTML(string=f"<h1>Primeiro PDF</h1>").write_pdf()
    service.append_pdf(pdf_1)
    pdf_2 = HTML(string=f"<h1>Segundo PDF</h1>").write_pdf()
    service.append_pdf(pdf_2)

    pdf_final = service.merge_pdfs()
    assert isinstance(pdf_final, bytes)
    texto = extrair_texto_de_pdf(pdf_final)
    assert "Primeiro PDF" in texto
    assert "Segundo PDF" in texto
