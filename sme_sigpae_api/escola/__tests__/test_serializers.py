import pytest

from sme_sigpae_api.escola.api.serializers import DiaCalendarioSerializer

pytestmark = pytest.mark.django_db


def test_vinculo_instituto_serializer(vinculo_instituto_serializer):
    assert vinculo_instituto_serializer.data is not None


def test_escola_simplissima_serializer(escola_simplissima_serializer):
    assert escola_simplissima_serializer.data is not None


def test_escola_simplissima_contem_campos_esperados(
    escola_simplissima_serializer,
):  # noqa
    esperado = set(
        [
            "uuid",
            "nome",
            "codigo_eol",
            "codigo_codae",
            "diretoria_regional",
            "lote",
            "quantidade_alunos",
            "tipo_gestao",
            "tipo_unidade",
        ]
    )
    resultado = escola_simplissima_serializer.data.keys()
    assert esperado == resultado


def test_serialize_dia_calendario_com_periodo_escolar(dia_calendario_noturno):
    serializer = DiaCalendarioSerializer(dia_calendario_noturno)
    data = serializer.data

    assert "id" not in data
    assert "uuid" not in data
    assert data["dia"] == "15"
    assert data["escola"] == dia_calendario_noturno.escola.nome
    assert data["dia_letivo"] is False
    assert isinstance(data["periodo_escolar"], dict)
    assert data["periodo_escolar"]["uuid"]
    assert (
        data["periodo_escolar"]["nome"] == dia_calendario_noturno.periodo_escolar.nome
    )


def test_serialize_dia_calendario_sem_periodo_escolar(dia_calendario_diurno):
    serializer = DiaCalendarioSerializer(dia_calendario_diurno)
    data = serializer.data

    assert "id" not in data
    assert "uuid" not in data
    assert data["dia"] == "15"
    assert data["escola"] == dia_calendario_diurno.escola.nome
    assert data["dia_letivo"] is True
    assert data["periodo_escolar"] is None
