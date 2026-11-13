import io

import pytest
from pypdf import PdfReader
from rest_framework import status

from src.pos_recebimento.models import (
    AssinaturaTermoRecebimentoProvisorio,
    TermoRecebimentoProvisorio,
)
from src.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


def _url_pdf(termo):
    return f"/pos-recebimento/termos/{termo.uuid}/gerar-pdf-termo/"


def _assina_fiscais(termo):
    """Registra a assinatura de cada fiscal distinto e conclui a etapa."""
    for fiscal in dict.fromkeys((termo.fiscal_1, termo.fiscal_2, termo.fiscal_3)):
        AssinaturaTermoRecebimentoProvisorio.objects.get_or_create(
            termo=termo,
            usuario=fiscal,
        )
    TermoRecebimentoProvisorio.objects.filter(pk=termo.pk).update(
        status=TermoRecebimentoProvisorio.TERMO_ASSINADO
    )
    termo.refresh_from_db()
    return termo


def test_pdf_negado_para_empresa_fornecedora(
    client_autenticado_fornecedor, termo_para_assinatura
):
    termo = _assina_fiscais(termo_para_assinatura)

    response = client_autenticado_fornecedor.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_pdf_indisponivel_com_assinaturas_pendentes(
    client_fiscal, termo_para_assinatura
):
    client, _ = client_fiscal

    response = client.get(_url_pdf(termo_para_assinatura))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "três Fiscais do Contrato" in response.json()["detail"]


def test_pdf_disponivel_apos_assinaturas_dos_tres_fiscais(
    client_fiscal, termo_para_assinatura
):
    client, _ = client_fiscal
    termo = _assina_fiscais(termo_para_assinatura)

    response = client.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/pdf"
    texto = extrair_texto_de_pdf(response.content)
    assert "TERMO DE RECEBIMENTO" in texto
    assert "PROVISÓRIO" in texto
    assert "FISCAL DO CONTRATO" in texto
    assert "São Paulo," in texto
    for fiscal in (termo.fiscal_1, termo.fiscal_2, termo.fiscal_3):
        assert fiscal.nome in texto


def _fontes_do_pdf(conteudo):
    reader = PdfReader(io.BytesIO(conteudo))
    fontes = set()
    for pagina in reader.pages:
        recursos = pagina.get("/Resources") or {}
        for referencia in (recursos.get("/Font") or {}).values():
            fontes.add(str(referencia.get_object().get("/BaseFont", "")))
    return fontes


def test_pdf_embute_fonte_roboto_bold(client_fiscal, termo_para_assinatura):
    client, _ = client_fiscal
    termo = _assina_fiscais(termo_para_assinatura)

    response = client.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_200_OK
    assert any("Roboto-Bold" in fonte for fonte in _fontes_do_pdf(response.content))


def test_pdf_renderiza_tres_blocos_com_fiscal_repetido(
    client_fiscal, termo_fiscais_repetidos
):
    client, _ = client_fiscal
    termo = _assina_fiscais(termo_fiscais_repetidos)

    response = client.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_200_OK
    texto = extrair_texto_de_pdf(response.content)
    assert texto.count("FISCAL DO CONTRATO") == 3


def test_pdf_usa_a_data_de_cadastro_do_termo(client_fiscal, termo_listagem):
    client, _ = client_fiscal
    termo = _assina_fiscais(termo_listagem)

    response = client.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_200_OK
    texto = extrair_texto_de_pdf(response.content)
    assert "15 de março de 2026" in texto


def test_pdf_apresenta_quantidade_total_recebida(
    client_fiscal, termos_painel_assinatura
):
    client, _ = client_fiscal
    termo = _assina_fiscais(termos_painel_assinatura.assinado_do_fiscal)

    response = client.get(_url_pdf(termo))

    assert response.status_code == status.HTTP_200_OK
    texto = extrair_texto_de_pdf(response.content)
    assert "MAMAO PAPAYA" in texto
    assert "1.234,56" in texto
