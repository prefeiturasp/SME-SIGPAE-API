"""Factory de tipo de embalagem (qualidade) para testes."""

from factory.django import DjangoModelFactory
from faker import Faker

from ...models import TipoEmbalagemQld

fake = Faker("pt_BR")


class TipoEmbalagemQldFactory(DjangoModelFactory):
    """Cria um ``TipoEmbalagemQld`` com valores padrão."""

    class Meta:
        model = TipoEmbalagemQld
