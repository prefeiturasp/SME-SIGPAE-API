import datetime

import pytest
from django.test import RequestFactory

from sme_sigpae_api.relatorios import relatorios

pytestmark = pytest.mark.django_db


def test_relatorio_alteracao_cardapio_aplica_nome_historico_escola(
    escola_factory,
    historico_escola_factory,
    alteracao_cardapio_factory,
    motivo_alteracao_cardapio_factory,
    data_intervalo_alteracao_cardapio_factory,
    substituicao_alimentacao_no_periodo_escolar_factory,
    tipo_alimentacao_factory,
    periodo_escolar_factory,
    monkeypatch,
):
    escola = escola_factory.create(nome="EMEI ATUAL", codigo_eol="123456")
    escola_nome_atual = escola.nome
    data_solicitacao = datetime.date(2025, 1, 10)
    historico_nome = "EMEI HISTORICO"

    historico_escola_factory.create(
        escola=escola,
        nome=historico_nome,
        data_inicial=datetime.date(2024, 12, 1),
        data_final=datetime.date(2025, 12, 31),
    )

    motivo = motivo_alteracao_cardapio_factory.create(nome="Atividade diferenciada")
    alteracao_cardapio = alteracao_cardapio_factory.create(
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        motivo=motivo,
        data_inicial=data_solicitacao,
        data_final=data_solicitacao,
    )

    data_intervalo_alteracao_cardapio_factory.create(
        alteracao_cardapio=alteracao_cardapio,
        data=data_solicitacao,
    )

    periodo = periodo_escolar_factory.create(nome="MANHA")
    tipo_de = tipo_alimentacao_factory.create(nome="Lanche")
    tipo_para = tipo_alimentacao_factory.create(nome="Refeição")

    substituicao_alimentacao_no_periodo_escolar_factory.create(
        alteracao_cardapio=alteracao_cardapio,
        periodo_escolar=periodo,
        qtd_alunos=50,
        tipos_alimentacao_de=[tipo_de],
        tipos_alimentacao_para=[tipo_para],
    )

    def _fake_html_to_pdf_response(html_string, pdf_filename, request=None):
        return html_string

    monkeypatch.setattr(relatorios, "html_to_pdf_response", _fake_html_to_pdf_response)

    request = RequestFactory().get("/")
    html_string = relatorios.relatorio_alteracao_cardapio(request, alteracao_cardapio)

    nome_historico_esperado = f"{historico_nome} (ATUAL {escola_nome_atual})"
    assert nome_historico_esperado in html_string
    assert escola.codigo_eol in html_string
    assert "Atividade diferenciada" in html_string
