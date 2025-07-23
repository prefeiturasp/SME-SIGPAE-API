import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow

pytestmark = pytest.mark.django_db


def test_get_rascunhos_do_usuario():
    usuario = baker.make("Usuario")
    alteracao_cardapio = baker.make(
        "AlteracaoCardapio",
        criado_por=usuario,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )

    rascunhos = AlteracaoCardapio.get_rascunhos_do_usuario(usuario)
    assert alteracao_cardapio.__str__() == rascunhos[0].__str__()
