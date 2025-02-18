import datetime
import os
from unittest import TestCase, mock

import pytest
from django.core.management import call_command

from sme_sigpae_api.escola.fixtures.factories.dia_suspensao_atividades_factory import (
    DiaSuspensaoAtividadesFactory,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    TipoUnidadeEscolarFactory,
)
from sme_sigpae_api.escola.models import DiaSuspensaoAtividades
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
)


class VinculaEditaisDiasSuspensaoCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "vincula_editais_e_dias_suspensao_atividade",
            *args,
            **kwargs,
        )

    def setUp(self) -> None:
        tipo_unidade_escolar = TipoUnidadeEscolarFactory.create(iniciais="EMEF")

        self.lista_editais = [
            "Edital de Pregão n° 74/SME/2022",
            "Edital de pregão n° 87/SME/2022",
            "Edital de pregão n° 75/SME/2022",
            "Edital de Pregão n°78/SME/2016",
            "Edital de Pregão n° 30/SME/2023",
            "Edital de Pregão nº 56/SME/2016",
            "Edital de Pregão n°70/SME/2022",
            "Edital de pregão n° 76/SME/2022",
            "Edital de Pregão n° 78/SME/2022",
            "Edital de Pregão n° 31/SME/2023",
            "Edital de pregão n° 30/SME/2022",
            "Edital de Pregão n° 36/SME/2022",
            "Edital de pregão n° 28/SME/2022",
            "Edital de Pregão n° 35/SME/2022",
        ]
        for edital in self.lista_editais:
            self.edital = EditalFactory.create(numero=edital)

        self.dias = [10, 11, 12, 13, 14, 15]
        for dia in self.dias:
            DiaSuspensaoAtividadesFactory.create(
                data=datetime.date(2025, 2, dia),
                tipo_unidade=tipo_unidade_escolar,
                edital=None,
            )

    @mock.patch.dict(os.environ, {"DJANGO_ENV": "development"})
    @pytest.mark.django_db(transaction=True)
    def test_command_vincula_editais_a_dias_suspensao_dev(self) -> None:
        self.call_command()
        for dia in self.dias:
            assert DiaSuspensaoAtividades.objects.filter(
                data__day=dia, tipo_unidade__iniciais="EMEF"
            ).count() == len(self.lista_editais)

    @mock.patch.dict(os.environ, {"DJANGO_ENV": "production"})
    @pytest.mark.django_db(transaction=True)
    def test_command_vincula_editais_a_dias_suspensao_prod(self) -> None:
        self.call_command()
        for dia in self.dias:
            assert DiaSuspensaoAtividades.objects.filter(
                data__day=dia, tipo_unidade__iniciais="EMEF"
            ).count() == len(self.lista_editais)

    @mock.patch.dict(os.environ, {"DJANGO_ENV": "development"})
    @pytest.mark.django_db(transaction=True)
    def test_command_vincula_editais_a_dias_suspensao_dev_dias_suspensao_sem_edital(
        self,
    ) -> None:
        DiaSuspensaoAtividades.objects.update(edital=self.edital)
        self.call_command()
        for dia in self.dias:
            assert (
                DiaSuspensaoAtividades.objects.filter(
                    data__day=dia, tipo_unidade__iniciais="EMEF"
                ).count()
                == 1
            )
