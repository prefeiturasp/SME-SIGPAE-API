import uuid

import pytest

from sme_sigpae_api.recebimento.api.serializers.serializers_create import (
    FichaDeRecebimentoRascunhoSerializer,
    QuestaoFichaRecebimentoCreateSerializer,
)
from sme_sigpae_api.recebimento.models import QuestaoFichaRecebimento

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
