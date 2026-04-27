import pytest
from unittest.mock import Mock
from model_bakery import baker

from sme_sigpae_api.produto.api.dashboard.utils import filtra_reclamacoes_por_usuario, filtra_reclamacoes_questionamento_codae
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.dados_comuns import constants


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


@pytest.mark.parametrize(
    "status",
    [
        HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
        HomologacaoProduto.workflow_class.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
        HomologacaoProduto.workflow_class.UE_RESPONDEU_QUESTIONAMENTO,
        HomologacaoProduto.workflow_class.NUTRISUPERVISOR_RESPONDEU_QUESTIONAMENTO,
        HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO,
        HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_UE,
        HomologacaoProduto.workflow_class.CODAE_QUESTIONOU_NUTRISUPERVISOR,
    ],
)
def test_filtra_reclamacoes_questionamento_codae_gpcodae_status_novo(
    status, produto_com_editais
):
    request = Mock()
    request.user = Mock()
    request.user.tipo_usuario = constants.TIPO_USUARIO_GESTAO_PRODUTO

    homologacao = baker.make("HomologacaoProduto", produto=produto_com_editais)
    HomologacaoProduto.objects.filter(pk=homologacao.pk).update(status=status)
    homologacao.refresh_from_db()

    resultado = filtra_reclamacoes_questionamento_codae(
        request, HomologacaoProduto.objects.all()
    )

    assert resultado.count() == 1
    assert resultado.first().pk == homologacao.pk
