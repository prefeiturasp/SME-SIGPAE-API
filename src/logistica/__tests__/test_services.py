import pytest

from src.dados_comuns.fluxo_status import GuiaRemessaWorkFlow
from src.logistica.models.guia import Guia
from src.logistica.services import cancelar_guias

pytestmark = pytest.mark.django_db


def test_action_cancelar_guias(
    guia, guia_com_escola_client_autenticado, guia_pendente_de_conferencia
):
    queryset = Guia.objects.all()
    solicitacao = queryset.first().solicitacao

    assert not queryset.filter(status=GuiaRemessaWorkFlow.CANCELADA).exists()
    assert not solicitacao.todas_as_guias_canceladas
    assert not solicitacao.cancelada

    cancelar_guias(queryset)

    solicitacao.refresh_from_db()
    qtd_guias_canceladas = Guia.objects.filter(
        status=GuiaRemessaWorkFlow.CANCELADA
    ).count()
    qtd_total_guias = Guia.objects.count()

    assert qtd_guias_canceladas == qtd_total_guias
    assert solicitacao.todas_as_guias_canceladas
    assert solicitacao.cancelada
