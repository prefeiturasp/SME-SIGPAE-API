import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 1), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 2), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 3), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 9, 30), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 9, 29), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 9, 28), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
    ]
)
def datas_alteracao_vencida(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 4), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 5), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 6), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 10, 7), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 8), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 9), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
    ]
)
def datas_alteracao_semana(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 4), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 10), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 15), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 10, 20), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 30), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 11, 4), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
    ]
)
def datas_alteracao_mes(request):
    return request.param


@pytest.fixture
def substituicoes_alimentacao_periodo(escola):
    alteracao_cardapio = mommy.make(
        AlteracaoCardapio, escola=escola, observacao="teste"
    )
    return mommy.make(
        SubstituicaoAlimentacaoNoPeriodoEscolar,
        uuid="59beb0ca-982a-49da-98b8-10a296f274ba",
        alteracao_cardapio=alteracao_cardapio,
    )
