import pytest

pytestmark = pytest.mark.django_db


def test_lote(lote):
    assert isinstance(str(lote), str)
    assert lote.escolas is not None
