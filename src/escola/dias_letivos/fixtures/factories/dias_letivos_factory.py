import datetime

import factory
from factory.django import DjangoModelFactory

from ...models import DiaLetivoSIGPAE


class DiaLetivoSIGPAEFactory(DjangoModelFactory):
    data = factory.LazyFunction(datetime.date.today)

    @factory.post_generation
    def lotes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.lotes.set(extracted)

    @factory.post_generation
    def tipos_unidade_escolar(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.tipos_unidade_escolar.set(extracted)

    @factory.post_generation
    def escolas(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.escolas.set(extracted)

    @factory.post_generation
    def periodos_escolares(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.periodos_escolares.set(extracted)

    class Meta:
        model = DiaLetivoSIGPAE
