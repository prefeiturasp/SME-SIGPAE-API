import re
from unittest.mock import patch

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
    get_pdf_cronograma,
    get_pdf_ficha_recebimento,
    get_pdf_ficha_tecnica,
    get_total_por_periodo,
    obter_justificativa_dieta,
    obter_relatorio_da_unidade,
    relatorio_dieta_especial_protocolo,
    relatorio_reclamacao_produtos,
    relatorio_solicitacao_medicao_por_escola,
    relatorio_suspensao_de_alimentacao,
)
from sme_sigpae_api.pre_recebimento.tasks import gerar_relatorio_cronogramas_pdf_async
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

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


def test_obter_justificativa_dieta_cancelada(
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
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação:" in texto
    assert "produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE:" in texto
    assert "deu certooo" in texto


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
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação:" in texto
    assert "produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE:" in texto
    assert "deu certooo" in texto


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
    assert "Empresa: ALIMENTAR GESTÃO DE SERVIÇOS" in texto
    assert "RF e Nome do Reclamante: 8115257 - SUPER USUARIO ESCOLA EMEF" in texto
    assert (
        "Cód EOL e Nome da Escola: 017981 - EMEF PERICLES EUGENIO DA SILVA RAMOS"
        in texto
    )
    assert " Data da reclamação: 15/07/2022" in texto
    assert "Justificativa da reclamação:" in texto
    assert "produto vencido" in texto
    assert "Data avaliação CODAE: 05/08/2022" in texto
    assert "Justificativa avaliação CODAE:" in texto
    assert "deu certooo" in texto


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


def test_relatorio_ficha_recebimento(
    ficha_recebimento_com_ocorrencia,
    ficha_recebimento_reposicao,
    ficha_recebimento_carta_credito,
):
    pdf_response = get_pdf_ficha_recebimento(None, ficha_recebimento_com_ocorrencia)

    assert pdf_response.status_code == 200
    assert pdf_response.headers["Content-Type"] == "application/pdf"

    texto = extrair_texto_de_pdf(pdf_response.content)

    assert (
        ficha_recebimento_com_ocorrencia.etapa.cronograma.ficha_tecnica.produto.nome
        in texto
    )
    assert ficha_recebimento_com_ocorrencia.observacao in texto
    assert "HOUVE OCORRÊNCIA(S) NO RECEBIMENTO: SIM" in texto
    assert "Faltaram 5 unidades do produto" in texto

    # Teste para Ficha de Recebimento de Reposição
    pdf_response_reposicao = get_pdf_ficha_recebimento(
        None, ficha_recebimento_reposicao
    )

    assert pdf_response_reposicao.status_code == 200
    assert pdf_response_reposicao.headers["Content-Type"] == "application/pdf"

    texto_reposicao = extrair_texto_de_pdf(pdf_response_reposicao.content)

    assert "REPOSIÇÃO / PAGAMENTO DE NOTIFICAÇÃO" in texto_reposicao
    assert (
        "Referente a ocorrência registrada nesta etapa, o Fornecedor optou por: REPOR OS PRODUTOS"
        in texto_reposicao
    )

    # Teste para caso de Carta de Crédito
    pdf_response_carta_credito = get_pdf_ficha_recebimento(
        None, ficha_recebimento_carta_credito
    )

    assert pdf_response_carta_credito.status_code == 200
    assert pdf_response_carta_credito.headers["Content-Type"] == "application/pdf"

    texto_carta_credito = extrair_texto_de_pdf(pdf_response_carta_credito.content)

    assert "FAZER UMA CARTA DE CRÉDITO DO VALOR PAGO" in texto_carta_credito


def test_relatorio_cronograma_entrega(cronograma):
    pdf_response_cronograma = get_pdf_cronograma(None, cronograma)

    assert pdf_response_cronograma.status_code == 200
    assert pdf_response_cronograma.headers["Content-Type"] == "application/pdf"

    texto_pdf = extrair_texto_de_pdf(pdf_response_cronograma.content)

    assert cronograma.ficha_tecnica.produto.nome in texto_pdf
    assert cronograma.ficha_tecnica.marca.nome in texto_pdf
    assert cronograma.numero in texto_pdf
    assert cronograma.contrato.numero in texto_pdf

    assert cronograma.unidade_medida.abreviacao in texto_pdf

    assert "Produto:" in texto_pdf
    assert "LEVE LEITE - PLL" in texto_pdf
    assert "Marca:" in texto_pdf
    assert "Quantidade Total Programada:" in texto_pdf

    # CNPJ formatado
    cnpj_regex = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
    assert re.search(cnpj_regex, texto_pdf), "CNPJ deve estar formatado corretamente"

    etapas = cronograma.etapas.all()
    if etapas.exists():
        for etapa in etapas:
            if etapa.numero_empenho:
                assert etapa.numero_empenho in texto_pdf


def test_relatorio_cronograma_lista_com_leve_leite(cronograma, usuario):
    cronograma.ficha_tecnica.programa = FichaTecnicaDoProduto.LEVE_LEITE
    cronograma.ficha_tecnica.save()

    pdf_content = gerar_relatorio_cronogramas_pdf_async(usuario.username, [cronograma.id], {})
    texto_pdf = extrair_texto_de_pdf(pdf_content)

    assert "LEVE LEITE - PLL" in texto_pdf


def test_relatorio_cronograma_lista_sem_leve_leite(cronograma, usuario):
    cronograma.ficha_tecnica.programa = FichaTecnicaDoProduto.ALIMENTACAO_ESCOLAR
    cronograma.ficha_tecnica.save()

    pdf_content = gerar_relatorio_cronogramas_pdf_async(usuario.username, [cronograma.id], {})
    texto_pdf = extrair_texto_de_pdf(pdf_content)

    assert "LEVE LEITE - PLL" not in texto_pdf

    if cronograma.armazem and cronograma.armazem.nome_fantasia:
        nome_armazem = cronograma.armazem.nome_fantasia
        assert nome_armazem in texto_pdf or nome_armazem.upper() in texto_pdf


def test_obter_relatorio_da_unidade_emef():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ), patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola"
    ) as mock_modulo_emef:

        tipos_unidade = ["EMEF"]
        resultado = obter_relatorio_da_unidade(tipos_unidade)

        assert resultado == mock_modulo_emef


def test_obter_relatorio_da_unidade_emei():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ), patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola"
    ) as mock_modulo_emei:

        tipos_unidade = ["EMEI"]
        resultado = obter_relatorio_da_unidade(tipos_unidade)

        assert resultado == mock_modulo_emei


def test_obter_relatorio_da_unidade_cei():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ), patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola_cei"
    ) as mock_modulo_cei:

        tipos_unidade = ["CEI"]
        resultado = obter_relatorio_da_unidade(tipos_unidade)

        assert resultado == mock_modulo_cei


def test_obter_relatorio_da_unidade_pertencem_a_nenhum_grupo():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ):

        tipos_unidade = ["TIPO_INEXISTENTE", "OUTRO_TIPO"]

        with pytest.raises(ValueError) as exc_info:
            obter_relatorio_da_unidade(tipos_unidade)

        assert "Unidades inválidas:" in str(exc_info.value)
        assert "TIPO_INEXISTENTE" in str(exc_info.value)


def test_relatorio_solicitacao_medicao_rodape_aprovacao(
    solicitacao_medicao_inicial_aprovada_codae,
):
    relatorio = relatorio_solicitacao_medicao_por_escola(
        solicitacao_medicao_inicial_aprovada_codae
    )
    texto = extrair_texto_de_pdf(relatorio)

    assert "INFORMAÇÕES BÁSICAS DA MEDIÇÃO" in texto
    assert "EMEF JOAO MENDES" in texto

    assert "Aprovado por CODAE em" in texto
    assert "27/11/2025" in texto
    assert "Usuário TESTE" in texto


def test_obter_relatorio_da_unidade_cemei():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEMEI",
        {"CEMEI", "CEU CEMEI"},
    ), patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola_cemei"
    ) as mock_modulo_cemei:

        tipos_unidade = ["CEMEI"]
        resultado = obter_relatorio_da_unidade(tipos_unidade)

        assert resultado == mock_modulo_cemei


def test_obter_relatorio_da_unidade_emebs():
    with patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEF",
        {"EMEF", "EMEFM"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEI", {"EMEI"}
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEI",
        {"CEI", "CEI CEU"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_CEMEI",
        {"CEMEI", "CEU CEMEI"},
    ), patch(
        "sme_sigpae_api.dados_comuns.constants.ORDEM_UNIDADES_GRUPO_EMEBS",
        {"EMEBS"},
    ), patch(
        "sme_sigpae_api.relatorios.relatorios.relatorio_solicitacao_medicao_por_escola_emebs"
    ) as mock_modulo_emebs:

        tipos_unidade = ["EMEBS"]
        resultado = obter_relatorio_da_unidade(tipos_unidade)

        assert resultado == mock_modulo_emebs
