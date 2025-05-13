import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow

pytestmark = pytest.mark.django_db


def test_label_tipos_alimentacao_retona_dois_tipos_alimentacao(label_tipos_alimentacao):
    modelo, tipo_vegetariano, tipo_vegano = label_tipos_alimentacao
    modelo.tipos_alimentacao.add(tipo_vegetariano, tipo_vegano)
    assert modelo.label == "Vegetariano e Vegano"


def test_label_property_retona_um_tipo_alimentacao(label_tipos_alimentacao):
    modelo, tipo_vegetariano, _ = label_tipos_alimentacao
    modelo.tipos_alimentacao.add(tipo_vegetariano)
    assert modelo.label == "Vegetariano"


def test_label_property_retona_nenhum_tipo(label_tipos_alimentacao):
    modelo, _, _ = label_tipos_alimentacao
    assert modelo.label == ""


def test_get_rascunhos_do_usuario():
    usuario = mommy.make("Usuario")
    alteracao_cardapio = mommy.make(
        "AlteracaoCardapio",
        criado_por=usuario,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )

    rascunhos = AlteracaoCardapio.get_rascunhos_do_usuario(usuario)
    assert alteracao_cardapio.__str__() == rascunhos[0].__str__()
