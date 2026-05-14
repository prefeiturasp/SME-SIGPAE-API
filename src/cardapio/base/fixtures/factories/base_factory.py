"""Factories para os modelos base do modulo de cardapio.

Utiliza ``factory_boy`` para criar instancias de teste dos modelos de tipos de
alimentacao e de vinculos entre periodo escolar e tipo de unidade escolar.
"""

import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.cardapio.base.models import (
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.escola.fixtures.factories.escola_factory import (
    PeriodoEscolarFactory,
    TipoUnidadeEscolarFactory,
)

fake = Faker("pt_BR")


class TipoAlimentacaoFactory(DjangoModelFactory):
    """Factory para o modelo ``TipoAlimentacao``.

    Gera instancias com nome unico combinando uma sequencia numerica com um
    valor produzido pelo Faker.
    """

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = TipoAlimentacao


class VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory(
    DjangoModelFactory
):
    """Factory para o modelo ``VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar``.

    Cria automaticamente o tipo de unidade escolar e o periodo escolar via
    subfactories. Suporta adicionar tipos de alimentacao relacionados pelo
    parametro ``tipos_alimentacao``.
    """

    tipo_unidade_escolar = SubFactory(TipoUnidadeEscolarFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        """Adiciona os tipos de alimentacao ao vinculo apos a criacao.

        Args:
            create (bool): Indica se a instancia foi persistida no banco.
            extracted: Colecao de tipos de alimentacao a associar, ou
                ``None``.
            **kwargs: Argumentos adicionais ignorados pelo hook.
        """
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar
