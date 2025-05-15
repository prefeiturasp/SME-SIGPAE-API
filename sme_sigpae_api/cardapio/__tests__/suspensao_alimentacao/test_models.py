import pytest

pytestmark = pytest.mark.django_db


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


def test_grupo_suspensao_alimentacao(grupo_suspensao_alimentacao):
    assert grupo_suspensao_alimentacao.__str__() == "lorem ipsum"


def test_existe_dia_cancelado_sem_cancelamento(grupo_suspensao_alimentacao):
    assert grupo_suspensao_alimentacao.existe_dia_cancelado == False


def test_existe_dia_cancelado_com_cancelamento(
    grupo_suspensao_alimentacao_escola_cancelou,
):
    assert grupo_suspensao_alimentacao_escola_cancelou.existe_dia_cancelado == True
