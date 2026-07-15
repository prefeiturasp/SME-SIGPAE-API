"""Factories para os modelos de Suspensão de Alimentação.

Utiliza ``factory_boy`` para criação de instâncias de teste dos modelos
relacionados à suspensão de alimentação escolar.
"""

import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
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


class GrupoSuspensaoAlimentacaoFactory(DjangoModelFactory):
    """Factory para o modelo ``GrupoSuspensaoAlimentacao``.

    Cria a escola solicitante e os campos de rastreio (escola, lote, DRE e
    terceirizada) via subfactories.
    """

    escola = SubFactory(EscolaFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = GrupoSuspensaoAlimentacao


class MotivoSuspensaoFactory(DjangoModelFactory):
    """Factory para o modelo ``MotivoSuspensao``.

    Gera instâncias com nome único usando sequência + Faker.
    """

    nome = Sequence(lambda n: f"nome - {fake.name()}")

    class Meta:
        model = MotivoSuspensao


class SuspensaoAlimentacaoFactory(DjangoModelFactory):
    """Factory para o modelo ``SuspensaoAlimentacao``.

    Associa automaticamente um ``GrupoSuspensaoAlimentacao`` e um
    ``MotivoSuspensao`` via subfactories.
    """

    grupo_suspensao = SubFactory(GrupoSuspensaoAlimentacaoFactory)
    motivo = SubFactory(MotivoSuspensaoFactory)

    class Meta:
        model = SuspensaoAlimentacao


class QuantidadePorPeriodoSuspensaoAlimentacaoFactory(DjangoModelFactory):
    """Factory para o modelo ``QuantidadePorPeriodoSuspensaoAlimentacao``.

    Cria a instância com um grupo de suspensão, um período escolar e
    um número aleatório de alunos via subfactories. Suporta adição de
    tipos de alimentação via parâmetro ``tipos_alimentacao``.
    """

    grupo_suspensao = SubFactory(GrupoSuspensaoAlimentacaoFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    numero_alunos = Sequence(lambda n: fake.random_int(min=1, max=100))

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        """Adiciona os tipos de alimentação suspensos à instância criada.

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
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao
