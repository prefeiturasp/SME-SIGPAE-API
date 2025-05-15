import datetime

import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.serializers import (
    InversaoCardapioSerializer,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import TemplateMensagem


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


@pytest.fixture(
    params=[
        (
            datetime.date(2019, 8, 10),
            datetime.date(2019, 10, 24),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
        (
            datetime.date(2019, 1, 1),
            datetime.date(2019, 3, 3),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
        (
            datetime.date(2019, 1, 1),
            datetime.date(2019, 3, 4),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
    ]
)
def datas_de_inversoes_intervalo_maior_60_dias(request):
    return request.param


@pytest.fixture(
    params=[
        (datetime.date(2019, 8, 10), datetime.date(2019, 10, 9), True),
        (datetime.date(2019, 1, 1), datetime.date(2019, 3, 1), True),
        (datetime.date(2019, 1, 1), datetime.date(2019, 3, 2), True),
    ]
)
def datas_de_inversoes_intervalo_entre_60_dias(request):
    return request.param


@pytest.fixture
def template_mensagem_inversao_cardapio():
    return mommy.make(
        TemplateMensagem,
        tipo=TemplateMensagem.INVERSAO_CARDAPIO,
        assunto="TESTE INVERSAO CARDAPIO",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def inversao_dia_cardapio(
    cardapio_valido2, cardapio_valido3, template_mensagem_inversao_cardapio, escola
):
    return mommy.make(
        InversaoCardapio,
        criado_em=datetime.date(2019, 12, 12),
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )


@pytest.fixture
def inversao_dia_cardapio_outra_dre(
    cardapio_valido2,
    cardapio_valido3,
    template_mensagem_inversao_cardapio,
    escola_dre_guaianases,
):
    return mommy.make(
        InversaoCardapio,
        criado_em=datetime.date(2019, 12, 12),
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        escola=escola_dre_guaianases,
        rastro_escola=escola_dre_guaianases,
        rastro_dre=escola_dre_guaianases.diretoria_regional,
    )


@pytest.fixture
def inversao_dia_cardapio_dre_validar(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_codae_questionado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_dre_validado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_codae_autorizado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio2(cardapio_valido, cardapio_valido2, escola):
    mommy.make(
        TemplateMensagem,
        assunto="TESTE INVERSAO CARDAPIO",
        tipo=TemplateMensagem.INVERSAO_CARDAPIO,
        template_html="@id @criado_em @status @link",
    )
    return mommy.make(
        InversaoCardapio,
        uuid="98dc7cb7-7a38-408d-907c-c0f073ca2d13",
        cardapio_de=cardapio_valido,
        cardapio_para=cardapio_valido2,
        escola=escola,
    )


@pytest.fixture
def inversao_cardapio_serializer(escola):
    cardapio_de = mommy.make("cardapio.Cardapio")
    cardapio_para = mommy.make("cardapio.Cardapio")
    inversao_cardapio = mommy.make(
        InversaoCardapio,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        escola=escola,
    )
    return InversaoCardapioSerializer(inversao_cardapio)


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de create, data para create, data de update, data para update
        (
            datetime.date(2019, 10, 25),
            datetime.date(2019, 11, 25),
            datetime.date(2019, 11, 24),
            datetime.date(2019, 11, 28),
        ),
        (
            datetime.date(2019, 10, 26),
            datetime.date(2019, 12, 24),
            datetime.date(2019, 10, 20),
            datetime.date(2019, 11, 24),
        ),
        (
            datetime.date(2019, 12, 25),
            datetime.date(2019, 12, 30),
            datetime.date(2019, 12, 15),
            datetime.date(2019, 12, 31),
        ),
    ]
)
def inversao_card_params(request):
    return request.param
