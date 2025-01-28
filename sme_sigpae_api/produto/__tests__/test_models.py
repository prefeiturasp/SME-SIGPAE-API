from datetime import date, datetime, timedelta

import pytest

from sme_sigpae_api.produto.models import AnaliseSensorial, UnidadeMedida

pytestmark = pytest.mark.django_db


def test_homologacao_produto_tempo_aguardando_acao_em_dias(homologacao_produto, user):
    homologacao_produto.inicia_fluxo(user=user)
    log = homologacao_produto.logs.first()
    log.criado_em = datetime.today() - timedelta(days=5)
    log.save()
    assert homologacao_produto.tempo_aguardando_acao_em_dias == 5
    homologacao_produto.codae_homologa(user=user, link_pdf="")
    assert homologacao_produto.tempo_aguardando_acao_em_dias == 5


def test_homologacao_produto_data_cadastro(
    homologacao_produto_homologado_com_log, user
):
    hoje = date.today()
    assert homologacao_produto_homologado_com_log.data_cadastro == hoje


def test_produto_componentes_max_length(homologacao_produto_homologado_com_log, user):
    homologacao_produto_homologado_com_log.componentes = "x" * 5000
    assert len(homologacao_produto_homologado_com_log.componentes) == 5000


def test_item_cadastrado_marca(item_cadastrado_1):
    assert item_cadastrado_1.tipo == "MARCA"


def test_modelo_fabricante(fabricante):
    assert fabricante.nome == "Fabricante1"


def test_modelo_marca(marca1):
    assert marca1.nome == "Marca1"


def test_modelo_unidade_medida(unidade_medida):
    assert isinstance(unidade_medida, UnidadeMedida)
    assert unidade_medida.nome == "Litros"


def test_modelo_embalagem(embalagem_produto):
    assert embalagem_produto.nome == "Bag"


def test_produto_logistica(produto_logistica):
    assert produto_logistica.nome == "PRODUTO TESTE"
    assert produto_logistica.tipo_produto == "LOGISTICA"


def test_reclamacao_produto(reclamacao):
    assert reclamacao.reclamante_registro_funcional == "23456789"
    assert reclamacao.reclamante_cargo == "Cargo"
    assert reclamacao.reclamante_nome == "Anderson"


def test_analise_sensorial(analise_sensorial):
    assert analise_sensorial.status == AnaliseSensorial.STATUS_AGUARDANDO_RESPOSTA
