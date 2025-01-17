import datetime

import pytest
from freezegun import freeze_time
from model_mommy import mommy
from xworkflows.base import InvalidTransitionError

from ...cardapio.models import Cardapio
from ...dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from ...escola.models import Escola

pytestmark = pytest.mark.django_db


def test_tipo_alimentacao(tipo_alimentacao):
    assert tipo_alimentacao.__str__() == "Refeição"


def test_motivo_alteracao_cardapio(motivo_alteracao_cardapio):
    assert motivo_alteracao_cardapio.nome is not None
    assert motivo_alteracao_cardapio.__str__() == "Aniversariantes do mês"


def test_motivo_suspensao_alimentacao(motivo_suspensao_alimentacao):
    assert motivo_suspensao_alimentacao.__str__() == "Não vai ter aula"


def test_quantidade_por_periodo_suspensao_alimentacao(
    quantidade_por_periodo_suspensao_alimentacao,
):
    assert (
        quantidade_por_periodo_suspensao_alimentacao.__str__()
        == "Quantidade de alunos: 100"
    )


def test_suspensao_alimentacao(suspensao_alimentacao):
    assert suspensao_alimentacao.__str__() == "Não vai ter aula"


def test_suspensao_alimentacao_no_periodo_escolar(suspensao_periodo_escolar):
    assert (
        suspensao_periodo_escolar.__str__()
        == "Suspensão de alimentação da Alteração de Cardápio: Não vai ter aula"
    )


def test_alteracao_cardapio(alteracao_cardapio):
    assert alteracao_cardapio.data_inicial is not None
    assert alteracao_cardapio.data_final is not None
    assert alteracao_cardapio.observacao == "teste"
    assert alteracao_cardapio.status is not None
    assert (
        alteracao_cardapio.__str__()
        == "Alteração de cardápio de: 2019-10-04 para 2019-12-31"
    )


def test_substituicoes_alimentacao_periodo(substituicoes_alimentacao_periodo):
    assert substituicoes_alimentacao_periodo.alteracao_cardapio is not None
    assert (
        substituicoes_alimentacao_periodo.alteracao_cardapio.substituicoes is not None
    )


def test_inversao_dia_cardapio(inversao_dia_cardapio):
    assert isinstance(inversao_dia_cardapio.escola, Escola)
    assert isinstance(inversao_dia_cardapio.cardapio_de, Cardapio)
    assert isinstance(inversao_dia_cardapio.cardapio_para, Cardapio)
    assunto, template_html = inversao_dia_cardapio.template_mensagem
    assert assunto == "TESTE INVERSAO CARDAPIO"
    assert "RASCUNHO" in template_html


@freeze_time("2019-12-12")
def test_inversao_dia_cardapio_fluxo_codae_em_cima_da_hora_error(inversao_dia_cardapio):
    # a data do evento é dia 15 de dez a solicitação foi pedida em 12 dez (ou seja em cima da hora)
    # e no mesmo dia 12 a codae tenta autorizar, ela nao deve ser capaz de autorizar, deve questionar
    user = mommy.make("Usuario")
    assert inversao_dia_cardapio.data == datetime.date(2019, 12, 15)
    assert inversao_dia_cardapio.prioridade == "PRIORITARIO"
    inversao_dia_cardapio.inicia_fluxo(user=user)
    inversao_dia_cardapio.dre_valida(user=user)
    assert inversao_dia_cardapio.foi_solicitado_fora_do_prazo is True
    assert inversao_dia_cardapio.status == "DRE_VALIDADO"
    with pytest.raises(
        InvalidTransitionError,
        match="CODAE não pode autorizar direto caso seja em cima da hora, deve questionar",
    ):
        inversao_dia_cardapio.codae_autoriza(user=user)


def test_inversao_dia_cardapio_fluxo(inversao_dia_cardapio):
    fake_user = mommy.make("perfil.Usuario")
    inversao_dia_cardapio.inicia_fluxo(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    inversao_dia_cardapio.dre_valida(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    )


@freeze_time("2012-01-14")
def test_inversao_dia_cardapio_fluxo_cancelamento(inversao_dia_cardapio):
    justificativa = "este e um cancelamento"
    fake_user = mommy.make("perfil.Usuario")
    inversao_dia_cardapio.inicia_fluxo(user=fake_user)
    assert (
        str(inversao_dia_cardapio.status) == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    )
    inversao_dia_cardapio.cancelar_pedido(user=fake_user, justificativa=justificativa)
    assert (
        str(inversao_dia_cardapio.status)
        == PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU
    )


def test_inversao_dia_cardapio_fluxo_cancelamento_erro(inversao_dia_cardapio2):
    justificativa = "este e um cancelamento"
    fake_user = mommy.make("perfil.Usuario")
    with pytest.raises(
        InvalidTransitionError,
        match=r".*Só pode cancelar com no mínimo 2 dia\(s\) úteis de antecedência.*",
    ):
        inversao_dia_cardapio2.inicia_fluxo(user=fake_user)
        inversao_dia_cardapio2.cancelar_pedido(
            user=fake_user, justificativa=justificativa
        )


def test_inclusao_alimentacao_continua_fluxo_erro(inversao_dia_cardapio):
    # TODO: pedir incremento do fluxo para testá-lo por completo
    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_pede_revisao' isn't available from state 'RASCUNHO'.",
    ):
        inversao_dia_cardapio.dre_pede_revisao()


def test_grupo_suspensao_alimentacao(grupo_suspensao_alimentacao):
    assert grupo_suspensao_alimentacao.__str__() == "lorem ipsum"


def test_vinculo_tipo_alimentacao(vinculo_tipo_alimentacao):
    assert vinculo_tipo_alimentacao.tipos_alimentacao.count() == 5


def test_horario_combo_tipo_alimentacao(horario_tipo_alimentacao):
    assert horario_tipo_alimentacao.hora_inicial == "07:00:00"
    assert horario_tipo_alimentacao.hora_final == "07:30:00"
    assert horario_tipo_alimentacao.escola.nome == "EMEF JOAO MENDES"
    assert (
        horario_tipo_alimentacao.tipo_alimentacao.uuid
        == "c42a24bb-14f8-4871-9ee8-05bc42cf3061"
    )
    assert (
        horario_tipo_alimentacao.periodo_escolar.uuid
        == "22596464-271e-448d-bcb3-adaba43fffc8"
    )
    assert horario_tipo_alimentacao.__str__() == (
        f"{horario_tipo_alimentacao.tipo_alimentacao.nome} "
        f"DE: {horario_tipo_alimentacao.hora_inicial} "
        f"ATE: {horario_tipo_alimentacao.hora_final}"
    )


def test_existe_dia_cancelado_sem_cancelamento(grupo_suspensao_alimentacao):
    assert grupo_suspensao_alimentacao.existe_dia_cancelado == False
