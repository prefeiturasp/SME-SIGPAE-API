from unittest.mock import MagicMock

import pytest

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoHistoricoDietasEspeciais,
    PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma,
    PermissaoParaCriarUsuarioComCoresso,
    PermissaoParaDashboardCronograma,
    PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma,
    PermissaoParaVisualizarCalendarioCronograma,
    PermissaoParaVisualizarCronograma,
    PermissaoParaVisualizarRelatorioCronograma,
    PermissaoParaVisualizarSolicitacoesAlteracaoCronograma,
    PermissaoRelatorioRecreioNasFerias,
    UsuarioAdministradorContratos,
    UsuarioDilogAbastecimento,
)

pytestmark = pytest.mark.django_db


def test_usuario_contratos_criar_usuario(user_admin_contratos):
    request = MagicMock()
    request.user = user_admin_contratos
    permissao = PermissaoParaCriarUsuarioComCoresso()
    assert permissao.has_permission(request, None)


def test_usuario_com_permissao_administrador_contrato(user_admin_contratos):
    request = MagicMock()
    request.user = user_admin_contratos
    permissao = UsuarioAdministradorContratos()
    assert permissao.has_permission(request, None)


def test_usuario_sem_permissao_administrador_contrato(
    usuario_teste_notificacao_autenticado,
):
    usuario, _ = usuario_teste_notificacao_autenticado
    request = MagicMock()
    request.user = usuario
    permissao = UsuarioAdministradorContratos()
    assert not permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento(user_dilog_abastecimento):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = UsuarioDilogAbastecimento()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_visualizar_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaVisualizarCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_visualizar_relatorio_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaVisualizarRelatorioCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_dashboard_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaDashboardCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_visualizar_calendario_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaVisualizarCalendarioCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_visualizar_solicitacoes_alteracao_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaVisualizarSolicitacoesAlteracaoCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_listar_dashboard_solicitacao_alteracao_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_dilog_abastecimento_permissao_para_analisar_solicitacao_alteracao_cronograma(
    user_dilog_abastecimento,
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma()
    assert permissao.has_permission(request, None)


def test_usuario_permissao_historico_dietas_especiais(usuario_da_dre):
    usuario, _ = usuario_da_dre
    request = MagicMock()
    request.user = usuario
    permissao = PermissaoHistoricoDietasEspeciais()
    assert permissao.has_permission(request, None)


def test_usuario_permissao_historico_dietas_especiais_sem_permissao(
    user_dilog_abastecimento, user_admin_contratos
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoHistoricoDietasEspeciais()
    assert not permissao.has_permission(request, None)

    request.user = user_admin_contratos
    permissao = PermissaoHistoricoDietasEspeciais()
    assert not permissao.has_permission(request, None)


def test_usuario_permissao_relatorio_recreio_nas_ferias(usuario_da_dre):
    usuario, _ = usuario_da_dre
    request = MagicMock()
    request.user = usuario
    permissao = PermissaoRelatorioRecreioNasFerias()
    assert permissao.has_permission(request, None)


def test_usuario_permissao_historico_dietas_especiais_sem_permissao(
    user_dilog_abastecimento, user_admin_contratos
):
    request = MagicMock()
    request.user = user_dilog_abastecimento
    permissao = PermissaoRelatorioRecreioNasFerias()
    assert not permissao.has_permission(request, None)

    request.user = user_admin_contratos
    permissao = PermissaoRelatorioRecreioNasFerias()
    assert not permissao.has_permission(request, None)
