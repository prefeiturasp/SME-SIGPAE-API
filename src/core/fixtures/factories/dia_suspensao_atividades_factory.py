from factory import SubFactory
from factory.django import DjangoModelFactory

from src.core.fixtures.factories.escola_factory import (
    TipoUnidadeEscolarFactory,
)
from src.core.models import DiaSuspensaoAtividades
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
)


class DiaSuspensaoAtividadesFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)
    tipo_unidade = SubFactory(TipoUnidadeEscolarFactory)

    class Meta:
        model = DiaSuspensaoAtividades
