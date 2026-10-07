import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker
from xworkflows.base import InvalidTransitionError

from src.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_PRODUTO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_GESTAO_PRODUTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    DJANGO_ADMIN_PASSWORD,
    USUARIO_EMPRESA,
)
from src.dados_comuns.fluxo_status import DocumentoDeRecebimentoWorkflow
from src.dados_comuns.models import LogSolicitacoesUsuario, Notificacao
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

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


@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
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
        password=DJANGO_ADMIN_PASSWORD,
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    ficha.inicia_fluxo(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    assert (
        kwargs["titulo"] == f"Ficha Técnica enviada pelo fornecedor - ({ficha.numero})"
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
        f"/pre-recebimento/detalhar-ficha-tecnica?uuid={ficha.uuid}"
        in contexto["url_detalhes_ficha_tecnica"]
    )


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_enviar_email_ao_aprovar(
    mock_enviar_email,
    mock_usuarios_vinculados,
    ficha_tecnica_factory,
    django_user_model,
):
    email_fornecedor = "fornecedor@test.com"
    mock_usuarios_vinculados.return_value = [email_fornecedor]

    usuario = django_user_model.objects.create_user(
        username="codae@test.com",
        password=DJANGO_ADMIN_PASSWORD,
        email="codae@test.com",
        registro_funcional="7654321",
    )

    ficha = ficha_tecnica_factory(
        status=FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_ANALISE
    )

    ficha.gpcodae_aprova(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    # Valida conteúdo do email
    assert kwargs["titulo"] == f"Ficha Técnica Aprovada - ({ficha.numero})"
    assert kwargs["assunto"] == f"[SIGPAE] Ficha Técnica Aprovada - ({ficha.numero})"
    assert kwargs["template"] == "pre_recebimento_email_codae_aprova_ficha_tecnica.html"
    assert email_fornecedor in kwargs["destinatarios"]

    contexto = kwargs["contexto_template"]

    assert contexto["numero_ficha_tecnica"] == ficha.numero
    assert contexto["nome_produto"] == ficha.produto.nome
    assert "data_envio" in contexto
    assert (
        f"/pre-recebimento/detalhar-ficha-tecnica?uuid={ficha.uuid}"
        in contexto["url_detalhes_ficha_tecnica"]
    )


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_salvar_log_ao_aprovar(
    mock_enviar_email,
    mock_usuarios_vinculados,
    ficha_tecnica_factory,
    django_user_model,
):
    mock_usuarios_vinculados.return_value = ["fornecedor@test.com"]

    usuario = django_user_model.objects.create_user(
        username="codae-aprovacao@test.com",
        password=DJANGO_ADMIN_PASSWORD,
        email="codae-aprovacao@test.com",
        registro_funcional="7654321",
    )

    ficha = ficha_tecnica_factory(
        status=FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_ANALISE
    )

    ficha.gpcodae_aprova(user=usuario)

    log = LogSolicitacoesUsuario.objects.get(
        uuid_original=ficha.uuid,
        usuario=usuario,
        status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_APROVADA,
    )

    assert log.status_evento_explicacao == "Ficha Técnica aprovada"


@patch(
    "src.dados_comuns.fluxo_status.PartesInteressadasService."
    "usuarios_vinculados_a_empresa_do_objeto"
)
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_ficha_tecnica_deve_enviar_email_ao_solicitar_correcao(
    mock_enviar_email,
    mock_usuarios_vinculados,
    ficha_tecnica_factory,
    django_user_model,
):
    email_fornecedor = "fornecedor@test.com"
    mock_usuarios_vinculados.return_value = [email_fornecedor]

    usuario = django_user_model.objects.create_user(
        username="codae@test.com",
        password=DJANGO_ADMIN_PASSWORD,
        email="codae@test.com",
        registro_funcional="7654321",
    )

    ficha = ficha_tecnica_factory(
        status=FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_ANALISE
    )

    ficha.gpcodae_envia_para_correcao(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    assert (
        kwargs["titulo"] == f"Correção solicitada na Ficha Técnica - ({ficha.numero})"
    )
    assert (
        kwargs["assunto"]
        == f"[SIGPAE] Correção solicitada na Ficha Técnica - ({ficha.numero})"
    )
    assert (
        kwargs["template"]
        == "pre_recebimento_email_codae_solicita_correcao_ficha_tecnica.html"
    )
    assert email_fornecedor in kwargs["destinatarios"]


@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_deve_enviar_email_quando_fornecedor_corrigir_ficha_tecnica(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    ficha_tecnica_factory,
    django_user_model,
):
    email_coordenador = "coordenador@test.com"
    email_admin = "admin@test.com"
    mock_usuarios_por_perfis.return_value = [email_coordenador, email_admin]

    usuario = django_user_model.objects.create_user(
        username="fornecedor@test.com",
        password=DJANGO_ADMIN_PASSWORD,
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory(
        status=FichaTecnicaDoProduto.workflow_class.ENVIADA_PARA_CORRECAO
    )

    ficha.fornecedor_corrige(user=usuario)

    mock_enviar_email.assert_called_once()

    _, kwargs = mock_enviar_email.call_args

    assert (
        kwargs["titulo"]
        == f"Ficha Técnica corrigida pelo fornecedor - ({ficha.numero})"
    )
    assert (
        kwargs["assunto"]
        == f"Ficha Técnica corrigida pelo fornecedor - ({ficha.numero})"
    )
    assert (
        kwargs["template"]
        == "pre_recebimento_email_fornecedor_corrige_ficha_tecnica.html"
    )
    assert email_coordenador in kwargs["destinatarios"]
    assert email_admin in kwargs["destinatarios"]


@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
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
        password=DJANGO_ADMIN_PASSWORD,
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


@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
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
        password=DJANGO_ADMIN_PASSWORD,
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
        password=DJANGO_ADMIN_PASSWORD,
        email="fornecedor@test.com",
        registro_funcional="1234567",
    )

    ficha = ficha_tecnica_factory()

    assert ficha.status == ficha.workflow_class.RASCUNHO

    ficha.inicia_fluxo(user=usuario)

    ficha.refresh_from_db()

    assert ficha.status == ficha.workflow_class.ENVIADA_PARA_ANALISE


PERFIS_EMAIL_DOCUMENTOS_PENDENTES_APROVACAO = [
    DILOG_QUALIDADE,
    DILOG_CRONOGRAMA,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
]


def _nomes_perfis_email(mock_usuarios_por_perfis):
    for call in mock_usuarios_por_perfis.call_args_list:
        if call.kwargs.get("somente_email") is True:
            return call.kwargs["nomes_perfis"]
    raise AssertionError("Nenhuma chamada de e-mail foi feita.")


def _criar_usuario_fornecedor(django_user_model, email="fornecedor@test.com"):
    return django_user_model.objects.create_user(
        username=email,
        password=DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional="1234567",
        cpf="12345678901",
        nome="Fornecedor Teste",
    )


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_notificacao")
@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_documento_recebimento_email_pendentes_aprovacao_ao_iniciar_fluxo(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    mock_enviar_notificacao,
    documento_de_recebimento_factory,
    django_user_model,
):
    mock_usuarios_por_perfis.return_value = ["qualidade@test.com"]
    usuario = _criar_usuario_fornecedor(django_user_model)
    documento = documento_de_recebimento_factory()

    documento.inicia_fluxo(user=usuario)

    mock_enviar_email.assert_called_once()
    nomes_perfis = _nomes_perfis_email(mock_usuarios_por_perfis)

    assert nomes_perfis == PERFIS_EMAIL_DOCUMENTOS_PENDENTES_APROVACAO
    assert DILOG_DIRETORIA not in nomes_perfis
    assert ADMINISTRADOR_CODAE_GABINETE not in nomes_perfis


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_notificacao")
@patch("src.dados_comuns.fluxo_status.PartesInteressadasService.usuarios_por_perfis")
@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_documento_recebimento_email_pendentes_aprovacao_ao_atualizar(
    mock_enviar_email,
    mock_usuarios_por_perfis,
    mock_enviar_notificacao,
    documento_de_recebimento_factory,
    django_user_model,
):
    mock_usuarios_por_perfis.return_value = ["qualidade@test.com"]
    usuario = _criar_usuario_fornecedor(django_user_model)
    documento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimentoWorkflow.APROVADO
    )

    documento.fornecedor_atualiza(user=usuario)

    mock_enviar_email.assert_called_once()
    nomes_perfis = _nomes_perfis_email(mock_usuarios_por_perfis)

    assert nomes_perfis == PERFIS_EMAIL_DOCUMENTOS_PENDENTES_APROVACAO
    assert DILOG_DIRETORIA not in nomes_perfis
    assert ADMINISTRADOR_CODAE_GABINETE not in nomes_perfis


def test_documento_recebimento_reprovacao_registra_log_com_justificativa(
    documento_de_recebimento_factory,
    django_user_model,
):
    usuario = _criar_usuario_fornecedor(django_user_model)
    documento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE
    )
    justificativa = "Documento não está de acordo com as informações esperadas."

    documento.qualidade_reprova_analise(user=usuario, justificativa=justificativa)

    documento.refresh_from_db()
    assert documento.status == DocumentoDeRecebimentoWorkflow.REPROVADO
    log = documento.logs.filter(
        status_evento=LogSolicitacoesUsuario.DOCUMENTO_REPROVADO
    ).first()
    assert log is not None
    assert log.justificativa == justificativa
    assert log.usuario == usuario


def test_documento_recebimento_reprovado_eh_terminal(
    documento_de_recebimento_factory,
    django_user_model,
):
    usuario = _criar_usuario_fornecedor(django_user_model)
    documento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimentoWorkflow.REPROVADO
    )

    with pytest.raises(InvalidTransitionError):
        documento.fornecedor_atualiza(user=usuario)


def _criar_usuario_empresa(django_user_model, email, nome):
    return django_user_model.objects.create_user(
        username=email,
        password=DJANGO_ADMIN_PASSWORD,
        email=email,
        nome=nome,
    )


def _criar_vinculo_empresa(usuario, empresa, nome_perfil):
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=empresa,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_documento_recebimento_reprovacao_envia_email_para_usuarios_da_empresa(
    mock_enviar_email,
    documento_de_recebimento_factory,
    django_user_model,
):
    documento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE
    )
    justificativa = "Documento não está de acordo com as informações esperadas."
    analista = _criar_usuario_fornecedor(django_user_model)
    admin_empresa = _criar_usuario_empresa(
        django_user_model, "admin.empresa@test.com", "Admin Empresa"
    )
    usuario_empresa = _criar_usuario_empresa(
        django_user_model, "usuario.empresa@test.com", "Usuario Empresa"
    )
    usuario_outra_empresa = _criar_usuario_empresa(
        django_user_model, "outra.empresa@test.com", "Outra Empresa"
    )
    _criar_vinculo_empresa(
        admin_empresa, documento.cronograma.empresa, ADMINISTRADOR_EMPRESA
    )
    _criar_vinculo_empresa(
        usuario_empresa, documento.cronograma.empresa, USUARIO_EMPRESA
    )
    _criar_vinculo_empresa(
        usuario_outra_empresa, baker.make("Terceirizada"), USUARIO_EMPRESA
    )

    documento.qualidade_reprova_analise(user=analista, justificativa=justificativa)

    assert mock_enviar_email.call_count == 2
    chamadas = {
        call.kwargs["destinatarios"][0]: call.kwargs
        for call in mock_enviar_email.call_args_list
    }
    assert set(chamadas) == {"admin.empresa@test.com", "usuario.empresa@test.com"}
    kwargs = chamadas["admin.empresa@test.com"]
    assert kwargs["titulo"] == "DOCUMENTOS DE RECEBIMENTO"
    assert kwargs["assunto"] == "SIGPAE - Documento(s) de Recebimento (s) Reprovado(s)"
    assert kwargs["template"] == (
        "pre_recebimento_email_qualidade_reprova_documento_recebimento.html"
    )
    assert (
        kwargs["contexto_template"]["numero_cronograma"] == documento.cronograma.numero
    )
    assert kwargs["contexto_template"]["nome_produto"] == (
        documento.cronograma.ficha_tecnica.produto.nome
    )
    assert kwargs["contexto_template"]["justificativa_reprovacao"] == justificativa
    assert kwargs["contexto_template"]["nome_usuario"] == "Admin Empresa"
    assert (
        chamadas["usuario.empresa@test.com"]["contexto_template"]["nome_usuario"]
        == "Usuario Empresa"
    )


@patch("src.dados_comuns.fluxo_status.EmailENotificacaoService.enviar_email")
def test_documento_recebimento_reprovacao_sem_usuarios_na_empresa_nao_envia_email(
    mock_enviar_email,
    documento_de_recebimento_factory,
    django_user_model,
):
    documento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE
    )
    analista = _criar_usuario_fornecedor(django_user_model)

    documento.qualidade_reprova_analise(
        user=analista, justificativa="Fora do esperado."
    )

    mock_enviar_email.assert_not_called()
