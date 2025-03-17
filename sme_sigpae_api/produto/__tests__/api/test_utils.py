from unittest.mock import Mock

from sme_sigpae_api.produto.api.dashboard.utils import filtra_reclamacoes_por_usuario
from sme_sigpae_api.produto.models import HomologacaoProduto


def test_filtra_reclamacoes_por_usuario_tercerizadas(
    client_autenticado_vinculo_terceirizada, hom_produto_com_editais
):
    client, usuario = client_autenticado_vinculo_terceirizada
    mock_request = Mock()
    mock_request.user = usuario
    query_set = HomologacaoProduto.objects.all()

    assert query_set.count() == 1
    query_set = filtra_reclamacoes_por_usuario(mock_request, query_set)
    assert query_set.count() == 1


def test_filtra_reclamacoes_por_usuario_escola(
    client_autenticado_da_escola, hom_produto_com_editais
):
    client, usuario = client_autenticado_da_escola
    mock_request = Mock()
    mock_request.user = usuario
    query_set = HomologacaoProduto.objects.all()

    assert query_set.count() == 1
    query_set = filtra_reclamacoes_por_usuario(mock_request, query_set)
    assert query_set.count() == 1


def test_filtra_reclamacoes_por_usuario_dre(
    client_autenticado_da_dre, hom_produto_com_editais
):
    client, usuario = client_autenticado_da_dre
    mock_request = Mock()
    mock_request.user = usuario
    query_set = HomologacaoProduto.objects.all()

    assert query_set.count() == 1
    query_set = filtra_reclamacoes_por_usuario(mock_request, query_set)
    assert query_set.count() == 0
