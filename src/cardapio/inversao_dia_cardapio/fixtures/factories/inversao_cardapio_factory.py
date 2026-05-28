"""Factories para o modelo InversaoCardapio.

Utiliza ``factory_boy`` para criar instancias de teste com os relacionamentos
necessarios para o fluxo de inversao de dia de cardapio.
"""

import factory
from factory import SubFactory
from factory.django import DjangoModelFactory

from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from src.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class InversaoCardapioFactory(DjangoModelFactory):
    """Factory para o modelo ``InversaoCardapio``.

    Cria automaticamente a escola solicitante e os campos de rastreio
    (escola, lote, DRE e terceirizada) por meio de subfactories.
    """

    escola = SubFactory(EscolaFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        """Adiciona os tipos de alimentacao a instancia criada.

        Args:
            create (bool): Indica se a instancia foi persistida no banco.
            extracted: Lista de tipos de alimentacao a associar, ou ``None``.
            **kwargs: Argumentos adicionais ignorados.
        """
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = InversaoCardapio
