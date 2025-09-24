import re

import pytest
from freezegun import freeze_time

from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.helpers import (
    formata_cnpj_ficha_tecnica,
    formata_telefone_ficha_tecnica,
)
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf

from ..relatorios import (
    cabecalho_reclamacao_produto,
    formata_informacoes_ficha_tecnica,
    get_pdf_ficha_tecnica,
    get_total_por_periodo,
    obter_justificativa_dieta,
    relatorio_dieta_especial_protocolo,
    relatorio_reclamacao_produtos,
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
    assert "1. Orientações Gerais" in html_string
    assert "2. Relação de Alimentos para Substituição" in html_string
    assert (
        "3. Termo de Ciência do Responsável e Autorização de Uso de Imagem"
        in html_string
    )
    assert "Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)" in html_string


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
    assert "1. Orientações Gerais" in html_string
    assert "2. Relação de Alimentos para Substituição" in html_string
    assert (
        "3. Termo de Ciência do Responsável e Autorização de Uso de Imagem"
        in html_string
    )
    assert "Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)" in html_string


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
    total_refeicao = get_total_por_periodo(tabelas, "total_refeicoes_pagamento", True)
    assert total_refeicao == {"Infantil INTEGRAL": 80}

    total_sobremesa = get_total_por_periodo(tabelas, "total_sobremesas_pagamento", True)
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
    assert "1. Orientações Gerais" in html_string
    assert "2. Relação de Alimentos para Substituição" in html_string
    assert "3. Termo de Ciência do Responsável" in html_string
    assert "e Autorização de Uso de Imagem" not in html_string
    assert (
        "Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)"
        not in html_string
    )


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
    assert "1. Orientações Gerais" in html_string
    assert "2. Relação de Alimentos para Substituição" in html_string
    assert (
        "3. Termo de Ciência do Responsável e Autorização de Uso de Imagem"
        in html_string
    )
    assert "Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)" in html_string


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

    assert ficha_tecnica.empresa.nome_fantasia in texto
    assert ficha_tecnica.empresa.razao_social in texto

    assert formata_cnpj_ficha_tecnica(ficha_tecnica.empresa.cnpj) in texto
    assert ficha_tecnica.empresa.endereco in texto

    assert "FABRICANTE E/OU ENVASADOR/DISTRIBUIDOR" in texto
    assert ficha_tecnica.fabricante.fabricante.nome in texto
    assert ficha_tecnica.fabricante.endereco in texto
    assert formata_cnpj_ficha_tecnica(ficha_tecnica.fabricante.cnpj) in texto

    assert formata_telefone_ficha_tecnica(ficha_tecnica.fabricante.telefone) in texto
    assert ficha_tecnica.fabricante.email in texto

    assert ficha_tecnica.envasador_distribuidor.fabricante.nome in texto
    assert ficha_tecnica.envasador_distribuidor.endereco in texto
    assert (
        formata_cnpj_ficha_tecnica(ficha_tecnica.envasador_distribuidor.cnpj) in texto
    )
    assert (
        formata_telefone_ficha_tecnica(ficha_tecnica.envasador_distribuidor.telefone)
        in texto
    )
    assert ficha_tecnica.envasador_distribuidor.email in texto


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


@freeze_time("2024-12-27")
def test_relatorio_reclamacao_produtos(
    mock_produtos_relatorio_reclamacao, mock_filtros_relatorio_reclamacao
):
    relatorio = relatorio_reclamacao_produtos(
        produtos=mock_produtos_relatorio_reclamacao,
        quantidade_reclamacoes=1,
        filtros=mock_filtros_relatorio_reclamacao,
    )
    texto = extrair_texto_de_pdf(relatorio)
    assert "RELATÓRIO DE ACOMPANHAMENTO DE RECLAMAÇÕES DE PRODUTOS" in texto
    assert "Total de Reclamações de Produtos: 1" in texto
    assert "Período: 01/01/2022 até 19/08/2025" in texto
    assert "Data de extração do relatório: 27/12/2024" in texto
    assert "Para os editais:" in texto
    assert texto.count("Edital de Pregão 001") == 2
    assert texto.count("Edital de Pregão 002") == 1
    assert texto.count("Edital de Pregão 003") == 1
    assert texto.count("Edital de Pregão 004") == 2
    assert "IP - 3567-3, LPSD - 1235-8" in texto
    assert "Reclamação #93C77" in texto
    assert "Status Reclamação: CODAE recusou" in texto
    assert "DRE/LOTE: IP - 3567-3" in texto
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS LTDA" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação: produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE: deu certooo" in texto


@freeze_time("2024-12-27")
def test_relatorio_reclamacao_produtos_sem_dre_lote_selecionadas(
    mock_produtos_relatorio_reclamacao, mock_filtros_relatorio_reclamacao
):
    mock_filtros_relatorio_reclamacao.pop("lotes")
    relatorio = relatorio_reclamacao_produtos(
        produtos=mock_produtos_relatorio_reclamacao,
        quantidade_reclamacoes=1,
        filtros=mock_filtros_relatorio_reclamacao,
    )
    texto = extrair_texto_de_pdf(relatorio)
    assert "RELATÓRIO DE ACOMPANHAMENTO DE RECLAMAÇÕES DE PRODUTOS" in texto
    assert "Total de Reclamações de Produtos: 1" in texto
    assert "Período: 01/01/2022 até 19/08/2025" in texto
    assert "Data de extração do relatório: 27/12/2024" in texto
    assert "Para os editais:" in texto
    assert texto.count("Edital de Pregão 001") == 2
    assert texto.count("Edital de Pregão 002") == 1
    assert texto.count("Edital de Pregão 003") == 1
    assert texto.count("Edital de Pregão 004") == 2
    assert "IP - 3567-3, LPSD - 1235-8" not in texto
    assert "Reclamação #93C77" in texto
    assert "Status Reclamação: CODAE recusou" in texto
    assert "DRE/LOTE: IP - 3567-3" in texto
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS LTDA" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação: produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE: deu certooo" in texto


@freeze_time("2024-12-27")
def test_relatorio_reclamacao_produtos_sem_data_selecionadas(
    mock_produtos_relatorio_reclamacao, mock_filtros_relatorio_reclamacao
):
    mock_filtros_relatorio_reclamacao.pop("data_inicial_reclamacao")
    mock_filtros_relatorio_reclamacao.pop("data_final_reclamacao")
    relatorio = relatorio_reclamacao_produtos(
        produtos=mock_produtos_relatorio_reclamacao,
        quantidade_reclamacoes=1,
        filtros=mock_filtros_relatorio_reclamacao,
    )
    texto = extrair_texto_de_pdf(relatorio)
    assert "RELATÓRIO DE ACOMPANHAMENTO DE RECLAMAÇÕES DE PRODUTOS" in texto
    assert "Total de Reclamações de Produtos: 1" in texto
    assert "Período: 01/01/2022 até 19/08/2025" not in texto
    assert "Data de extração do relatório: 27/12/2024" in texto
    assert "Para os editais:" in texto
    assert texto.count("Edital de Pregão 001") == 2
    assert texto.count("Edital de Pregão 002") == 1
    assert texto.count("Edital de Pregão 003") == 1
    assert texto.count("Edital de Pregão 004") == 2
    assert "IP - 3567-3, LPSD - 1235-8" in texto
    assert "Reclamação #93C77" in texto
    assert "Status Reclamação: CODAE recusou" in texto
    assert "DRE/LOTE: IP - 3567-3" in texto
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS LTDA" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação: produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE: deu certooo" in texto


@freeze_time("2024-12-27")
def test_cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao):
    cabecalho = cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao)
    assert isinstance(cabecalho, dict)
    assert cabecalho == {
        "data_extracao": "27/12/2024",
        "editais": "Edital de Pregão 001, Edital de Pregão 002, Edital de Pregão 003, Edital de Pregão 004",
        "lotes": "IP - 3567-3, LPSD - 1235-8",
        "periodo": "01/01/2022 até 19/08/2025",
    }


@freeze_time("2024-12-27")
def test_cabecalho_reclamacao_produto_sem_dre_lote(mock_filtros_relatorio_reclamacao):
    mock_filtros_relatorio_reclamacao.pop("lotes")
    cabecalho = cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao)
    assert isinstance(cabecalho, dict)
    assert cabecalho == {
        "data_extracao": "27/12/2024",
        "editais": "Edital de Pregão 001, Edital de Pregão 002, Edital de Pregão 003, Edital de Pregão 004",
        "periodo": "01/01/2022 até 19/08/2025",
    }


@freeze_time("2024-12-27")
def test_cabecalho_reclamacao_produto_sem_data(mock_filtros_relatorio_reclamacao):
    mock_filtros_relatorio_reclamacao.pop("data_inicial_reclamacao")
    mock_filtros_relatorio_reclamacao.pop("data_final_reclamacao")
    cabecalho = cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao)
    assert isinstance(cabecalho, dict)
    assert cabecalho == {
        "data_extracao": "27/12/2024",
        "editais": "Edital de Pregão 001, Edital de Pregão 002, Edital de Pregão 003, Edital de Pregão 004",
        "lotes": "IP - 3567-3, LPSD - 1235-8",
    }


@freeze_time("2024-12-27")
def test_cabecalho_reclamacao_produto_sem_data_final(mock_filtros_relatorio_reclamacao):
    mock_filtros_relatorio_reclamacao.pop("data_final_reclamacao")
    cabecalho = cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao)
    assert isinstance(cabecalho, dict)
    assert cabecalho == {
        "data_extracao": "27/12/2024",
        "editais": "Edital de Pregão 001, Edital de Pregão 002, Edital de Pregão 003, Edital de Pregão 004",
        "lotes": "IP - 3567-3, LPSD - 1235-8",
        "periodo": "A partir de 01/01/2022",
    }


@freeze_time("2024-12-27")
def test_cabecalho_reclamacao_produto_sem_data_inicial(
    mock_filtros_relatorio_reclamacao,
):
    mock_filtros_relatorio_reclamacao.pop("data_inicial_reclamacao")
    cabecalho = cabecalho_reclamacao_produto(mock_filtros_relatorio_reclamacao)
    assert isinstance(cabecalho, dict)
    assert cabecalho == {
        "data_extracao": "27/12/2024",
        "editais": "Edital de Pregão 001, Edital de Pregão 002, Edital de Pregão 003, Edital de Pregão 004",
        "lotes": "IP - 3567-3, LPSD - 1235-8",
        "periodo": "Até 19/08/2025",
    }
