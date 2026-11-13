import pytest

pytestmark = pytest.mark.django_db


def test_sub_prefeitura(sub_prefeitura):
    assert isinstance(str(sub_prefeitura), str)
