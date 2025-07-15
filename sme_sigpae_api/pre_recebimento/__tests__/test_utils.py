import pytest

from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.services import (
    ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles,
)

pytestmark = pytest.mark.django_db


def test_service_dashboard_solicitacao_alteracao_cronograma_profiles(
    django_user_model, client_autenticado_dilog_abastecimento
):
    service = ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles
    user_id = client_autenticado_dilog_abastecimento.session["_auth_user_id"]
    usuario = django_user_model.objects.get(pk=user_id)
    status_esperados = [
        "CRONOGRAMA_CIENTE",
        "APROVADO_DILOG_ABASTECIMENTO",
        "REPROVADO_DILOG_ABASTECIMENTO",
        "ALTERACAO_ENVIADA_FORNECEDOR",
        "FORNECEDOR_CIENTE",
    ]

    assert service.get_dashboard_status(usuario) == status_esperados


def test_service_dashboard_solicitacao_alteracao_cronograma_profiles_value_error(
    django_user_model, client_autenticado_vinculo_escola
):
    service = ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles
    user_id = client_autenticado_vinculo_escola.session["_auth_user_id"]
    usuario = django_user_model.objects.get(pk=user_id)

    with pytest.raises(ValueError, match="Perfil não existe"):
        service.get_dashboard_status(usuario)
