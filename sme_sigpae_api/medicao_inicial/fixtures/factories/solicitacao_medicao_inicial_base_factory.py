from random import randint

import factory
from factory import SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.escola.fixtures.factories.escola_factory import EscolaFactory
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial

fake = Faker("pt_BR")


class SolicitacaoMedicaoInicialFactory(DjangoModelFactory):
    mes = "%02d" % randint(1, 12)
    ano = str(randint(2023, 2024))
    escola = SubFactory(EscolaFactory)

    @factory.post_generation
    def tipos_contagem_alimentacao(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tipos_contagem_alimentacao.add(*extracted)

    class Meta:
        model = SolicitacaoMedicaoInicial
