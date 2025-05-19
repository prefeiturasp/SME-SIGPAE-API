from factory import SubFactory
from factory.django import DjangoModelFactory

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.escola.models import DiaSuspensaoAtividades
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
)


class DiaSuspensaoAtividadesFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)
    tipo_unidade = SubFactory(TipoUnidadeEscolarFactory)

    class Meta:
        model = DiaSuspensaoAtividades
