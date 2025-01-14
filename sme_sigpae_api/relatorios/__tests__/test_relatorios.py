from io import BytesIO

import pytest
from PyPDF4 import PdfFileReader

from ..relatorios import (
    relatorio_dieta_especial_protocolo,
    relatorio_suspensao_de_alimentacao,
)


@pytest.mark.django_db
def test_relatorio_dieta_especial_protocolo(solicitacao_dieta_especial_autorizada):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_autorizada
    )

    assert ("Orientações Gerais" in html_string) is True
    assert (
        solicitacao_dieta_especial_autorizada.orientacoes_gerais in html_string
    ) is True


@pytest.mark.django_db
def test_relatorio_suspensao_de_alimentacao(grupo_suspensao_alimentacao):
    pdf_response = relatorio_suspensao_de_alimentacao(None, grupo_suspensao_alimentacao)

    assert pdf_response.status_code == 200
    assert pdf_response.headers["Content-Type"] == "application/pdf"
    assert (
        pdf_response.headers["Content-Disposition"]
        == f'filename="solicitacao_suspensao_{grupo_suspensao_alimentacao.id_externo}.pdf"'
    )

    pdf_reader = PdfFileReader(BytesIO(pdf_response.content))
    text = ""
    for page_num in range(pdf_reader.getNumPages()):
        text += pdf_reader.getPage(page_num).extractText()

    assert grupo_suspensao_alimentacao.escola.nome in text
    assert grupo_suspensao_alimentacao.observacao in text
    assert "Justificativa" not in text
    assert "Histórico de cancelamento" not in text

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in text
        assert sustentacao_alimentacao.motivo.nome in text


@pytest.mark.django_db
def test_relatorio_suspensao_de_alimentacao_parcialmente_cancelado(
    grupo_suspensao_alimentacao_cancelamento_parcial,
):
    pdf_response = relatorio_suspensao_de_alimentacao(
        None, grupo_suspensao_alimentacao_cancelamento_parcial
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["Content-Type"] == "application/pdf"
    assert (
        pdf_response.headers["Content-Disposition"]
        == f'filename="solicitacao_suspensao_{grupo_suspensao_alimentacao_cancelamento_parcial.id_externo}.pdf"'
    )

    pdf_reader = PdfFileReader(BytesIO(pdf_response.content))
    text = ""
    for page_num in range(pdf_reader.getNumPages()):
        text += pdf_reader.getPage(page_num).extractText()

    assert grupo_suspensao_alimentacao_cancelamento_parcial.escola.nome in text
    assert grupo_suspensao_alimentacao_cancelamento_parcial.observacao in text
    assert "Justificativa" in text
    assert "Histórico de cancelamento" in text

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao_cancelamento_parcial.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in text
        assert sustentacao_alimentacao.motivo.nome in text
        if sustentacao_alimentacao.cancelado:
            assert sustentacao_alimentacao.cancelado_justificativa in text


@pytest.mark.django_db
def test_relatorio_suspensao_de_alimentacao_totalmente_cancelado(
    grupo_suspensao_alimentacao_cancelamento_total,
):
    pdf_response = relatorio_suspensao_de_alimentacao(
        None, grupo_suspensao_alimentacao_cancelamento_total
    )

    assert pdf_response.status_code == 200
    assert pdf_response.headers["Content-Type"] == "application/pdf"
    assert (
        pdf_response.headers["Content-Disposition"]
        == f'filename="solicitacao_suspensao_{grupo_suspensao_alimentacao_cancelamento_total.id_externo}.pdf"'
    )

    pdf_reader = PdfFileReader(BytesIO(pdf_response.content))
    text = ""
    for page_num in range(pdf_reader.getNumPages()):
        text += pdf_reader.getPage(page_num).extractText()

    assert grupo_suspensao_alimentacao_cancelamento_total.escola.nome in text
    assert grupo_suspensao_alimentacao_cancelamento_total.observacao in text
    assert "Justificativa" in text
    assert "Histórico de cancelamento" in text

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao_cancelamento_total.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in text
        assert sustentacao_alimentacao.motivo.nome in text
        assert sustentacao_alimentacao.cancelado_justificativa in text
