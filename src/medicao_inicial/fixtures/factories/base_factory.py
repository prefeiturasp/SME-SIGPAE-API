from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.escola.fixtures.factories.escola_factory import EscolaFactory
from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    LancheEmergencialDiario,
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


class LancheEmergencialDiarioFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)

    class Meta:
        model = LancheEmergencialDiario
