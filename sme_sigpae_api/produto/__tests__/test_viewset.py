import pytest
from django.db.models.query import RawQuerySet
from rest_framework import status

from sme_sigpae_api.dados_comuns.fluxo_status import (
    HomologacaoProdutoWorkflow,
    ReclamacaoProdutoWorkflow,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    ReclamacaoDeProdutoSerializer,
)
from sme_sigpae_api.produto.api.viewsets import ReclamacaoProdutoViewSet
from sme_sigpae_api.produto.models import AnaliseSensorial

pytestmark = pytest.mark.django_db


def test_view_muda_status_com_justificativa_e_anexo_retorna_200(
    reclamacao_respondido_terceirizada, mock_view_de_reclamacao_produto
):
    mock_request, viewset = mock_view_de_reclamacao_produto
    assert (
        reclamacao_respondido_terceirizada.status
        == ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA
    )
    resposta = viewset.muda_status_com_justificativa_e_anexo(
        mock_request, reclamacao_respondido_terceirizada.codae_recusa
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert (
        resposta.data
        == ReclamacaoDeProdutoSerializer(reclamacao_respondido_terceirizada).data
    )
    assert resposta.data["status"] == ReclamacaoProdutoWorkflow.CODAE_RECUSOU
    assert resposta.data["status_titulo"] == "CODAE recusou"
    assert len(resposta.data["anexos"]) == 0


def test_view_muda_status_com_justificativa_e_anex_retorna_exception(
    reclamacao_respondido_terceirizada, mock_view_de_reclamacao_produto
):
    mock_request, viewset = mock_view_de_reclamacao_produto
    reclamacao_respondido_terceirizada.status = ReclamacaoProdutoWorkflow.CODAE_ACEITOU
    resposta = viewset.muda_status_com_justificativa_e_anexo(
        mock_request, reclamacao_respondido_terceirizada.codae_recusa
    )
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        resposta.data["detail"]
        == "Erro de transição de estado: Transition 'codae_recusa' isn't available from state 'CODAE_ACEITOU'."
    )


def test_view_quantidade_reclamacoes_ativas_retorna_uma(
    reclamacao_respondido_terceirizada,
):
    viewset = ReclamacaoProdutoViewSet()
    reclamacoes_ativas = viewset.quantidade_reclamacoes_ativas(
        reclamacao_respondido_terceirizada
    )
    assert reclamacoes_ativas == 1


def test_view_quantidade_reclamacoes_ativas_retorna_nenhuma(
    reclamacao_respondido_terceirizada,
):
    reclamacao = (
        reclamacao_respondido_terceirizada.homologacao_produto.reclamacoes.first()
    )
    reclamacao.status = ReclamacaoProdutoWorkflow.CODAE_ACEITOU
    reclamacao.save()

    viewset = ReclamacaoProdutoViewSet()
    reclamacoes_ativas = viewset.quantidade_reclamacoes_ativas(
        reclamacao_respondido_terceirizada
    )
    assert reclamacoes_ativas == 0


def test_view_update_analise_sensorial_status(reclamacao_respondido_terceirizada):
    analises_sensoriais = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
    ).all()
    assert analises_sensoriais.count() == 1

    viewset = ReclamacaoProdutoViewSet()
    viewset.update_analise_sensorial_status(
        analises_sensoriais, AnaliseSensorial.STATUS_RESPONDIDA
    )
    analises_aguardando_resposta = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
    ).count()
    assert analises_aguardando_resposta == 0

    analises_respondidas = reclamacao_respondido_terceirizada.homologacao_produto.analises_sensoriais.filter(
        status=AnaliseSensorial.STATUS_RESPONDIDA
    ).count()
    assert analises_respondidas == 1


def test_get_queryset_solicitacoes_homologacao_por_status(
    mock_view_de_homologacao_produto_painel_gerencial, hom_produto_com_editais
):
    mock_request, viewset = mock_view_de_homologacao_produto_painel_gerencial
    user = mock_request.user
    filtro_aplicado = "codae_pediu_analise_reclamacao"
    query_set = viewset.get_queryset_solicitacoes_homologacao_por_status(
        mock_request.query_params,
        user.vinculo_atual.perfil.nome,
        user.tipo_usuario,
        user.vinculo_atual.object_id,
        filtro_aplicado,
        instituicao=user.vinculo_atual.instituicao,
    )
    assert isinstance(query_set, RawQuerySet)
    sql_gerado = str(query_set.query)
    assert sql_gerado.count("SELECT produto_homologacaoproduto.* ") == 1
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT DISTINCT ON (homologacao_produto_id) homologacao_produto_id, escola_id AS escola_reclamacao_id FROM produto_reclamacaodeproduto)"
        )
        == 1
    )
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT id AS escola_id_escola, lote_id FROM escola_escola) "
        )
        == 1
    )
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT id AS lote_id_lote, terceirizada_id, diretoria_regional_id FROM escola_lote)"
        )
        == 1
    )
    assert sql_gerado.count("AND produto_homologacaoproduto.eh_copia = false") == 1
    assert sql_gerado.count("ORDER BY log_criado_em DESC") == 1


def test_build_raw_sql_produtos_por_status_com_dois_editais(
    mock_view_de_homologacao_produto_painel_gerencial,
):
    mock_request, viewset = mock_view_de_homologacao_produto_painel_gerencial
    user = mock_request.user

    filtro_aplicado = "codae_pediu_analise_reclamacao"
    edital = None
    filtros = {}
    editais = "'20', '30'"
    sql_gerado, dados = viewset.build_raw_sql_produtos_por_status(
        filtro_aplicado,
        edital,
        user.vinculo_atual.perfil.nome,
        filtros,
        user.tipo_usuario,
        user.vinculo_atual.object_id,
        editais=editais,
    )
    assert isinstance(dados, dict)
    assert dados == {
        "logs": "dados_comuns_logsolicitacoesusuario",
        "homologacao_produto": "produto_homologacaoproduto",
        "reclamacoes_produto": "produto_reclamacaodeproduto",
        "produto_edital": "produto_produtoedital",
        "escola": "escola_escola",
        "lote": "escola_lote",
        "edital_id": edital,
        "editais": editais,
    }

    assert isinstance(sql_gerado, str)
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT DISTINCT id AS produto_edital_id, suspenso,produto_id as produto_id_prod_edit, edital_id as edital_id_prod_edit FROM %(produto_edital)s) "
        )
        == 1
    )
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT DISTINCT ON (homologacao_produto_id) homologacao_produto_id, escola_id AS escola_reclamacao_id FROM %(reclamacoes_produto)s)"
        )
        == 1
    )
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT id AS escola_id_escola, lote_id FROM %(escola)s)"
        )
        == 1
    )
    assert (
        sql_gerado.count(
            "LEFT JOIN (SELECT id AS lote_id_lote, terceirizada_id, diretoria_regional_id FROM %(lote)s"
        )
        == 1
    )
    assert sql_gerado.count("ORDER BY log_criado_em DESC") == 1
    assert sql_gerado.count("IN ('20', '30')") == 1


def test_trata_edital_com_um_edital(
    mock_view_de_homologacao_produto_painel_gerencial, edital
):
    raw_sql = "SELECT * FROM %(produto_edital)s) AS produto_edital ON produto_edital.produto_id_prod_edit = %(homologacao_produto)s.produto_id"
    _, viewset = mock_view_de_homologacao_produto_painel_gerencial
    sql_gerado = viewset.trata_edital(raw_sql, edital)
    assert isinstance(sql_gerado, str)
    assert (
        sql_gerado.count(f"AND produto_edital.edital_id_prod_edit = {edital.id}") == 1
    )


def test_trata_edital_com_dois_editais(
    mock_view_de_homologacao_produto_painel_gerencial,
):
    raw_sql = "SELECT * FROM %(produto_edital)s) AS produto_edital ON produto_edital.produto_id_prod_edit = %(homologacao_produto)s.produto_id"
    edital = None
    editais = "'20', '30'"
    _, viewset = mock_view_de_homologacao_produto_painel_gerencial
    sql_gerado = viewset.trata_edital(raw_sql, edital, editais)
    assert isinstance(sql_gerado, str)
    assert (
        sql_gerado.count(f"AND produto_edital.edital_id_prod_edit IN ({editais})") == 1
    )


def test_obter_produtos_ordenados_por_edital_e_reclamacoes_filtro_edital(
    mock_view_de_produtos, hom_produto_com_editais
):
    mock_request, viewset = mock_view_de_produtos
    editais = mock_request.query_params.getlist("editais[]")
    filtro_reclamacao = {
        "escola__lote__contratos_do_lote__edital__numero__in": editais,
        "escola__lote__contratos_do_lote__encerrado": False,
    }
    filtro_homologacao = {
        f"homologacao__reclamacoes__escola__lote__contratos_do_lote__edital__numero__in": editais,
        f"homologacao__reclamacoes__escola__lote__contratos_do_lote__encerrado": False,
    }
    qs = viewset.obter_produtos_ordenados_por_edital_e_reclamacoes(
        filtro_reclamacao, filtro_homologacao
    )
    assert qs.count() == 1


def test_obter_produtos_ordenados_por_edital_e_reclamacoes_filtro_status_resposta_tercerizada(
    mock_view_de_produtos, reclamacao_produto_pdf
):
    _, viewset = mock_view_de_produtos

    filtro_reclamacao = {
        "status__in": [ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA]
    }
    filtro_homologacao = {
        "homologacao__reclamacoes__status__in": [
            ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA
        ]
    }
    qs = viewset.obter_produtos_ordenados_por_edital_e_reclamacoes(
        filtro_reclamacao, filtro_homologacao
    )
    assert qs.count() == 1


def test_obter_produtos_ordenados_por_edital_e_reclamacoes_filtro_status_analise_sensorial(
    mock_view_de_produtos, reclamacao_produto_pdf
):
    _, viewset = mock_view_de_produtos
    filtro_reclamacao = {
        "status__in": [ReclamacaoProdutoWorkflow.ANALISE_SENSORIAL_RESPONDIDA]
    }
    filtro_homologacao = {
        "homologacao__reclamacoes__status__in": [
            ReclamacaoProdutoWorkflow.ANALISE_SENSORIAL_RESPONDIDA
        ]
    }
    qs = viewset.obter_produtos_ordenados_por_edital_e_reclamacoes(
        filtro_reclamacao, filtro_homologacao
    )
    assert qs.count() == 0
