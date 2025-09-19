from datetime import datetime

from sme_sigpae_api.produto.api.serializers.serializers import (
    ReclamacaoDeProdutoExcelSerializer,
)
from sme_sigpae_api.produto.utils.relatorio_reclamacao_produto import (
    _extrair_dados_reclamacao,
    _gerar_subtitulo,
)


def test_extrair_dados_reclamacao(reclamacao_produto_query_excel):
    reclamacoes = ReclamacaoDeProdutoExcelSerializer(
        reclamacao_produto_query_excel, many=True
    ).data
    dado = _extrair_dados_reclamacao(reclamacoes[0], index=1)
    assert dado["Nº"] == 1
    assert dado["Edital"] == "Edital de Pregão nº 41/sme/2017"
    assert dado["Nome do Produto"] == "Produto1"
    assert dado["Marca"] == "Marca1"
    assert dado["Fabricante"] == "Fabricante1"
    assert dado["Status do Produto"] == "RASCUNHO"
    assert dado["Status da Reclamação"] == "Aguardando resposta da terceirizada"
    assert "Nº da Reclamação" in dado
    assert "RF e Nome do Reclamante" in dado
    assert "Data da Reclamação" in dado
    assert "DRE/LOTE" in dado
    assert "Empresa" in dado
    assert "Cód EOL e Nome da Escola" in dado


def test_gerar_subtitulo_com_datas():
    filtros = {
        "data_inicial_reclamacao": "01/01/2022",
        "data_final_reclamacao": "01/09/2025",
    }
    resultado = _gerar_subtitulo(filtros, 3)
    assert (
        "Total de Reclamações de produtos para os editais selecionados: 3" in resultado
    )
    assert "Período das Reclamações: De 01/01/2022 a 01/09/2025" in resultado
    assert (
        f"Data de Extração do Relatório: {datetime.now().date().strftime('%d/%m/%Y')}"
        in resultado
    )


def test_gerar_subtitulo_somente_data_inicial():
    filtros = {
        "data_inicial_reclamacao": "01/01/2022",
    }
    resultado = _gerar_subtitulo(filtros, 3)
    assert (
        "Total de Reclamações de produtos para os editais selecionados: 3" in resultado
    )
    assert "Período das Reclamações: A partir de 01/01/2022" in resultado
    assert (
        f"Data de Extração do Relatório: {datetime.now().date().strftime('%d/%m/%Y')}"
        in resultado
    )


def test_gerar_subtitulo_somente_data_final():
    filtros = {"data_final_reclamacao": "01/09/2025"}
    resultado = _gerar_subtitulo(filtros, 3)
    assert (
        "Total de Reclamações de produtos para os editais selecionados: 3" in resultado
    )
    assert "Período das Reclamações: Até 01/09/2025" in resultado
    assert (
        f"Data de Extração do Relatório: {datetime.now().date().strftime('%d/%m/%Y')}"
        in resultado
    )


def test_gerar_subtitulo_sem_datas():
    resultado = _gerar_subtitulo({}, 3)
    assert (
        "Total de Reclamações de produtos para os editais selecionados: 3" in resultado
    )
    assert (
        f"Data de Extração do Relatório: {datetime.now().date().strftime('%d/%m/%Y')}"
        in resultado
    )
    assert "Período das Reclamações" not in resultado
