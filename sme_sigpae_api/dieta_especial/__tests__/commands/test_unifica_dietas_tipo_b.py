from unittest import TestCase

import pytest
from django.core.management import call_command

from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial


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

    def setUp(self) -> None:
        self.setup_dietas()

    @pytest.mark.django_db(transaction=True)
    def test_unifica_dietas_tipo_b(self) -> None:
        self.call_command()

        assert (
            SolicitacaoDietaEspecial.objects.filter(
                classificacao__nome="Tipo B"
            ).count()
            == 6
        )
