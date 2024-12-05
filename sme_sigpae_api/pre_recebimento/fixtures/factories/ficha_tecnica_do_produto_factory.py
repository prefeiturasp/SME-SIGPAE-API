from factory import DjangoModelFactory, LazyFunction, SubFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.fixtures.factories.unidade_medida_factory import (
    UnidadeMedidaFactory,
)
from sme_sigpae_api.pre_recebimento.models.cronograma import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
)
from sme_sigpae_api.produto.fixtures.factories.produto_factory import (
    MarcaFactory,
    ProdutoLogisticaFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class FichaTecnicaFactory(DjangoModelFactory):
    class Meta:
        model = FichaTecnicaDoProduto

    empresa = SubFactory(EmpresaFactory)
    produto = SubFactory(ProdutoLogisticaFactory)
    marca = SubFactory(MarcaFactory)
    categoria = LazyFunction(
        lambda: fake.random.choice(
            [
                FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
                FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
            ]
        )
    )
    peso_liquido_embalagem_primaria = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
    unidade_medida_primaria = SubFactory(UnidadeMedidaFactory)
    peso_liquido_embalagem_secundaria = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
    unidade_medida_secundaria = SubFactory(UnidadeMedidaFactory)
    embalagem_primaria = LazyFunction(lambda: fake.text())
    embalagem_secundaria = LazyFunction(lambda: fake.text())


class AnaliseFichaTecnicaFactory(DjangoModelFactory):
    class Meta:
        model = AnaliseFichaTecnica

    ficha_tecnica = SubFactory(FichaTecnicaFactory)
