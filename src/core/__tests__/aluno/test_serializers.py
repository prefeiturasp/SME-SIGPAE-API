from unittest.mock import patch

import pytest

from src.core.aluno.api.serializers import AlunoSerializer
from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR

pytestmark = pytest.mark.django_db


def test_aluno_serializer_exibe_periodo(aluno):
    aluno.nao_matriculado = False
    aluno.escola.tipo_unidade.iniciais = TIPOS_UNIDADE_ESCOLAR.EMEF.value

    with patch.object(
        AlunoSerializer,
        "get_possui_dieta_especial",
        return_value=False,
    ):
        serializer = AlunoSerializer(aluno)
        data = serializer.data

    assert "periodo" in data
    assert data["periodo"] == aluno.periodo_escolar.nome
