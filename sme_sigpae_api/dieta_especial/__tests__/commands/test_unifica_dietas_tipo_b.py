import datetime
from unittest import TestCase

import pytest
from django.core.management import call_command

from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    LogQuantidadeDietasAutorizadasCEIFactory,
    LogQuantidadeDietasAutorizadasFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)


class UnificaDietasTipoBCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "unifica_dietas_tipo_b",
            *args,
            **kwargs,
        )

    def setup_dietas(self):
        self.classificacao_tipo_b_lanche = ClassificacaoDietaFactory.create(
            nome="Tipo B - LANCHE"
        )
        self.classificacao_tipo_b_lanche_refeicao = ClassificacaoDietaFactory.create(
            nome="Tipo B - LANCHE e REFEIÇÃO"
        )

        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche
        )
        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche
        )
        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche
        )

        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche_refeicao
        )
        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche_refeicao
        )
        SolicitacaoDietaEspecialFactory.create(
            classificacao=self.classificacao_tipo_b_lanche_refeicao
        )

    def setup_logs_dietas_autorizadas(self):
        self.periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        self.escola = EscolaFactory.create(
            nome="EMEF JARBAS SANTOS", codigo_eol="123456"
        )

        for dia in [1, 2, 3, 4, 5]:
            LogQuantidadeDietasAutorizadasFactory.create(
                classificacao=self.classificacao_tipo_b_lanche,
                periodo_escolar=self.periodo_integral,
                quantidade=10,
                escola=self.escola,
                data=datetime.date(2025, 2, dia),
            )

        for dia in [1, 2, 3, 4, 5]:
            LogQuantidadeDietasAutorizadasFactory.create(
                classificacao=self.classificacao_tipo_b_lanche_refeicao,
                periodo_escolar=self.periodo_integral,
                quantidade=20,
                escola=self.escola,
                data=datetime.date(2025, 2, dia),
            )

    def setup_logs_dietas_autorizadas_cei(self):
        faixa_etaria = FaixaEtariaFactory.create()

        for dia in [1, 2, 3, 4, 5]:
            LogQuantidadeDietasAutorizadasCEIFactory.create(
                classificacao=self.classificacao_tipo_b_lanche,
                periodo_escolar=self.periodo_integral,
                quantidade=10,
                escola=self.escola,
                data=datetime.date(2025, 2, dia),
                faixa_etaria=faixa_etaria,
            )

        for dia in [1, 2, 3, 4, 5]:
            LogQuantidadeDietasAutorizadasCEIFactory.create(
                classificacao=self.classificacao_tipo_b_lanche_refeicao,
                periodo_escolar=self.periodo_integral,
                quantidade=20,
                escola=self.escola,
                data=datetime.date(2025, 2, dia),
                faixa_etaria=faixa_etaria,
            )

    def setUp(self) -> None:
        self.setup_dietas()

    @pytest.mark.django_db(transaction=True)
    def test_unifica_dietas_tipo_b(self) -> None:
        self.setup_logs_dietas_autorizadas()
        self.setup_logs_dietas_autorizadas_cei()
        self.call_command()

        assert (
            SolicitacaoDietaEspecial.objects.filter(
                classificacao__nome="Tipo B"
            ).count()
            == 6
        )

        assert (
            LogQuantidadeDietasAutorizadas.objects.filter(
                classificacao__nome="Tipo B"
            ).count()
            == 5
        )
        assert list(
            LogQuantidadeDietasAutorizadas.objects.filter(
                classificacao__nome="Tipo B"
            ).values_list("quantidade", flat=True)
        ) == [30, 30, 30, 30, 30]

        assert (
            LogQuantidadeDietasAutorizadasCEI.objects.filter(
                classificacao__nome="Tipo B"
            ).count()
            == 5
        )
        assert list(
            LogQuantidadeDietasAutorizadasCEI.objects.filter(
                classificacao__nome="Tipo B"
            ).values_list("quantidade", flat=True)
        ) == [30, 30, 30, 30, 30]
