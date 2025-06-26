import re

import pytest

from sme_sigpae_api.pre_recebimento.api.helpers import (
    formata_cnpj_ficha_tecnica,
    formata_telefone_ficha_tecnica,
)
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf

from ..relatorios import (
    formata_informacoes_ficha_tecnica,
    get_pdf_ficha_tecnica,
    get_total_por_periodo,
    obter_justificativa_dieta,
    relatorio_dieta_especial_protocolo,
    relatorio_suspensao_de_alimentacao,
)

pytestmark = pytest.mark.django_db


def test_relatorio_dieta_especial_protocolo(solicitacao_dieta_especial_autorizada):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_autorizada
    )

    assert ("Orientações Gerais" in html_string) is True
    assert (
        solicitacao_dieta_especial_autorizada.orientacoes_gerais in html_string
    ) is True
    assert "PROTOCOLO PADRÃO DE DIETA ESPECIAL" in html_string
    assert "Dieta cancelada em" not in html_string
    assert "Justificativa" not in html_string


def test_relatorio_suspensao_de_alimentacao(grupo_suspensao_alimentacao):
    pdf_response = relatorio_suspensao_de_alimentacao(None, grupo_suspensao_alimentacao)

    assert pdf_response.status_code == 200
    assert pdf_response.headers["Content-Type"] == "application/pdf"
    assert (
        pdf_response.headers["Content-Disposition"]
        == f'filename="solicitacao_suspensao_{grupo_suspensao_alimentacao.id_externo}.pdf"'
    )

    texto = extrair_texto_de_pdf(pdf_response.content)

    assert grupo_suspensao_alimentacao.escola.nome in texto
    assert f"Observações: {grupo_suspensao_alimentacao.observacao}" in texto
    # r"Justi.*cativa": '.*' significa qualquer sequência de caracteres, incluindo quebras de linha
    assert not re.search(r"Justi.*cativa", texto)
    assert "Histórico de cancelamento" not in texto

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in texto
        assert sustentacao_alimentacao.motivo.nome in texto
        assert sustentacao_alimentacao.cancelado_justificativa == ""


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
    texto = extrair_texto_de_pdf(pdf_response.content)

    assert grupo_suspensao_alimentacao_cancelamento_parcial.escola.nome in texto
    assert (
        f"Observações: {grupo_suspensao_alimentacao_cancelamento_parcial.observacao}"
        in texto
    )
    # r"Justi.*cativa": '.*' significa qualquer sequência de caracteres, incluindo quebras de linha
    assert re.search(r"Justi.*cativa", texto)
    assert "Histórico de cancelamento" in texto

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao_cancelamento_parcial.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in texto
        assert sustentacao_alimentacao.motivo.nome in texto
        if sustentacao_alimentacao.cancelado:
            assert sustentacao_alimentacao.cancelado_justificativa in texto
            assert texto.count(sustentacao_alimentacao.cancelado_justificativa) == 2


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

    texto = extrair_texto_de_pdf(pdf_response.content)

    assert grupo_suspensao_alimentacao_cancelamento_total.escola.nome in texto
    assert (
        f"Observações: {grupo_suspensao_alimentacao_cancelamento_total.observacao}"
        in texto
    )
    # r"Justi.*cativa": '.*' significa qualquer sequência de caracteres, incluindo quebras de linha
    assert re.search(r"Justi.*cativa", texto)
    assert "Histórico de cancelamento" in texto

    for (
        sustentacao_alimentacao
    ) in grupo_suspensao_alimentacao_cancelamento_total.suspensoes_alimentacao.all():
        assert sustentacao_alimentacao.data.strftime("%d/%m/%Y") in texto
        assert sustentacao_alimentacao.motivo.nome in texto
        assert sustentacao_alimentacao.cancelado_justificativa in texto
        assert texto.count(sustentacao_alimentacao.cancelado_justificativa) == 2


def test_relatorio_dieta_especial_protocolo_cancelada(
    solicitacao_dieta_especial_cancelada,
):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_cancelada
    )
    assert ("Orientações Gerais" in html_string) is True
    assert (
        solicitacao_dieta_especial_cancelada.orientacoes_gerais in html_string
    ) is True

    assert "PROTOCOLO PADRÃO DE DIETA ESPECIAL" in html_string
    assert "Dieta cancelada em" in html_string
    assert "Justificativa" in html_string


def test_get_total_por_periodo_unico_periodo():
    tabelas = [
        {
            "periodos": ["Infantil INTEGRAL"],
            "nomes_campos": [
                "matriculados",
                "frequencia",
                "lanche",
                "lanche_4h",
                "refeicao",
                "repeticao_refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "repeticao_sobremesa",
                "total_sobremesas_pagamento",
            ],
            "len_periodos": [10],
            "valores_campos": [
                [
                    "Total",
                    "-",
                    "-",
                    40,
                    50,
                    60,
                    70,
                    80,
                    90,
                    100,
                    110,
                ]
            ],
        }
    ]
    total_refeicao = get_total_por_periodo(tabelas, "total_refeicoes_pagamento")
    assert total_refeicao == {"Infantil INTEGRAL": 80}

    total_sobremesa = get_total_por_periodo(tabelas, "total_sobremesas_pagamento")
    assert total_sobremesa == {"Infantil INTEGRAL": 110}


def test_get_total_por_periodo_multiplos_periodos():
    tabelas = [
        {
            "periodos": ["PARCIAL", "Infantil INTEGRAL"],
            "nomes_campos": [
                "matriculados",
                "frequencia",
                "lanche",
                "lanche_4h",
                "refeicao",
                "repeticao_refeicao",
                "total_refeicoes_pagamento",
                "sobremesa",
                "repeticao_sobremesa",
                "total_sobremesas_pagamento",
            ],
            "len_periodos": [5, 10],
            "valores_campos": [
                [
                    "Total",
                    "-",
                    "10",
                    "-",
                    "20",
                    30,
                    "-",
                    "-",
                    40,
                    50,
                    60,
                    70,
                    80,
                    90,
                    100,
                    110,
                ]
            ],
        }
    ]
    total_refeicao = get_total_por_periodo(tabelas, "total_refeicoes_pagamento")
    assert total_refeicao == {"Infantil INTEGRAL": 80}

    total_sobremesa = get_total_por_periodo(tabelas, "total_sobremesas_pagamento")
    assert total_sobremesa == {"Infantil INTEGRAL": 110}


def test_relatorio_dieta_especial_protocolo_alteracao_ue(
    solicitacao_dieta_especial_autorizada_alteracao_ue,
):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_autorizada_alteracao_ue
    )
    assert "PROTOCOLO PADRÃO DE DIETA ESPECIAL" in html_string
    assert (
        solicitacao_dieta_especial_autorizada_alteracao_ue.escola_destino.nome
        in html_string
    )
    assert (
        solicitacao_dieta_especial_autorizada_alteracao_ue.rastro_escola.nome
        not in html_string
    )
    assert "Alteração de UE - <b>Recreio nas Férias</b>" in html_string
    assert solicitacao_dieta_especial_autorizada_alteracao_ue.aluno.nome in html_string
    assert "Orientações Gerais" in html_string
    assert "Relação de Alimentos para Substituição" in html_string
    assert "Dieta cancelada em" not in html_string
    assert "Justificativa" not in html_string


def test_relatorio_dieta_especial_protocolo_inativa(
    solicitacao_dieta_especial_inativa,
):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_inativa
    )
    assert ("Orientações Gerais" in html_string) is True
    assert (
        solicitacao_dieta_especial_inativa.orientacoes_gerais in html_string
    ) is True

    assert "PROTOCOLO PADRÃO DE DIETA ESPECIAL" in html_string
    assert "Dieta Inativada em" in html_string
    assert (
        "Justificativa: Autorização de novo protocolo de dieta especial" in html_string
    )
    assert "Dieta cancelada em" not in html_string


def test_obter_justificativa_dieta_dieta_autorizada(
    solicitacao_dieta_especial_autorizada,
):
    justificativa = obter_justificativa_dieta(solicitacao_dieta_especial_autorizada)
    assert justificativa is None


def test_obter_justificativa_dieta_dieta_cancelada(
    solicitacao_dieta_especial_cancelada,
):
    log_recente = solicitacao_dieta_especial_cancelada.logs.last()
    justificativa = obter_justificativa_dieta(solicitacao_dieta_especial_cancelada)
    assert (
        justificativa
        == f'Dieta cancelada em: {log_recente.criado_em.strftime("%d/%m/%Y")} | Justificativa: Escola cancelou'
    )


def test_obter_justificativa_dieta_dieta_inativa(solicitacao_dieta_especial_inativa):
    log_recente = solicitacao_dieta_especial_inativa.logs.last()
    justificativa = obter_justificativa_dieta(solicitacao_dieta_especial_inativa)
    assert (
        justificativa
        == f'Dieta Inativada em: {log_recente.criado_em.strftime("%d/%m/%Y")} | Justificativa: Autorização de novo protocolo de dieta especial'
    )


def test_get_pdf_ficha_tecnica(ficha_tecnica):

    response = get_pdf_ficha_tecnica(None, ficha_tecnica)
    nome_pdf = f"ficha_tecnica_{ficha_tecnica.numero}.pdf"
    texto = extrair_texto_de_pdf(response.content)

    assert response["Content-Type"] == "application/pdf"
    assert f'filename="{nome_pdf}"' in response["Content-Disposition"]

    assert ficha_tecnica.numero in texto
    assert ficha_tecnica.produto.nome in texto
    assert ficha_tecnica.marca.nome in texto

    assert (
        f"Proponente:  {ficha_tecnica.empresa.nome_fantasia} / {ficha_tecnica.empresa.razao_social}"
        in texto
    )
    assert f"CNPJ:  {formata_cnpj_ficha_tecnica(ficha_tecnica.empresa.cnpj)}" in texto
    assert f"Endereço:  {ficha_tecnica.empresa.endereco}" in texto

    assert f"Status da Ficha Técnica Aprovada" in texto

    assert "FABRICANTE E/OU ENVASADOR/DISTRIBUIDOR" in texto
    assert f"Fabricante:  {ficha_tecnica.fabricante.fabricante.nome}" in texto
    assert f"Endereço:  {ficha_tecnica.fabricante.endereco}" in texto
    assert (
        f"CNPJ:  {formata_cnpj_ficha_tecnica(ficha_tecnica.fabricante.cnpj)}" in texto
    )
    assert (
        f"Telefone:  {formata_telefone_ficha_tecnica(ficha_tecnica.fabricante.telefone)}"
        in texto
    )
    assert f"E-mail:  {ficha_tecnica.fabricante.email}" in texto

    assert (
        f"Envasador/Distribuidor:  {ficha_tecnica.envasador_distribuidor.fabricante.nome}"
        in texto
    )
    assert f"Endereço:  {ficha_tecnica.envasador_distribuidor.endereco}" in texto
    assert (
        f"CNPJ:  {formata_cnpj_ficha_tecnica(ficha_tecnica.envasador_distribuidor.cnpj)}"
        in texto
    )
    assert (
        f"Telefone:  {formata_telefone_ficha_tecnica(ficha_tecnica.envasador_distribuidor.telefone)}"
        in texto
    )
    assert f"E-mail:  {ficha_tecnica.envasador_distribuidor.email}" in texto


def test_formata_informacoes_ficha_tecnica(ficha_tecnica):
    cnpj, telefone = formata_informacoes_ficha_tecnica(ficha_tecnica.empresa)
    assert cnpj == formata_cnpj_ficha_tecnica(ficha_tecnica.empresa.cnpj)
    assert telefone == formata_telefone_ficha_tecnica(
        ficha_tecnica.empresa.responsavel_telefone
    )


def test_formata_informacoes_ficha_tecnica_retorna_none():
    cnpj, telefone = formata_informacoes_ficha_tecnica(None)
    assert cnpj is None
    assert telefone is None


def test_get_pdf_ficha_tecnica_sem_envasador(ficha_tecnica_sem_envasador):

    response = get_pdf_ficha_tecnica(None, ficha_tecnica_sem_envasador)
    nome_pdf = f"ficha_tecnica_{ficha_tecnica_sem_envasador.numero}.pdf"
    texto = extrair_texto_de_pdf(response.content)

    assert response["Content-Type"] == "application/pdf"
    assert f'filename="{nome_pdf}"' in response["Content-Disposition"]

    assert "Envasador/Distribuidor" not in texto
