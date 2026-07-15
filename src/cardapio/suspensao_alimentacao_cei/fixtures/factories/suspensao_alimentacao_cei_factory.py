"""Factories para o modelo de Suspensão de Alimentação de CEI.

Utiliza ``factory_boy`` para criação de instâncias de teste do modelo
de suspensão de alimentação escolar de CEI.
"""

import factory
from factory import SubFactory
from factory.django import DjangoModelFactory

from src.cardapio.suspensao_alimentacao.fixtures.factories.suspensao_alimentacao_factory import (
    MotivoSuspensaoFactory,
)
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
)
from src.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class SuspensaoAlimentacaoDaCEIFactory(DjangoModelFactory):
    """Factory para o modelo ``SuspensaoAlimentacaoDaCEI``.

    Cria uma solicitação de suspensão de alimentação de CEI com escola,
    motivo, data e campos de rastreio via subfactories. Suporta adição de
    períodos escolares via parâmetro ``periodos_escolares`` no pós-create.
    """

    criado_por = SubFactory(UsuarioFactory)
    escola = SubFactory(EscolaFactory)
    motivo = SubFactory(MotivoSuspensaoFactory)
    data = factory.faker.Faker("date")
    rastro_escola = SubFactory(EscolaFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    @factory.post_generation
    def periodos_escolares(self, create, extracted, **kwargs):
        """Adiciona os períodos escolares suspensos à instância criada.

        Args:
            create (bool): Indica se a instância está sendo criada (``True``)
                ou apenas construída em memória (``False``).
            extracted (list | None): Lista de períodos escolares a associar.
                Se ``None``, nenhum período é adicionado.
            **kwargs: Argumentos adicionais ignorados.
        """
        if not create:
            return

        if extracted:
            for periodo_escolar in extracted:
                self.periodos_escolares.add(periodo_escolar)

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
