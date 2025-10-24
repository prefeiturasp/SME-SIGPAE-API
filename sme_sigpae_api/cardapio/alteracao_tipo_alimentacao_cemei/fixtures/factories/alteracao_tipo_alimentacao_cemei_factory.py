import factory
from factory import SubFactory
from factory.django import DjangoModelFactory

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory import (
    MotivoAlteracaoCardapioFactory,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    DataIntervaloAlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class AlteracaoCardapioCEMEIFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    motivo = SubFactory(MotivoAlteracaoCardapioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = AlteracaoCardapioCEMEI


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory(DjangoModelFactory):
    alteracao_cardapio = SubFactory(AlteracaoCardapioCEMEIFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory(DjangoModelFactory):
    alteracao_cardapio = SubFactory(AlteracaoCardapioCEMEIFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEIFactory(DjangoModelFactory):
    substituicao_alimentacao = SubFactory(
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory
    )
    faixa_etaria = SubFactory(FaixaEtariaFactory)

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEMEICEI


class DataIntervaloAlteracaoCardapioCEMEIFactory(DjangoModelFactory):
    alteracao_cardapio_cemei = SubFactory(AlteracaoCardapioCEMEIFactory)

    class Meta:
        model = DataIntervaloAlteracaoCardapioCEMEI
