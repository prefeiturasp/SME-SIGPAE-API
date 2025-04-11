import pytest

from sme_sigpae_api.recebimento.api.serializers.serializers import (
    QuestaoFichaRecebimentoSerializer,
    QuestoesPorProdutoDetalheSerializer,
)
from sme_sigpae_api.recebimento.models import QuestaoFichaRecebimento

pytestmark = pytest.mark.django_db


def test_questoes_por_produto_detalhe_serializer(questoes_por_produto):
    serializer = QuestoesPorProdutoDetalheSerializer(instance=questoes_por_produto)
    data = serializer.data

    assert "questoes_primarias" in data
    assert isinstance(data["questoes_primarias"], list)
    assert len(data["questoes_primarias"]) == 1
    assert "uuid" in data["questoes_primarias"][0]
    assert isinstance(data["questoes_primarias"][0]["uuid"], str)
    assert "questao" in data["questoes_primarias"][0]
    assert isinstance(data["questoes_primarias"][0]["questao"], str)

    assert "questoes_secundarias" in data
    assert isinstance(data["questoes_secundarias"], list)
    assert len(data["questoes_secundarias"]) == 1
    assert "uuid" in data["questoes_secundarias"][0]
    assert isinstance(data["questoes_secundarias"][0]["uuid"], str)
    assert "questao" in data["questoes_secundarias"][0]
    assert isinstance(data["questoes_secundarias"][0]["questao"], str)


def test_questao_ficha_recebimentos_serializer(questao_ficha_recebimento):
    serializer = QuestaoFichaRecebimentoSerializer(instance=questao_ficha_recebimento)
    data = serializer.data

    assert "id" not in data
    assert "uuid" in data
    assert isinstance(data["uuid"], str)
    assert "criado_em" in data
    assert isinstance(data["criado_em"], str)
    assert "alterado_em" in data
    assert isinstance(data["alterado_em"], str)
    assert "ficha_recebimento" in data
    assert isinstance(data["ficha_recebimento"], int)
    assert "questao_conferencia" in data
    assert isinstance(data["questao_conferencia"], int)
    assert "resposta" in data
    assert isinstance(data["resposta"], bool)
    assert "tipo_questao" in data
    assert isinstance(data["tipo_questao"], str)
    assert data["tipo_questao"] in [
        QuestaoFichaRecebimento.TIPO_QUESTAO_PRIMARIA,
        QuestaoFichaRecebimento.TIPO_QUESTAO_SECUNDARIA,
    ]
