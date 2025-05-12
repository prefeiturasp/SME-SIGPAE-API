import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.cardapio.models import (
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)

fake = Faker("pt_BR")


class TipoAlimentacaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = TipoAlimentacao


class VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory(
    DjangoModelFactory
):
    tipo_unidade_escolar = SubFactory(TipoUnidadeEscolarFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
