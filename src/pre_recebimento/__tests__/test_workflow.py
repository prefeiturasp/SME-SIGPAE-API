from unittest.mock import patch

import pytest

from src.dados_comuns.models import LogSolicitacoesUsuario

pytestmark = pytest.mark.django_db


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_deve_enviar_email_ao_iniciar_fluxo(
    mock_enviar_email,
    mock_usuarios_vinculados,
    cronograma_semanal_rascunho,
    client_autenticado_vinculo_dilog_cronograma,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma

    mock_usuarios_vinculados.return_value = ["teste@empresa.com"]

    cronograma_semanal_rascunho.inicia_fluxo(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    assert (
        kwargs["titulo"]
        == f"Cronograma Criado: Nº {cronograma_semanal_rascunho.numero}"
    )
    assert (
        kwargs["assunto"]
        == f"[SIGPAE] Ciência do cronograma Nº {cronograma_semanal_rascunho.numero}"
    )
    assert kwargs["template"] == "pre_recebimento_email_criacao_cronograma_semanal.html"
    assert kwargs["destinatarios"] == ["teste@empresa.com"]

    contexto = kwargs["contexto_template"]

    assert contexto["numero_cronograma"] == cronograma_semanal_rascunho.numero
    assert "url_detalhe_cronograma" in contexto
    assert (
        f"pre-recebimento/detalhe-cronograma-semanal?uuid={str(cronograma_semanal_rascunho.uuid)}"
        in contexto["url_detalhe_cronograma"]
    )


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_deve_salvar_log_ao_iniciar_fluxo(
    mock_enviar_email,
    mock_usuarios_vinculados,
    cronograma_semanal_rascunho,
    client_autenticado_vinculo_dilog_cronograma,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma

    mock_usuarios_vinculados.return_value = ["teste@empresa.com"]

    cronograma_semanal_rascunho.inicia_fluxo(user=usuario)

    assert LogSolicitacoesUsuario.objects.filter(
        uuid_original=cronograma_semanal_rascunho.uuid,
        usuario=usuario,
        status_evento=(LogSolicitacoesUsuario.CRONOGRAMA_SEMANAL_ENVIADO_AO_FORNECEDOR),
    ).exists()


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_nao_deve_enviar_email_sem_usuario(
    mock_enviar_email, cronograma_semanal_rascunho
):

    cronograma_semanal_rascunho.inicia_fluxo()

    mock_enviar_email.assert_not_called()


def test_deve_alterar_status_ao_iniciar_fluxo(
    cronograma_semanal_rascunho,
    client_autenticado_vinculo_dilog_cronograma,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma

    cronograma_semanal_rascunho.inicia_fluxo(user=usuario)

    cronograma_semanal_rascunho.refresh_from_db()

    assert (
        cronograma_semanal_rascunho.status
        == cronograma_semanal_rascunho.workflow_class.ENVIADO_AO_FORNECEDOR
    )
