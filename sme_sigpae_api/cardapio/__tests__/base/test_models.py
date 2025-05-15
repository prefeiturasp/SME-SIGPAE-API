import pytest

pytestmark = pytest.mark.django_db


def test_tipo_alimentacao(tipo_alimentacao):
    assert tipo_alimentacao.__str__() == "Refeição"


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
