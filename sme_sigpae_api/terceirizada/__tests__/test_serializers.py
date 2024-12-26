import pytest

pytestmark = pytest.mark.django_db


def test_vigencia_contrato_serializer(vigencia_contrato_serializer):
    assert vigencia_contrato_serializer.data is not None
    assert "uuid" in vigencia_contrato_serializer.data
    assert "data_inicial" in vigencia_contrato_serializer.data
    assert "data_final" in vigencia_contrato_serializer.data


def test_contrato_serializer(contrato_serializer):
    assert contrato_serializer.data is not None
    assert "uuid" in contrato_serializer.data
    assert "numero" in contrato_serializer.data
    assert "processo" in contrato_serializer.data
    assert "data_proposta" in contrato_serializer.data
    assert "lotes" in contrato_serializer.data
    assert "terceirizada" in contrato_serializer.data
    assert "edital" in contrato_serializer.data
    assert "vigencias" in contrato_serializer.data


def test_edital_contratos_serializer(edital_contratos_serializer):
    assert edital_contratos_serializer.data is not None
    assert "uuid" in edital_contratos_serializer.data
    assert "numero" in edital_contratos_serializer.data
    assert "tipo_contratacao" in edital_contratos_serializer.data
    assert "processo" in edital_contratos_serializer.data
    assert "objeto" in edital_contratos_serializer.data
    assert "contratos" in edital_contratos_serializer.data


def test_edital_serializer(edital_serializer):
    assert edital_serializer.data is not None
    assert "uuid" in edital_serializer.data
    assert "numero" in edital_serializer.data
    assert "tipo_contratacao" in edital_serializer.data
    assert "processo" in edital_serializer.data
    assert "objeto" in edital_serializer.data


def test_edital_simples_serializer(edital_simples_serializer):
    assert edital_simples_serializer.data is not None
    assert "uuid" in edital_simples_serializer.data
    assert "numero" in edital_simples_serializer.data


def test_emails_terceiradas_modulos(email_terceirizada_por_modulo_serializer):
    assert email_terceirizada_por_modulo_serializer.data is not None
    assert "uuid" in email_terceirizada_por_modulo_serializer.data
    assert "email" in email_terceirizada_por_modulo_serializer.data


def test_modalidade_serializer(modalidade_serializer):
    assert modalidade_serializer.data is not None
    assert "uuid" in modalidade_serializer.data
    assert "nome" in modalidade_serializer.data
