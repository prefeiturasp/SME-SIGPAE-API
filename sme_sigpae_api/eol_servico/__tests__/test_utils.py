import json
from unittest import TestCase
from unittest.mock import patch

import pytest

from sme_sigpae_api.eol_servico.utils import EOLServicoSGP, dt_nascimento_from_api
from sme_sigpae_api.escola.__tests__.conftest import mocked_response
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)


def test_utils_dt_nascimento_from_api(datas_nascimento_api):
    (str_dt_nascimento, ano, mes, dia) = datas_nascimento_api
    obj_dt_nascimento = dt_nascimento_from_api(str_dt_nascimento)
    assert obj_dt_nascimento.year == ano
    assert obj_dt_nascimento.month == mes
    assert obj_dt_nascimento.day == dia


class TestEOLServicoSGP(TestCase):
    def set_up_faixas_etarias(self):
        FaixaEtariaFactory.create(inicio=0, fim=1)
        FaixaEtariaFactory.create(inicio=1, fim=4)
        FaixaEtariaFactory.create(inicio=4, fim=6)
        FaixaEtariaFactory.create(inicio=6, fim=7)
        FaixaEtariaFactory.create(inicio=7, fim=12)
        FaixaEtariaFactory.create(inicio=12, fim=48)
        FaixaEtariaFactory.create(inicio=48, fim=73)

    def setUp(self) -> None:
        self.eol_servico_sgp = EOLServicoSGP()
        self.escola = EscolaFactory.create(
            nome="CEI DIRET CABREUVAS",
            codigo_eol="400020",
            tipo_unidade__iniciais="CEI DIRET",
        )

        PeriodoEscolarFactory.create(nome="INTEGRAL", tipo_turno=6)
        self.set_up_faixas_etarias()

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_400509_dados_alunos_2025.json",
            "r",
        ) as file:
            self.mocked_chamada_externa_alunos_por_escola_por_ano_letivo = (
                mocked_response(json.load(file), 200)
            )

    @pytest.mark.django_db(transaction=True)
    @patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.chamada_externa_alunos_por_escola_por_ano_letivo"
    )
    def test_get_alunos_por_escola_por_ano_letivo(
        self, mock_chamada_externa_alunos_por_escola_por_ano_letivo
    ):
        mock_chamada_externa_alunos_por_escola_por_ano_letivo.return_value = (
            self.mocked_chamada_externa_alunos_por_escola_por_ano_letivo
        )

        lista_alunos = self.eol_servico_sgp.get_alunos_por_escola_por_ano_letivo(
            self.escola.codigo_eol
        )
        assert len(lista_alunos) == 1
        assert lista_alunos[0]["nomeAluno"] == "MILENA SANTOS"
