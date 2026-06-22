from unittest.mock import patch

import pytest

from src.dados_comuns.constants import (
    ADMINISTRADOR_GESTAO_PRODUTO,
    COORDENADOR_GESTAO_PRODUTO,
)
from src.dados_comuns.models import LogSolicitacoesUsuario, Notificacao

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
    client_user_autenticado_fornecedor,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma
    _, fornecedor = client_user_autenticado_fornecedor

    mock_usuarios_vinculados.side_effect = [
        [fornecedor.email],
        [fornecedor],
    ]

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
    assert kwargs["destinatarios"] == [fornecedor.email]

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
    client_user_autenticado_fornecedor,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma

    _, fornecedor = client_user_autenticado_fornecedor

    mock_usuarios_vinculados.side_effect = [
        [fornecedor.email],
        [fornecedor],
    ]

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


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_notificacao")
def test_deve_enviar_notificacao_ao_iniciar_fluxo(
    mock_enviar_notificacao,
    mock_usuarios_vinculados,
    cronograma_semanal_rascunho,
    client_autenticado_vinculo_dilog_cronograma,
    client_user_autenticado_fornecedor,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma
    _, fornecedor = client_user_autenticado_fornecedor

    mock_usuarios_vinculados.side_effect = [
        [fornecedor.email],
        [fornecedor],
    ]

    cronograma_semanal_rascunho.inicia_fluxo(user=usuario)

    mock_enviar_notificacao.assert_called_once()

    _, kwargs = mock_enviar_notificacao.call_args

    numero_cronograma = cronograma_semanal_rascunho.numero
    nome_produto = (
        cronograma_semanal_rascunho.cronograma_mensal.ficha_tecnica.produto.nome
    )

    assert (
        kwargs["template"]
        == "pre_recebimento_notificacao_criacao_cronograma_semanal.html"
    )

    assert kwargs["titulo_notificacao"] == (
        f"Cronograma Ponto a Ponto {numero_cronograma} – "
        f"{nome_produto} criado pela CODAE."
    )

    assert kwargs["tipo_notificacao"] == Notificacao.TIPO_NOTIFICACAO_ALERTA

    assert kwargs["categoria_notificacao"] == (
        Notificacao.CATEGORIA_NOTIFICACAO_CRIACAO_CRONOGRAMA_PONTO_A_PONTO
    )

    assert kwargs["usuarios"] == [fornecedor]

    assert (
        f"pre-recebimento/detalhe-cronograma-semanal?uuid="
        f"{str(cronograma_semanal_rascunho.uuid)}" in kwargs["link_acesse_aqui"]
    )

    contexto = kwargs["contexto_template"]

    assert contexto["numero_cronograma"] == numero_cronograma

    assert contexto["nome_produto"] == nome_produto

    assert "data_evento" in contexto


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_notificacao")
def test_nao_deve_enviar_notificacao_sem_usuario(
    mock_enviar_notificacao,
    cronograma_semanal_rascunho,
):
    cronograma_semanal_rascunho.inicia_fluxo()

    mock_enviar_notificacao.assert_not_called()


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_notificacao")
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_deve_enviar_email_e_notificacao_para_usuarios_vinculados(
    mock_enviar_email,
    mock_enviar_notificacao,
    mock_usuarios_vinculados,
    cronograma_semanal_rascunho,
    client_autenticado_vinculo_dilog_cronograma,
    client_user_autenticado_fornecedor,
    client_user_autenticado_fornecedor_usuario,
):
    _, usuario = client_autenticado_vinculo_dilog_cronograma
    _, fornecedor = client_user_autenticado_fornecedor
    _, funcionario = client_user_autenticado_fornecedor_usuario

    mock_usuarios_vinculados.side_effect = [
        [fornecedor.email, funcionario.email],
        [fornecedor, funcionario],
    ]

    cronograma_semanal_rascunho.inicia_fluxo(user=usuario)

    mock_enviar_email.assert_called_once()
    mock_enviar_notificacao.assert_called_once()

    _, kwargs_email = mock_enviar_email.call_args

    assert fornecedor.email in kwargs_email["destinatarios"]
    assert funcionario.email in kwargs_email["destinatarios"]

    _, kwargs_notificacao = mock_enviar_notificacao.call_args

    assert fornecedor in kwargs_notificacao["usuarios"]
    assert funcionario in kwargs_notificacao["usuarios"]


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_enviar_email_ao_iniciar_fluxo(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    ficha_tecnica_factory,
    django_user_model,
):
    email_coordenador = "coordenador@test.com"
    email_admin = "admin@test.com"
    mock_usuarios_por_perfis.side_effect = [
        [email_coordenador, email_admin],
    ]

    usuario = django_user_model.objects.create_user(
        username="fornecedor@test.com",
        password="123",
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    ficha.inicia_fluxo(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    assert (
        kwargs["titulo"]
        == f"Ficha Técnica enviada pelo fornecedor - ({ficha.numero})"
    )
    assert (
        kwargs["assunto"]
        == f"[SIGPAE] Ficha Técnica enviada pelo fornecedor - ({ficha.numero})"
    )
    assert (
        kwargs["template"]
        == "pre_recebimento_email_fornecedor_envia_ficha_tecnica.html"
    )
    assert email_coordenador in kwargs["destinatarios"]
    assert email_admin in kwargs["destinatarios"]

    contexto = kwargs["contexto_template"]

    nome_fornecedor_esperado = (
        f"{ficha.empresa.nome_fantasia} - {ficha.empresa.razao_social}"
    )
    assert contexto["nome_fornecedor"] == nome_fornecedor_esperado
    assert contexto["numero_ficha_tecnica"] == ficha.numero
    assert contexto["nome_produto"] == ficha.produto.nome
    assert "data_envio" in contexto
    assert (
        f"/pre-recebimento/ficha-tecnica/{ficha.uuid}"
        in contexto["url_detalhes_ficha_tecnica"]
    )

    # Sem cronograma vinculado, CP e ATA devem ser None
    assert contexto["numero_cp"] is None
    assert contexto["numero_ata"] is None


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_salvar_log_ao_iniciar_fluxo(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    ficha_tecnica_factory,
    django_user_model,
):
    mock_usuarios_por_perfis.side_effect = [
        ["email@test.com"],
    ]

    usuario = django_user_model.objects.create_user(
        username="fornecedor@test.com",
        password="123",
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    ficha.inicia_fluxo(user=usuario)

    assert LogSolicitacoesUsuario.objects.filter(
        uuid_original=ficha.uuid,
        usuario=usuario,
        status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_ANALISE,
    ).exists()


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_consultar_perfis_corretos(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    ficha_tecnica_factory,
    django_user_model,
):
    mock_usuarios_por_perfis.side_effect = [
        ["email@test.com"],
    ]

    usuario = django_user_model.objects.create_user(
        username="fornecedor@test.com",
        password="123",
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    ficha.inicia_fluxo(user=usuario)

    mock_usuarios_por_perfis.assert_called_once_with(
        nomes_perfis=[
            COORDENADOR_GESTAO_PRODUTO,
            ADMINISTRADOR_GESTAO_PRODUTO,
        ],
        somente_email=True,
    )


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_nao_deve_enviar_email_sem_usuario(
    mock_enviar_email,
    ficha_tecnica_factory,
):
    ficha = ficha_tecnica_factory()

    ficha.inicia_fluxo()

    mock_enviar_email.assert_not_called()


def test_ficha_tecnica_deve_alterar_status_ao_iniciar_fluxo(
    ficha_tecnica_factory,
    django_user_model,
):
    usuario = django_user_model.objects.create_user(
        username="fornecedor@test.com",
        password="123",
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    assert ficha.status == ficha.workflow_class.RASCUNHO

    ficha.inicia_fluxo(user=usuario)

    ficha.refresh_from_db()

    assert (
        ficha.status
        == ficha.workflow_class.ENVIADA_PARA_ANALISE
    )
