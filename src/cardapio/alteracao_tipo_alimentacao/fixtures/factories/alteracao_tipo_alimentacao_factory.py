"""Factories para os modelos de Alteração do Tipo de Alimentação.

Utiliza ``factory_boy`` para criação de instâncias de teste dos modelos
relacionados à alteração de cardápio escolar.
"""

import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from src.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class MotivoAlteracaoCardapioFactory(DjangoModelFactory):
    """Factory para o modelo ``MotivoAlteracaoCardapio``.

    Gera instâncias com nome único usando sequência + Faker.
    """

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = MotivoAlteracaoCardapio


class AlteracaoCardapioFactory(DjangoModelFactory):
    """Factory para o modelo ``AlteracaoCardapio``.

    Cria a escola solicitante, o motivo e os campos de rastreio (escola, lote,
    DRE e terceirizada) via subfactories.
    """

    escola = SubFactory(EscolaFactory)
    motivo = SubFactory(MotivoAlteracaoCardapioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = AlteracaoCardapio


class DataIntervaloAlteracaoCardapioFactory(DjangoModelFactory):
    """Factory para o modelo ``DataIntervaloAlteracaoCardapio``.

    Associa automaticamente uma ``AlteracaoCardapio`` via subfactory.
    """

    alteracao_cardapio = SubFactory(AlteracaoCardapioFactory)

    class Meta:
        model = DataIntervaloAlteracaoCardapio


class SubstituicaoAlimentacaoNoPeriodoEscolarFactory(DjangoModelFactory):
    """Factory para o modelo ``SubstituicaoAlimentacaoNoPeriodoEscolar``.

    Cria a instância com uma alteração de cardápio e um período escolar via
    subfactories. Suporta adição de tipos de alimentação de origem e destino
    via parâmetros ``tipos_alimentacao_de`` e ``tipos_alimentacao_para``.
    """

    alteracao_cardapio = SubFactory(AlteracaoCardapioFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        """Adiciona os tipos de alimentação de origem à instância criada.

        Args:
            create (bool): Indica se a instância está sendo criada (``True``) ou
                apenas construída em memória (``False``).
            extracted: Lista de tipos de alimentação a associar, ou ``None``.
            **kwargs: Argumentos adicionais ignorados.
        """
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        """Adiciona os tipos de alimentação de destino à instância criada.

        Args:
            create (bool): Indica se a instância está sendo criada (``True``) ou
                apenas construída em memória (``False``).
            extracted: Lista de tipos de alimentação a associar, ou ``None``.
            **kwargs: Argumentos adicionais ignorados.
        """
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
