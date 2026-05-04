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
    escola = SubFactory(EscolaFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = InversaoCardapio
