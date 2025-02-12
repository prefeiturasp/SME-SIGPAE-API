import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from sme_sigpae_api.dados_comuns.constants import StatusProcessamentoArquivo
from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.escola.models import AlunosMatriculadosPeriodoEscola
from sme_sigpae_api.escola.tasks import (
    atualiza_alunos_escolas,
    atualiza_cache_matriculados_por_faixa,
    atualiza_codigo_codae_das_escolas_task,
    atualiza_dados_escolas,
    atualiza_tipo_gestao_das_escolas_task,
    atualiza_total_alunos_escolas,
    build_pdf_alunos_matriculados,
    calendario_escolas,
    cria_logs_alunos_por_dia_escolas_cei,
    gera_pdf_relatorio_alunos_matriculados_async,
    gera_xlsx_relatorio_alunos_matriculados_async,
    matriculados_por_escola_e_periodo_programas,
    matriculados_por_escola_e_periodo_regulares,
    nega_solicitacoes_pendentes_autorizacao_vencidas,
    nega_solicitacoes_vencidas,
    registra_historico_matriculas_alunos,
)
from sme_sigpae_api.escola.utils import cria_arquivo_excel
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


@patch("django.core.management.call_command")
def test_atualiza_total_alunos_escolas(mock_call_command):
    atualiza_total_alunos_escolas.delay()
    mock_call_command.assert_called_once_with(
        "atualiza_total_alunos_escolas", verbosity=0
    )


@patch("django.core.management.call_command")
def test_atualiza_dados_escolas(mock_call_command):
    atualiza_dados_escolas.delay()
    mock_call_command.assert_called_once_with("atualiza_dados_escolas", verbosity=0)


@patch("django.core.management.call_command")
def test_atualiza_alunos_escolas(mock_call_command):
    atualiza_alunos_escolas.delay()
    mock_call_command.assert_called_once_with("atualiza_alunos_escolas", verbosity=0)


def test_atualiza_codigo_codae_das_escolas_task(codigo_codae_das_escolas):
    escola1, escola2, planilha = codigo_codae_das_escolas
    caminho_arquivo_escola = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"codigo_eol": 123456, "codigo_unidade": 54321},
            {"codigo_eol": 789012, "codigo_unidade": 98765},
        ],
    )
    atualiza_codigo_codae_das_escolas_task(caminho_arquivo_escola, planilha.id)
    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha.refresh_from_db()

    assert escola1.codigo_codae == "54321"
    assert escola2.codigo_codae == "98765"
    assert planilha.codigos_codae_vinculados is True

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)


def test_atualiza_tipo_gestao_das_escolas_task(tipo_gestao_das_escolas):
    (
        escola1,
        escola2,
        planilha_atualizacao_tipo_gestao,
        caminho_arquivo_escola,
        parceira,
        direta,
    ) = tipo_gestao_das_escolas

    atualiza_tipo_gestao_das_escolas_task(
        caminho_arquivo_escola, planilha_atualizacao_tipo_gestao.id
    )
    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha_atualizacao_tipo_gestao.refresh_from_db()

    assert escola1.tipo_gestao == parceira
    assert escola2.tipo_gestao == direta
    assert (
        planilha_atualizacao_tipo_gestao.status
        == StatusProcessamentoArquivo.SUCESSO.value
    )

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)


def test_nega_solicitacoes_vencidas():
    nega_solicitacoes_vencidas()


def test_nega_solicitacoes_pendentes_autorizacao_vencidas():
    nega_solicitacoes_pendentes_autorizacao_vencidas()


def test_matriculados_por_escola_e_periodo_regulares():
    matriculados_por_escola_e_periodo_regulares()


def test_matriculados_por_escola_e_periodo_programas():
    matriculados_por_escola_e_periodo_programas()


def test_calendario_escolas():
    calendario_escolas()


@patch("django.core.management.call_command")
def test_atualiza_cache_matriculados_por_faixa(mock_call_command):
    atualiza_cache_matriculados_por_faixa.delay()
    mock_call_command.assert_called_once_with(
        "atualiza_cache_matriculados_por_faixa", verbosity=0
    )


def test_build_pdf_alunos_matriculados(dados_planilha_alunos_matriculados):
    usuario = dados_planilha_alunos_matriculados["usuario"]
    nome_pdf = "teste.pdf"
    pdf = build_pdf_alunos_matriculados(dados_planilha_alunos_matriculados, nome_pdf)
    assert isinstance(pdf, bytes)

    texto = extrair_texto_de_pdf(pdf)
    assert "Relatório SIGPAE - Alunos matriculados" in texto
    assert f"Solicitado por {usuario}" in texto


def test_gera_pdf_relatorio_alunos_matriculados_async(
    dicionario_de_alunos_matriculados,
    dados_planilha_alunos_matriculados,
    faixas_etarias,
    usuario_coordenador_codae,
):
    uuids = [am.uuid for am in AlunosMatriculadosPeriodoEscola.objects.all()]
    username = usuario_coordenador_codae.username
    nome_pdf = "teste.pdf"
    resultado = gera_pdf_relatorio_alunos_matriculados_async.delay(
        user=username, nome_arquivo=nome_pdf, uuids=uuids
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True

    central_download = CentralDeDownload.objects.get(identificador=nome_pdf)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO


def test_gera_pdf_relatorio_alunos_matriculados_async_erro(usuario_coordenador_codae):
    uuids = "5645645646"
    username = usuario_coordenador_codae.username
    nome_pdf = "teste.pdf"
    gera_pdf_relatorio_alunos_matriculados_async(
        user=username, nome_arquivo=nome_pdf, uuids=uuids
    )

    central_download = CentralDeDownload.objects.get(identificador=nome_pdf)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_ERRO


def test_gera_xlsx_relatorio_alunos_matriculados_async(
    dicionario_de_alunos_matriculados,
    dados_planilha_alunos_matriculados,
    faixas_etarias,
    usuario_coordenador_codae,
):
    uuids = [am.uuid for am in AlunosMatriculadosPeriodoEscola.objects.all()]
    username = usuario_coordenador_codae.username
    nome_pdf = "teste.pdf"
    resultado = gera_xlsx_relatorio_alunos_matriculados_async.delay(
        user=username, nome_arquivo=nome_pdf, uuids=uuids
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True

    central_download = CentralDeDownload.objects.get(identificador=nome_pdf)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO


def test_gera_xlsx_relatorio_alunos_matriculados_async_erro(usuario_coordenador_codae):
    uuids = "5645645646"
    username = usuario_coordenador_codae.username
    nome_pdf = "teste.pdf"
    gera_xlsx_relatorio_alunos_matriculados_async(
        user=username, nome_arquivo=nome_pdf, uuids=uuids
    )

    central_download = CentralDeDownload.objects.get(identificador=nome_pdf)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_ERRO


@patch("django.core.management.call_command")
def test_registra_historico_matriculas_alunos(mock_call_command):
    registra_historico_matriculas_alunos.delay()
    mock_call_command.assert_called_once_with(
        "registra_historico_matriculas_alunos", verbosity=0
    )


@patch("django.core.management.call_command")
def test_registra_historico_matriculas_alunos_com_parametro(mock_call_command):
    registra_historico_matriculas_alunos.apply(kwargs={"ano": "2025"})
    mock_call_command.assert_called_once_with(
        "registra_historico_matriculas_alunos", "--ano=2025", verbosity=0
    )


@patch("django.core.management.call_command")
def test_cria_logs_alunos_por_dia_escolas_cei(mock_call_command):
    cria_logs_alunos_por_dia_escolas_cei.delay()
    mock_call_command.assert_called_once_with(
        "cria_logs_alunos_por_dia_escolas_cei", verbosity=0
    )
