from factory import Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from ...models import (
    Laboratorio,
)


fake = Faker("pt_BR")


class LaboratorioFactory(DjangoModelFactory):
    class Meta:
        model = Laboratorio

    nome = Sequence(lambda n: f"Laboratorio {n}")
    cnpj = Sequence(lambda n: str(n).zfill(14))
