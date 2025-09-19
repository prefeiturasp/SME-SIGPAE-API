from sme_sigpae_api.produto.api.serializers.serializers import (
    ReclamacaoDeProdutoExcelSerializer,
)
from sme_sigpae_api.produto.utils.relatorio_reclamacao_produto import (
    _extrair_dados_reclamacao,
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
    assert "Nº da Reclamação" in dado
    assert "RF e Nome do Reclamante" in dado
    assert "Data da Reclamação" in dado
