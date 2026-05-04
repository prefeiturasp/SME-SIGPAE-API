import pytest
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.imr.api.serializers.serializers_create import (
    FormularioDiretorCreateSerializer,
    FormularioDiretorManyCreateSerializer,
    FormularioSupervisaoRascunhoCreateSerializer,
)

pytestmark = pytest.mark.django_db


def test_formulario_diretor_data_is_valid(solicitacao_medicao_inicial_factory):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create()
    data = {
        "data": "2024-05-31",
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "ocorrencias": [],
    }
    serializer = FormularioDiretorCreateSerializer(data=data)
    assert serializer.is_valid()


def test_formulario_diretor_sem_data(solicitacao_medicao_inicial_factory):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create()
    data = {
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "ocorrencias": [],
    }
    serializer = FormularioDiretorCreateSerializer(data=data)
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


def test_formulario_diretor_create(
    client_autenticado_diretor_escola, solicitacao_medicao_inicial_factory
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create()
    data = {
        "data": "31/05/2024",
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "ocorrencias": [],
    }
    context = {
        "request": type(
            "Request", (), {"user": client_autenticado_diretor_escola["user"]}
        )
    }
    serializer = FormularioDiretorCreateSerializer(data=data, context=context)
    assert serializer.is_valid()
    form_diretor = serializer.save()
    assert form_diretor.solicitacao_medicao_inicial == solicitacao_medicao_inicial


def test_formulario_diretor_many_create(
    client_autenticado_diretor_escola, solicitacao_medicao_inicial_factory
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory.create()
    data = {
        "datas": ["31/05/2024", "01/06/2024"],
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "ocorrencias": [],
    }
    context = {
        "request": type(
            "Request", (), {"user": client_autenticado_diretor_escola["user"]}
        )
    }
    serializer = FormularioDiretorManyCreateSerializer(data=data, context=context)
    assert serializer.is_valid()
    form_diretor = serializer.save()
    assert form_diretor is not None


def test_serializer_nutri_sem_serializer_class_erro():
    with pytest.raises(
        ValueError,
        match="Nenhum serializer encontrado com o nome 'ModeloNaoExiste'",
    ):
        serializer = FormularioSupervisaoRascunhoCreateSerializer()
        serializer.get_serializer_class_by_name("ModeloNaoExiste")


def test_serializer_nutri_validate_erro():
    with pytest.raises(
        ValidationError,
        match="Este campo é obrigatório!",
    ):
        data = {}
        serializer = FormularioSupervisaoRascunhoCreateSerializer()
        serializer.validate(data)


def test_serializer_diretor_sem_serializer_class_erro():
    with pytest.raises(
        ValueError,
        match="Nenhum serializer encontrado com o nome 'ModeloNaoExiste'",
    ):
        serializer = FormularioDiretorCreateSerializer()
        serializer.get_serializer_class_by_name("ModeloNaoExiste")


def test_serializer_diretor_validate_erro():
    with pytest.raises(
        ValidationError,
        match="Este campo é obrigatório!",
    ):
        data = {}
        serializer = FormularioDiretorCreateSerializer()
        serializer.validate(data)
