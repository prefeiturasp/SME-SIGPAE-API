from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    EscolaFactory,
    LoteFactory,
)
from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import (
    CategoriaAlimentacao,
    RecreioNasFerias,
    RecreioNasFeriasUnidadeParticipante,
    RecreioNasFeriasUnidadeTipoAlimentacao,
)

fake = Faker("pt_BR")


class RecreioNasFeriasFactory(DjangoModelFactory):
    titulo = Sequence(lambda n: f"Recreio nas Férias {n} - {fake.word()}")

    class Meta:
        model = RecreioNasFerias


class RecreioNasFeriasUnidadeParticipanteFactory(DjangoModelFactory):
    recreio_nas_ferias = SubFactory(RecreioNasFeriasFactory)
    lote = SubFactory(LoteFactory)
    unidade_educacional = SubFactory(EscolaFactory)

    class Meta:
        model = RecreioNasFeriasUnidadeParticipante


class CategoriaAlimentacaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"{fake.word()}")

    class Meta:
        model = CategoriaAlimentacao


class RecreioNasFeriasUnidadeTipoAlimentacaoFactory(DjangoModelFactory):
    recreio_ferias_unidade = SubFactory(RecreioNasFeriasUnidadeParticipanteFactory)
    tipo_alimentacao = SubFactory(TipoAlimentacaoFactory)
    categoria = SubFactory(CategoriaAlimentacaoFactory)

    class Meta:
        model = RecreioNasFeriasUnidadeTipoAlimentacao
