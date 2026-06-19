import datetime

import pytest
from model_bakery import baker

from src.escola.dias_letivos.models import DiaLetivoSIGPAE

pytestmark = pytest.mark.django_db


def test_dia_letivo_str():
    dia = baker.prepare(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    assert str(dia) == "Dia 2026-06-22 letivo no SIGPAE"
