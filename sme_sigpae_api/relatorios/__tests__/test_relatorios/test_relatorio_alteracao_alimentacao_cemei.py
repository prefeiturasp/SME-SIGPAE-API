import datetime

import pytest
from django.test import RequestFactory

from sme_sigpae_api.relatorios import relatorios

pytestmark = pytest.mark.django_db


def test_relatorio_alteracao_alimentacao_cemei_aplica_nome_historico_escola(
    escola_factory,
    historico_escola_factory,
    alteracao_cardapio_cemei_factory,
    motivo_alteracao_cardapio_factory,
    data_intervalo_alteracao_cardapio_cemei_factory,
    substituicao_alimentacao_no_periodo_escolar_cemeicei_factory,
    substituicao_alimentacao_no_periodo_escolar_cemeiemei_factory,
    faixa_etaria_substituicao_alimentacao_cemeicei_factory,
    tipo_alimentacao_factory,
    periodo_escolar_factory,
    tipo_unidade_escolar_factory,
    vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar_factory,
    monkeypatch,
):
    tipo_unidade_cemei = tipo_unidade_escolar_factory.create(iniciais="CEMEI")
    escola = escola_factory.create(
        nome="CEMEI ATUAL",
        codigo_eol="123456",
        tipo_unidade=tipo_unidade_cemei,
    )
    escola_nome_atual = escola.nome
    data_solicitacao = datetime.date(2025, 1, 10)
    historico_nome = "CEMEI HISTORICO"

    historico_escola_factory.create(
        escola=escola,
        nome=historico_nome,
        data_inicial=datetime.date(2024, 12, 1),
        data_final=datetime.date(2025, 12, 31),
    )

    motivo = motivo_alteracao_cardapio_factory.create(nome="Atividade diferenciada")
    alteracao_cardapio = alteracao_cardapio_cemei_factory.create(
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        motivo=motivo,
        data_inicial=data_solicitacao,
        data_final=data_solicitacao,
    )

    data_intervalo_alteracao_cardapio_cemei_factory.create(
        alteracao_cardapio_cemei=alteracao_cardapio,
        data=data_solicitacao,
    )

    periodo = periodo_escolar_factory.create(nome="MANHA")
    tipo_de = tipo_alimentacao_factory.create(nome="Lanche")
    tipo_para = tipo_alimentacao_factory.create(nome="Refeição")

    tipo_unidade_cei = tipo_unidade_escolar_factory.create(iniciais="CEI DIRET")
    tipo_unidade_emei = tipo_unidade_escolar_factory.create(iniciais="EMEI")

    vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar_factory.create(
        periodo_escolar=periodo,
        tipo_unidade_escolar=tipo_unidade_cei,
        tipos_alimentacao=[tipo_de, tipo_para],
    )
    vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar_factory.create(
        periodo_escolar=periodo,
        tipo_unidade_escolar=tipo_unidade_emei,
        tipos_alimentacao=[tipo_de, tipo_para],
    )

    substituicao_cei = (
        substituicao_alimentacao_no_periodo_escolar_cemeicei_factory.create(
            alteracao_cardapio=alteracao_cardapio,
            periodo_escolar=periodo,
            tipos_alimentacao_de=[tipo_de],
            tipos_alimentacao_para=[tipo_para],
        )
    )
    faixa_etaria_substituicao_alimentacao_cemeicei_factory.create(
        substituicao_alimentacao=substituicao_cei,
        quantidade=10,
        matriculados_quando_criado=12,
    )

    substituicao_alimentacao_no_periodo_escolar_cemeiemei_factory.create(
        alteracao_cardapio=alteracao_cardapio,
        periodo_escolar=periodo,
        qtd_alunos=20,
        matriculados_quando_criado=25,
        tipos_alimentacao_de=[tipo_de],
        tipos_alimentacao_para=[tipo_para],
    )

    def _fake_html_to_pdf_response(html_string, pdf_filename, request=None):
        return html_string

    monkeypatch.setattr(relatorios, "html_to_pdf_response", _fake_html_to_pdf_response)

    request = RequestFactory().get("/")
    html_string = relatorios.relatorio_alteracao_alimentacao_cemei(
        request, alteracao_cardapio
    )

    nome_historico_esperado = f"{historico_nome} (ATUAL {escola_nome_atual})"
    assert nome_historico_esperado in html_string
    assert escola.codigo_eol in html_string
    assert "Alunos CEI" in html_string
    assert "Alunos EMEI" in html_string
    assert "Atividade diferenciada" in html_string
