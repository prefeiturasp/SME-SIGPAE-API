import pytest

from src.dieta_especial.logs_models.models import (
    LogDietasAtivasCanceladasAutomaticamente,
)

pytestmark = pytest.mark.django_db


def test_instance_model(log_dietas_ativas_canceladas_automaticamente):
    model = log_dietas_ativas_canceladas_automaticamente
    assert isinstance(model, LogDietasAtivasCanceladasAutomaticamente)
    assert model.dieta
    assert model.codigo_eol_aluno
    assert model.nome_aluno
    assert model.codigo_eol_escola_origem
    assert model.nome_escola_origem
    assert model.codigo_eol_escola_destino
    assert model.nome_escola_destino
