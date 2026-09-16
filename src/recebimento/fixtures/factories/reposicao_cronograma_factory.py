"""Factory de reposição de cronograma da ficha para testes."""

from factory.django import DjangoModelFactory
from faker import Faker

from src.recebimento.models import ReposicaoCronogramaFichaRecebimento

fake = Faker("pt_BR")


class ReposicaoCronogramaFichaRecebimentoFactory(DjangoModelFactory):
    """Cria um ``ReposicaoCronogramaFichaRecebimento`` com valores padrão."""

    class Meta:
        model = ReposicaoCronogramaFichaRecebimento
