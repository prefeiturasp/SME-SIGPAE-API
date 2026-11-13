import pytest

pytestmark = pytest.mark.django_db


def test_vinculo_instituto_serializer(vinculo_instituto_serializer):
    assert vinculo_instituto_serializer.data is not None
