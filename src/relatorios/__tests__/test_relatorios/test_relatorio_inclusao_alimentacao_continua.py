import datetime

import pytest
from django.test import RequestFactory

from src.dados_comuns.models import LogSolicitacoesUsuario
from src.relatorios import relatorios

pytestmark = pytest.mark.django_db


def test_relatorio_inclusao_alimentacao_continua_exibe_encerramento_e_historico_alteracao(
    escola_factory,
    motivo_inclusao_continua_factory,
    inclusao_alimentacao_continua_factory,
    quantidade_por_periodo_factory,
    tipo_alimentacao_factory,
    periodo_escolar_factory,
    usuario_factory,
    log_solicitacoes_usuario_factory,
    monkeypatch,
):
    escola = escola_factory.create(nome="EMEF PERICLES EUGENIO DA SILVA RAMOS")
    motivo = motivo_inclusao_continua_factory.create(
        nome="Programas/Projetos Contínuos"
    )
    periodo_integral = periodo_escolar_factory.create(nome="INTEGRAL")
    periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
    tipo_lanche = tipo_alimentacao_factory.create(nome="Lanche")
    tipo_refeicao = tipo_alimentacao_factory.create(nome="Refeição")
    tipo_lanche_4h = tipo_alimentacao_factory.create(nome="Lanche 4h")
    usuario = usuario_factory.create()

    inclusao = inclusao_alimentacao_continua_factory.create(
        escola=escola,
        motivo=motivo,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_lote=escola.lote,
        rastro_terceirizada=escola.lote.terceirizada,
        data_inicial=datetime.date(2026, 5, 12),
        data_final=datetime.date(2026, 12, 31),
        status="CODAE_AUTORIZADO",
    )

    quantidade_por_periodo_factory.create(
        inclusao_alimentacao_continua=inclusao,
        grupo_inclusao_normal=None,
        periodo_escolar=periodo_integral,
        numero_alunos=40,
        tipos_alimentacao=[tipo_lanche],
        dias_semana=[0, 1, 2, 3],
        encerrado_a_partir_de=datetime.date(2026, 5, 21),
        cancelado_justificativa="sdaasdasd",
    )
    quantidade_por_periodo_factory.create(
        inclusao_alimentacao_continua=inclusao,
        grupo_inclusao_normal=None,
        periodo_escolar=periodo_integral,
        numero_alunos=21,
        tipos_alimentacao=[tipo_refeicao],
        dias_semana=[1, 2, 3],
    )
    quantidade_por_periodo_factory.create(
        inclusao_alimentacao_continua=inclusao,
        grupo_inclusao_normal=None,
        periodo_escolar=periodo_tarde,
        numero_alunos=2,
        tipos_alimentacao=[tipo_lanche_4h],
        dias_semana=[2, 3],
        encerrado_a_partir_de=datetime.date(2026, 5, 30),
        cancelado_justificativa="Sim.",
    )
    quantidade_por_periodo_factory.create(
        inclusao_alimentacao_continua=inclusao,
        grupo_inclusao_normal=None,
        periodo_escolar=periodo_integral,
        numero_alunos=1,
        tipos_alimentacao=[tipo_lanche],
        dias_semana=[1],
    )

    log_inicio = log_solicitacoes_usuario_factory.create(
        uuid_original=inclusao.uuid,
        usuario=usuario,
        solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CONTINUA,
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        justificativa="",
    )
    log_inicio.criado_em = datetime.datetime(2026, 5, 5, 9, 14, 28)
    log_inicio.save(update_fields=["criado_em"])

    log_autorizado = log_solicitacoes_usuario_factory.create(
        uuid_original=inclusao.uuid,
        usuario=usuario,
        solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CONTINUA,
        status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        justificativa="",
    )
    log_autorizado.criado_em = datetime.datetime(2026, 5, 5, 19, 15, 42)
    log_autorizado.save(update_fields=["criado_em"])

    log_alteracao_1 = log_solicitacoes_usuario_factory.create(
        uuid_original=inclusao.uuid,
        usuario=usuario,
        solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CONTINUA,
        status_evento=LogSolicitacoesUsuario.ESCOLA_ALTEROU_ENCERRAMENTO_INCLUSAO_CONTINUA,
        justificativa="sdaasdasd",
    )
    log_alteracao_1.criado_em = datetime.datetime(2026, 5, 6, 17, 22, 51)
    log_alteracao_1.save(update_fields=["criado_em"])

    log_alteracao_2 = log_solicitacoes_usuario_factory.create(
        uuid_original=inclusao.uuid,
        usuario=usuario,
        solicitacao_tipo=LogSolicitacoesUsuario.INCLUSAO_ALIMENTACAO_CONTINUA,
        status_evento=LogSolicitacoesUsuario.ESCOLA_ALTEROU_ENCERRAMENTO_INCLUSAO_CONTINUA,
        justificativa="Sim.",
    )
    log_alteracao_2.criado_em = datetime.datetime(2026, 5, 8, 10, 9, 56)
    log_alteracao_2.save(update_fields=["criado_em"])

    def _fake_html_to_pdf_response(html_string, pdf_filename, request=None):
        return html_string

    monkeypatch.setattr(relatorios, "html_to_pdf_response", _fake_html_to_pdf_response)

    request = RequestFactory().get("/")
    html_string = relatorios.relatorio_inclusao_alimentacao_continua(request, inclusao)

    assert "Encerramento previsto para:" in html_string
    assert "21/05/2026" in html_string
    assert "30/05/2026" in html_string
    assert "Histórico de alteração:" in html_string
    assert "Histórico de cancelamento:" not in html_string
    assert "06/05/2026 17:22:51 - Escola alterou a data fim" in html_string
    assert "INTEGRAL - Lanche -" in html_string
    assert "TARDE - Lanche 4h -" in html_string


def test_relatorio_inclusao_alimentacao_continua_destaca_data_final_quando_todos_periodos_encerram_mesma_data(
    escola_factory,
    motivo_inclusao_continua_factory,
    inclusao_alimentacao_continua_factory,
    quantidade_por_periodo_factory,
    tipo_alimentacao_factory,
    periodo_escolar_factory,
    monkeypatch,
):
    escola = escola_factory.create()
    motivo = motivo_inclusao_continua_factory.create(
        nome="Programas/Projetos Contínuos"
    )
    periodo_integral = periodo_escolar_factory.create(nome="INTEGRAL")
    periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
    tipo_lanche = tipo_alimentacao_factory.create(nome="Lanche")

    inclusao = inclusao_alimentacao_continua_factory.create(
        escola=escola,
        motivo=motivo,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_lote=escola.lote,
        rastro_terceirizada=escola.lote.terceirizada,
        data_inicial=datetime.date(2026, 5, 12),
        data_final=datetime.date(2026, 12, 31),
        status="CODAE_AUTORIZADO",
    )

    for periodo in [periodo_integral, periodo_tarde]:
        quantidade_por_periodo_factory.create(
            inclusao_alimentacao_continua=inclusao,
            grupo_inclusao_normal=None,
            periodo_escolar=periodo,
            numero_alunos=10,
            tipos_alimentacao=[tipo_lanche],
            encerrado_a_partir_de=datetime.date(2026, 5, 21),
            cancelado_justificativa="Encerramento geral",
        )

    def _fake_html_to_pdf_response(html_string, pdf_filename, request=None):
        return html_string

    monkeypatch.setattr(relatorios, "html_to_pdf_response", _fake_html_to_pdf_response)

    request = RequestFactory().get("/")
    html_string = relatorios.relatorio_inclusao_alimentacao_continua(request, inclusao)

    assert "text-decoration: line-through;" in html_string
    assert "21/05/2026" in html_string
    assert "Encerramento previsto para:" not in html_string
