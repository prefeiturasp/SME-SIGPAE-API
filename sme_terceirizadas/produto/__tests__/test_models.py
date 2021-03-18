from datetime import date, datetime, timedelta

import pytest

pytestmark = pytest.mark.django_db


def test_homologacao_produto_tempo_aguardando_acao_em_dias(homologacao_produto, user):
    homologacao_produto.inicia_fluxo(user=user)
    log = homologacao_produto.logs.first()
    log.criado_em = datetime.today() - timedelta(days=5)
    log.save()
    assert homologacao_produto.tempo_aguardando_acao_em_dias == 5
    homologacao_produto.codae_homologa(user=user, link_pdf='')
    assert homologacao_produto.tempo_aguardando_acao_em_dias == 5


def test_homologacao_produto_data_cadastro(homologacao_produto_homologado_com_log, user):
    hoje = date.today()
    assert homologacao_produto_homologado_com_log.data_cadastro == hoje


def test_produto_componentes_max_length(homologacao_produto_homologado_com_log, user):
    homologacao_produto_homologado_com_log.componentes = 'x' * 5000
    assert len(homologacao_produto_homologado_com_log.componentes) == 5000
