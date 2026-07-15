from factory.django import DjangoModelFactory
from faker import Faker

from src.recebimento.models import ReposicaoCronogramaFichaRecebimento

fake = Faker("pt_BR")


class ReposicaoCronogramaFichaRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = ReposicaoCronogramaFichaRecebimento
