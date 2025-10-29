import pytest

from sme_sigpae_api.dados_comuns.__tests__.conftest import user_diretor_escola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario

pytestmark = pytest.mark.django_db


def test_inicio_fluxo_alteracao_ue_usa_status_correto(
    solicitacao_dieta_especial_aprovada_alteracao_ue,
    usuario_admin,
):
    """Testa se a transição inicia_fluxo usa o status INICIO_FLUXO_ALTERACAO_UE_DIETA_ESPECIAL para alteração UE."""
    usuario = usuario_admin

    solicitacao = solicitacao_dieta_especial_aprovada_alteracao_ue
    solicitacao._inicia_fluxo_hook(user=usuario)

    log = LogSolicitacoesUsuario.objects.get(uuid_original=solicitacao.uuid)
    assert (
        log.status_evento
        == LogSolicitacoesUsuario.INICIO_FLUXO_ALTERACAO_UE_DIETA_ESPECIAL
    )


def test_inicio_fluxo_comum_usa_status_normal(
    solicitacao_dieta_especial_a_autorizar,
):
    """Testa se a transição inicia_fluxo usa INICIO_FLUXO para solicitação comum."""
    solicitacao = solicitacao_dieta_especial_a_autorizar

    log = LogSolicitacoesUsuario.objects.get(uuid_original=solicitacao.uuid)
    assert log.status_evento == LogSolicitacoesUsuario.INICIO_FLUXO

    solicitacao._codae_autoriza_hook(user=solicitacao.criado_por)

    logs = LogSolicitacoesUsuario.objects.filter(uuid_original=solicitacao.uuid)
    print(logs)
    assert logs[0].status_evento == LogSolicitacoesUsuario.CODAE_AUTORIZOU
