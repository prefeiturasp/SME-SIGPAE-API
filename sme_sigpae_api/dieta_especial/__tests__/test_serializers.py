import pytest

from sme_sigpae_api.dieta_especial.api.serializers import (
    SolicitacaoDietaEspecialRecreioNasFeriasSerializer,
)

pytestmark = pytest.mark.django_db


def test_unidade_educacional_serializer(unidade_educacional):
    assert unidade_educacional.data is not None
    assert "lote" in unidade_educacional.data
    assert "unidade_educacional" in unidade_educacional.data
    assert "tipo_unidade" in unidade_educacional.data
    assert "classificacao" in unidade_educacional.data
    assert "total" in unidade_educacional.data
    assert "data" in unidade_educacional.data
    assert "periodos" in unidade_educacional.data


def test_solicitacao_recrei_nas_ferias_serializer(
    solicitacao_dieta_especial_aprovada_alteracao_ue,
):
    solicitacao = SolicitacaoDietaEspecialRecreioNasFeriasSerializer(
        solicitacao_dieta_especial_aprovada_alteracao_ue
    )
    data = solicitacao.data
    assert data is not None
    assert "id" in data
    assert "uuid" in data
    assert "status_solicitacao" in data
    assert "data_inicio" in data
    assert "data_termino" in data
    assert "tipo_solicitacao" in data
    assert "aluno" in data
    assert "escola" in data
    assert "escola_destino" in data
    assert "alergias_intolerancias" in data
    assert "classificacao" in data
    assert "dieta_alterada" in data
