from uuid import UUID

import pytest

from sme_pratoaberto_terceirizadas.escola.models import PeriodoEscolar, Escola
from ..models import MotivoInclusaoContinua

pytestmark = pytest.mark.django_db


def test_motivo_inclusao_continua(motivo_inclusao_continua):
    assert isinstance(motivo_inclusao_continua.nome, str)
    assert isinstance(motivo_inclusao_continua.uuid, UUID)


def test_motivo_inclusao_normal(motivo_inclusao_normal):
    assert isinstance(motivo_inclusao_normal.nome, str)
    assert isinstance(motivo_inclusao_normal.uuid, UUID)


def test_quantidade_por_periodo(quantidade_por_periodo):
    assert isinstance(quantidade_por_periodo.numero_alunos, int)
    assert isinstance(quantidade_por_periodo.periodo_escolar, PeriodoEscolar)
    assert quantidade_por_periodo.tipos_alimentacao.all().count() == 5


def test_inclusao_alimentacao_continua(inclusao_alimentacao_continua):
    assert isinstance(inclusao_alimentacao_continua.escola, Escola)
    assert isinstance(inclusao_alimentacao_continua.motivo, MotivoInclusaoContinua)
