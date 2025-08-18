import json
from unittest import TestCase
from unittest.mock import patch

import pytest
from freezegun.api import freeze_time

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.eol_servico.utils import (
    EOLException,
    EOLServicoSGP,
    dt_nascimento_from_api,
)
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

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_dre_108100_matriculas_escolas_quantidades.json",
            "r",
        ) as file:
            self.mocked_response_matricula_por_escola = mocked_response(
                json.load(file), 200
            )

        self.mocked_api_eol_erro_503 = mocked_response("Timeout", 503)

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

    @freeze_time("2024-12-27")
    @pytest.mark.django_db(transaction=True)
    @patch("requests.get")
    def test_matricula_por_escola(self, mock_response_matricula_por_escola):
        mock_response_matricula_por_escola.return_value = (
            self.mocked_response_matricula_por_escola
        )

        response = self.eol_servico_sgp.matricula_por_escola(
            self.escola.codigo_eol, "2024-12-27", 1
        )
        assert response == self.mocked_response_matricula_por_escola.json()

    @freeze_time("2024-12-27")
    @pytest.mark.django_db(transaction=True)
    @patch("requests.get")
    def test_matricula_por_escola(self, mock_response_matricula_por_escola):
        mock_response_matricula_por_escola.return_value = self.mocked_api_eol_erro_503
        with self.assertRaises(EOLException) as context:
            EOLServicoSGP.matricula_por_escola("400020", "2024-12-01")

        self.assertIn("API EOL do SGP está com erro", str(context.exception))
        self.assertIn("Status: 503", str(context.exception))


def test_redefine_senha_coresso(client_autenticado_da_escola, monkeypatch):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_altera_senha",
        lambda p1: mocked_response({}, 200),
    )
    response = EOLServicoSGP.redefine_senha("123456", DJANGO_ADMIN_PASSWORD)
    assert response == "OK"


def test_redefine_senha_coresso_eol_exception(
    client_autenticado_da_escola, monkeypatch
):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_altera_senha",
        lambda p1: mocked_response({"erro": "EOL fora do ar"}, 400),
    )
    with pytest.raises(EOLException):
        EOLServicoSGP.redefine_senha("123456", DJANGO_ADMIN_PASSWORD)


def test_redefine_email_coresso(client_autenticado_da_escola, monkeypatch):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_altera_email_coresso",
        lambda p1: mocked_response({}, 200),
    )
    response = EOLServicoSGP.redefine_email("123456", DJANGO_ADMIN_PASSWORD)
    assert response == "OK"


def test_redefine_email_coresso_eol_exception(
    client_autenticado_da_escola, monkeypatch
):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_altera_email_coresso",
        lambda p1: mocked_response({"erro": "EOL fora do ar"}, 400),
    )
    with pytest.raises(EOLException):
        EOLServicoSGP.redefine_email("123456", DJANGO_ADMIN_PASSWORD)


def test_criar_usuario_coresso(client_autenticado_da_escola, monkeypatch):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_criar_usuario_coresso",
        lambda p1, p2: mocked_response({}, 200),
    )
    response = EOLServicoSGP.cria_usuario_core_sso(
        "123456", "FULANO DA SILVA", "fulano@silva.com"
    )
    assert response == "OK"


def test_criar_usuario_coresso_eol_exception(client_autenticado_da_escola, monkeypatch):
    monkeypatch.setattr(
        EOLServicoSGP,
        "chamada_externa_criar_usuario_coresso",
        lambda p1, p2: mocked_response({"erro": "EOL fora do ar"}, 400),
    )
    with pytest.raises(EOLException):
        EOLServicoSGP.cria_usuario_core_sso(
            "123456", "FULANO DA SILVA", "fulano@silva.com"
        )
