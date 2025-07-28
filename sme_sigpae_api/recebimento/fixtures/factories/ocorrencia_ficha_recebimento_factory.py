from factory import LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
)
from sme_sigpae_api.recebimento.models import OcorrenciaFichaRecebimento

fake = Faker("pt_BR")


class OcorrenciaFichaRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = OcorrenciaFichaRecebimento

    ficha_recebimento = SubFactory(FichaDeRecebimentoFactory)
    tipo = LazyFunction(
        lambda: fake.random.choice(
            [tipo[0] for tipo in OcorrenciaFichaRecebimento.TIPO_CHOICES]
        )
    )
    relacao = LazyFunction(
        lambda: fake.random.choice(
            [relacao[0] for relacao in OcorrenciaFichaRecebimento.RELACAO_CHOICES]
        )
    )
    quantidade = LazyFunction(
        lambda: f"{fake.random_int(min=1, max=100)} {fake.random_element(('unidades', 'caixas', 'pacotes'))}"
    )
    descricao = LazyFunction(lambda: fake.paragraph(nb_sentences=3))
    numero_nota = LazyFunction(
        lambda: (
            str(fake.random_number(digits=44))
            if fake.boolean(chance_of_getting_true=70)
            else None
        )
    )
