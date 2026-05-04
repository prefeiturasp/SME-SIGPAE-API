import factory
from factory.django import DjangoModelFactory
from faker import Faker

from src.imr.models import (
    ImportacaoPlanilhaTipoOcorrencia,
    ImportacaoPlanilhaTipoPenalidade,
)

fake = Faker("pt_BR")


class ImportacaoPlanilhaTipoPenalidadeFactory(DjangoModelFactory):
    conteudo = factory.django.FileField()

    class Meta:
        model = ImportacaoPlanilhaTipoPenalidade


class ImportacaoPlanilhaTipoOcorrenciaFactory(DjangoModelFactory):
    conteudo = factory.django.FileField()

    class Meta:
        model = ImportacaoPlanilhaTipoOcorrencia
