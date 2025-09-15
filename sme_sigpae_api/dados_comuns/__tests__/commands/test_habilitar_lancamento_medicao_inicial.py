import io
import os
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

pytestmark = pytest.mark.django_db


@override_settings(DJANGO_ENV="development")
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.incluir_etec"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.incluir_programas_e_projetos"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.solicitar_lanche_emergencial"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.solicitar_kit_lanche"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.incluir_log_alunos_matriculados"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.habilitar_dias_letivos"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.obter_escolas"
)
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.obter_usuario"
)
@mock.patch("sme_sigpae_api.escola.models.Escola.objects.get")
def test_executa_com_sucesso(
    mock_get_escola,
    mock_obter_usuario,
    mock_obter_escolas,
    mock_habilitar_dias_letivos,
    mock_incluir_logs,
    mock_solicitar_kit_lache,
    mock_solicitar_lanche_emergencial,
    mock_programas_e_projetos,
    mock_etec,
    user_diretor_escola,
    escola,
):
    usuario, _ = user_diretor_escola

    escola_fake = mock.Mock()
    escola_fake.nome = escola.nome
    escola_fake.eh_cemei = False
    escola_fake.eh_cei = False
    escola_fake.eh_emebs = False
    escola_fake.eh_emef = True
    escola_fake.eh_ceu_gestao = False
    escola_fake.periodos_escolares.return_value.get.return_value = mock.Mock()

    mock_get_escola.return_value = escola_fake
    mock_obter_escolas.return_value = [
        {"nome_escola": escola.nome, "email": usuario.email, "periodos": ["MANHA"]}
    ]
    mock_obter_usuario.return_value = usuario
    mock_solicitar_kit_lache.return_value = "OK"
    mock_solicitar_lanche_emergencial.return_value = "OK"
    mock_programas_e_projetos.return_value = "OK"
    mock_etec.return_value = "OK"

    with open(os.devnull, "w") as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            call_command(
                "habilitar_lancamento_medicao_inicial", "--ano", "2024", "--mes", "5"
            )

    mock_get_escola.assert_called_once()
    mock_obter_usuario.assert_called_once()
    mock_obter_escolas.assert_called_once()
    mock_habilitar_dias_letivos.assert_called_once()
    mock_incluir_logs.assert_called_once()
    mock_solicitar_kit_lache.assert_called_once()
    mock_solicitar_lanche_emergencial.assert_called_once()
    mock_programas_e_projetos.assert_called_once()
    mock_etec.assert_called_once()


@override_settings(DJANGO_ENV="production")
@mock.patch(
    "utility.carga_dados.medicao.insere_informacoes_lancamento_inicial.obter_escolas"
)
def test_nao_executa_em_producao(mock_obter_escolas):
    out = io.StringIO()
    with mock.patch.dict(os.environ, {"DJANGO_ENV": "production"}):
        call_command(
            "habilitar_lancamento_medicao_inicial",
            "--ano",
            "2024",
            "--mes",
            "5",
            stdout=out,
        )

    assert "SÓ PODE EXECUTAR EM DESENVOLVIMENTO" in out.getvalue()
    mock_obter_escolas.assert_not_called()


@override_settings(DJANGO_ENV="development")
def test_parametros_obrigatorios_nao_enviados_lanca_erro():
    with pytest.raises(
        CommandError, match="Error: the following arguments are required: --ano"
    ):
        call_command("habilitar_lancamento_medicao_inicial")

    with pytest.raises(
        CommandError, match="Error: the following arguments are required: --mes"
    ):
        call_command("habilitar_lancamento_medicao_inicial", "--ano", "2024")


@override_settings(DJANGO_ENV="development")
def test_mes_invalido_lanca_erro():
    with pytest.raises(CommandError, match="Mês deve estar entre 1 e 12"):
        call_command(
            "habilitar_lancamento_medicao_inicial",
            "--ano",
            "2024",
            "--mes",
            "13",
        )


@override_settings(DJANGO_ENV="development")
def test_data_kit_lanche_invalido_lanca_erro():
    with pytest.raises(
        CommandError, match="Dia do kit lanche deve estar entre 1 e 31 para 05/2024"
    ):
        call_command(
            "habilitar_lancamento_medicao_inicial",
            "--ano",
            "2024",
            "--mes",
            "5",
            "--data-kit-lanche",
            "123",
        )


@override_settings(DJANGO_ENV="development")
def test_data_lanche_emergencial_invalido_lanca_erro():
    with pytest.raises(
        CommandError,
        match="Dia do lanche emergencial deve estar entre 1 e 31 para 05/2024",
    ):
        call_command(
            "habilitar_lancamento_medicao_inicial",
            "--ano",
            "2024",
            "--mes",
            "5",
            "--data-lanche-emergencial",
            "123",
        )
