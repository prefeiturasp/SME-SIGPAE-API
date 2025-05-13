import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.cardapio.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class MotivoAlteracaoCardapioFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = MotivoAlteracaoCardapio


class AlteracaoCardapioFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    motivo = SubFactory(MotivoAlteracaoCardapioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = AlteracaoCardapio


class DataIntervaloAlteracaoCardapioFactory(DjangoModelFactory):
    alteracao_cardapio = SubFactory(AlteracaoCardapioFactory)

    class Meta:
        model = DataIntervaloAlteracaoCardapio


class SubstituicaoAlimentacaoNoPeriodoEscolarFactory(DjangoModelFactory):
    alteracao_cardapio = SubFactory(AlteracaoCardapioFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
