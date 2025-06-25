from factory import Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    TipoContagemAlimentacao,
)

fake = Faker("pt_BR")


class TipoContagemAlimentacaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Periodo {n} - {fake.word()}")

    class Meta:
        model = TipoContagemAlimentacao


class GrupoMedicaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Periodo {n} - {fake.word()}")

    class Meta:
        model = GrupoMedicao


class CategoriaMedicaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Periodo {n} - {fake.word()}")

    class Meta:
        model = CategoriaMedicao
