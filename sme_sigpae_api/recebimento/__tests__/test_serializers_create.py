import uuid

import pytest
from model_bakery import baker

from sme_sigpae_api.conftest import (
    client_autenticado_qualidade,
)
from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.recebimento.api.serializers.serializers_create import (
    FichaDeRecebimentoCreateSerializer,
    FichaDeRecebimentoRascunhoSerializer,
    OcorrenciaFichaRecebimentoCreateSerializer,
    QuestaoFichaRecebimentoCreateSerializer,
)
from sme_sigpae_api.recebimento.models import (
    QuestaoConferencia,
    QuestaoFichaRecebimento,
)

pytestmark = pytest.mark.django_db


def test_questao_ficha_recebimento_create_serializer(questao_ficha_recebimento):
    serializer = QuestaoFichaRecebimentoCreateSerializer(
        instance=questao_ficha_recebimento
    )
    data = serializer.data

    assert "id" not in data
    assert "ficha_recebimento" not in data
    assert "uuid" in data
    assert isinstance(data["uuid"], str)
    assert "criado_em" in data
    assert isinstance(data["criado_em"], str)
    assert "alterado_em" in data
    assert isinstance(data["alterado_em"], str)
    assert "questao_conferencia" in data
    assert isinstance(data["questao_conferencia"], uuid.UUID)
    assert "resposta" in data
    assert isinstance(data["resposta"], bool)
    assert "tipo_questao" in data
    assert isinstance(data["tipo_questao"], str)
    assert data["tipo_questao"] in [
        QuestaoFichaRecebimento.TIPO_QUESTAO_PRIMARIA,
        QuestaoFichaRecebimento.TIPO_QUESTAO_SECUNDARIA,
    ]


def test_ficha_recebimento_rascunho_serializer(
    ficha_recebimento_rascunho, etapa_cronograma
):
    serializer = FichaDeRecebimentoRascunhoSerializer(data=ficha_recebimento_rascunho)
    assert serializer.is_valid()

    instancia = serializer.save()
    assert instancia.etapa == etapa_cronograma
    assert instancia.documentos_recebimento.count() == 1
    assert instancia.questoes_conferencia.count() == 1
    assert instancia.veiculos.count() == 1
    assert (
        instancia.ocorrencias.count() == 2
    )  # Verifica se as ocorrências foram criadas


def test_ficha_recebimento_rascunho_serializer_erro_sem_etapa(
    ficha_recebimento_rascunho,
):
    ficha_recebimento_rascunho.pop("etapa")
    serializer = FichaDeRecebimentoRascunhoSerializer(data=ficha_recebimento_rascunho)
    assert serializer.is_valid() is False
    assert serializer.errors == {"etapa": ["Este campo é obrigatório."]}


def test_ficha_recebimento_rascunho_serializer_erro_etapa_invalida(
    ficha_recebimento_rascunho,
):
    ficha_recebimento_rascunho["etapa"] += "Aa"
    serializer = FichaDeRecebimentoRascunhoSerializer(data=ficha_recebimento_rascunho)
    assert serializer.is_valid() is False
    assert serializer.errors == {
        "etapa": [
            f'O valor “{ficha_recebimento_rascunho["etapa"]}” não é um UUID válido'
        ]
    }


def test_ocorrencia_serializer_valid_data(ocorrencia_ficha_recebimento_data):
    """Testa o serializer com dados válidos."""
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(
        data=ocorrencia_ficha_recebimento_data
    )
    assert serializer.is_valid() is True


def test_ocorrencia_serializer_missing_required_fields():
    """Testa o serializer com campos obrigatórios ausentes."""
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data={})
    assert serializer.is_valid() is False
    assert "tipo" in serializer.errors


def test_ocorrencia_serializer_tipo_falta_validation(ocorrencia_ficha_recebimento_data):
    """Testa a validação para o tipo FALTA."""
    data = ocorrencia_ficha_recebimento_data.copy()
    data.update({"tipo": "FALTA", "relacao": "CRONOGRAMA", "quantidade": "5 unidades"})
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is True

    # Teste sem quantidade para FALTA
    data["quantidade"] = ""
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is False
    assert "quantidade" in serializer.errors


def test_ocorrencia_serializer_tipo_recusa_validation(
    ocorrencia_ficha_recebimento_data,
):
    """Testa a validação para o tipo RECUSA."""
    data = ocorrencia_ficha_recebimento_data.copy()
    data.update(
        {
            "tipo": "RECUSA",
            "relacao": "TOTAL",
            "numero_nota": "NF12345",
            "quantidade": "10 unidades",
        }
    )
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is True

    # Teste sem numero_nota para RECUSA
    data.pop("numero_nota")
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is False
    assert "numero_nota" in serializer.errors


def test_ocorrencia_serializer_tipo_outros_motivos(ocorrencia_ficha_recebimento_data):
    """Testa a validação para o tipo OUTROS_MOTIVOS."""
    data = ocorrencia_ficha_recebimento_data.copy()
    data.update({"tipo": "OUTROS_MOTIVOS", "quantidade": ""})  # Deve ser opcional
    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is True


def test_ocorrencia_serializer_create(
    ocorrencia_ficha_recebimento_data, ficha_recebimento
):
    """Testa a criação de uma instância através do serializer."""
    # Cria uma cópia dos dados para não modificar o fixture original
    data = ocorrencia_ficha_recebimento_data.copy()
    data["ficha_recebimento"] = ficha_recebimento.id

    serializer = OcorrenciaFichaRecebimentoCreateSerializer(data=data)
    assert serializer.is_valid() is True, serializer.errors
    instance = serializer.save(ficha_recebimento=ficha_recebimento)
    assert instance.tipo == data["tipo"]
    assert instance.descricao == data["descricao"]
    assert instance.ficha_recebimento == ficha_recebimento


def test_ficha_recebimento_serializer_create(payload_ficha_recebimento):
    """Testa a criação de uma ficha através do serializer."""

    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    context = {"request": FakeObject()}
    serializer = FichaDeRecebimentoCreateSerializer(
        data=payload_ficha_recebimento, context=context
    )
    is_valid = serializer.is_valid()
    if not is_valid:
        print("\nErros de validação:", serializer.errors)
    assert is_valid, f"O serializer não é válido. Erros: {serializer.errors}"

    ficha = serializer.save()
    assert ficha.id is not None
    assert ficha.veiculos.count() > 0
    assert ficha.arquivos.count() > 0
    assert ficha.questoes_conferencia.count() > 0


def test_ficha_recebimento_serializer_update(
    ficha_recebimento, payload_ficha_recebimento
):
    """Testa a atualização de uma ficha existente através do serializer."""
    payload_ficha_recebimento["observacao"] = "Observação atualizada"

    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    context = {"request": FakeObject()}

    serializer = FichaDeRecebimentoCreateSerializer(
        instance=ficha_recebimento, data=payload_ficha_recebimento, context=context
    )
    is_valid = serializer.is_valid()
    if not is_valid:
        print("\nErros de validação:", serializer.errors)
    assert is_valid, f"O serializer não é válido. Erros: {serializer.errors}"

    ficha = serializer.save()
    assert ficha.observacao == "Observação atualizada"
    assert ficha.veiculos.count() > 0
    assert ficha.arquivos.count() > 0
    assert ficha.questoes_conferencia.count() > 0


def test_ficha_recebimento_serializer_validate_veiculos(payload_ficha_recebimento):
    """Testa a validação de veículos obrigatórios."""
    payload = payload_ficha_recebimento.copy()
    payload["veiculos"] = []  # Lista vazia deve falhar

    serializer = FichaDeRecebimentoCreateSerializer(data=payload)
    assert not serializer.is_valid()
    assert "veiculos" in serializer.errors


def test_ficha_recebimento_serializer_validate_questoes(
    payload_ficha_recebimento, questao_conferencia
):
    """Testa a validação de questões obrigatórias."""
    payload = payload_ficha_recebimento.copy()

    questoes_obrigatorias = set(
        str(q.uuid)
        for q in QuestaoConferencia.objects.filter(pergunta_obrigatoria=True)
    )

    payload["questoes"] = [
        q
        for q in payload["questoes"]
        if q["questao_conferencia"] not in questoes_obrigatorias
    ]

    serializer = FichaDeRecebimentoCreateSerializer(data=payload)
    assert not serializer.is_valid()
    assert "questoes" in serializer.errors
