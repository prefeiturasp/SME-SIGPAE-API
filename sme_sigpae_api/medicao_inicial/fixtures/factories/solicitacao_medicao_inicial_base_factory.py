from random import randint

import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.base_factory import (
    CategoriaMedicaoFactory,
    GrupoMedicaoFactory,
)
from sme_sigpae_api.medicao_inicial.models import (
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)

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


class MedicaoFactory(DjangoModelFactory):
    solicitacao_medicao_inicial = SubFactory(SolicitacaoMedicaoInicialFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    grupo = SubFactory(GrupoMedicaoFactory)

    class Meta:
        model = Medicao


class ValorMedicaoFactory(DjangoModelFactory):
    valor = str(randint(1, 100))
    nome_campo = Sequence(lambda n: f"{fake.unique.word()}")
    medicao = SubFactory(MedicaoFactory)
    categoria_medicao = SubFactory(CategoriaMedicaoFactory)
    tipo_alimentacao = SubFactory(TipoAlimentacaoFactory)
    faixa_etaria = SubFactory(FaixaEtariaFactory)

    class Meta:
        model = ValorMedicao
