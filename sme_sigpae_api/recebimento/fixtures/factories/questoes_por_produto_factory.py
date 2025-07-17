from factory import SubFactory
from factory.django import DjangoModelFactory

from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from sme_sigpae_api.recebimento.models import QuestoesPorProduto


class QuestoesPorProdutoFactory(DjangoModelFactory):
    class Meta:
        model = QuestoesPorProduto

    ficha_tecnica = SubFactory(FichaTecnicaFactory)
