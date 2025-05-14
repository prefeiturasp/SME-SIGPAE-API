import datetime

import pytest

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 5),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 2),
            datetime.date(2019, 10, 6),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 3),
            datetime.date(2019, 10, 7),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 10, 5),
            datetime.date(2019, 10, 1),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 6),
            datetime.date(2019, 10, 2),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 7),
            datetime.date(2019, 10, 3),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_vencida(request):
    return request.param


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        ((2019, 10, 4), (2019, 10, 30), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 5), (2019, 10, 12), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 6), (2019, 10, 13), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (
            (2019, 10, 7),
            (2019, 10, 14),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        ((2019, 10, 28), (2019, 10, 7), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 29), (2019, 10, 8), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (
            (2019, 10, 30),
            (2019, 10, 9),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            (2019, 10, 30),
            (2019, 10, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_desta_semana(request):
    return request.param


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        (
            datetime.date(2019, 10, 29),
            datetime.date(2019, 11, 1),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 15),
            datetime.date(2019, 10, 31),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 10),
            datetime.date(2019, 10, 29),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 28),
            datetime.date(2019, 11, 3),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 10, 10),
            datetime.date(2019, 10, 15),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 15),
            datetime.date(2019, 10, 10),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 4),
            datetime.date(2019, 11, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 11, 4),
            datetime.date(2019, 10, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_deste_mes(request):
    return request.param
