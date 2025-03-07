import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from freezegun.api import freeze_time
from requests.models import Response
from rest_framework import status

from sme_sigpae_api.escola.__tests__.conftest import mocked_response
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
    HistoricoMatriculaAlunoFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas import (
    Command,
    MaxRetriesExceeded,
)
from sme_sigpae_api.escola.models import Aluno


class AtualizaAlunosEscolasCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "atualiza_alunos_escolas",
            *args,
            **kwargs,
        )

    def set_up_periodos_escolares(self):
        self.periodo_escolar_manha = PeriodoEscolarFactory.create(
            nome="MANHA", tipo_turno=1
        )
        PeriodoEscolarFactory.create(nome="INTERMEDIARIO", tipo_turno=2)
        PeriodoEscolarFactory.create(nome="TARDE", tipo_turno=3)
        PeriodoEscolarFactory.create(nome="VESPERTINO", tipo_turno=4)
        PeriodoEscolarFactory.create(nome="NOITE", tipo_turno=5)
        PeriodoEscolarFactory.create(nome="INTEGRAL", tipo_turno=6)

    def setUp(self) -> None:
        self.set_up_periodos_escolares()
        self.escola = EscolaFactory.create(codigo_eol="000086")

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_000086_dados_alunos_2024.json",
            "r",
        ) as file:
            self.mocked_response_dados_alunos = mocked_response(json.load(file), 200)

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_000086_dados_alunos_2025.json",
            "r",
        ) as file:
            self.mocked_response_dados_alunos_prox_ano = mocked_response(
                json.load(file), 200
            )

    def setup_escola2(self):
        self.escola2 = EscolaFactory.create(codigo_eol="000094")

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_000094_dados_alunos_2025.json",
            "r",
        ) as file:
            self.mocked_response_dados_alunos_2 = mocked_response(json.load(file), 200)

    def setup_escola2_matricula_concluida(self):
        self.escola2 = EscolaFactory.create(codigo_eol="000094")

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_000094_teste_matricula_concluido.json",
            "r",
        ) as file:
            self.mocked_response_dados_alunos_2 = mocked_response(json.load(file), 200)

    @freeze_time("2024-12-12")
    @patch(
        "sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas.Command.get_response_alunos_por_escola"
    )
    @pytest.mark.django_db(transaction=True)
    def test_command_atualiza_alunos_escolas_d_menos_2(
        self, mock_get_response_alunos_por_escola
    ) -> None:
        self.setup_escola2()

        AlunoFactory.create(
            codigo_eol="7388348",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )

        aluno_7924897 = AlunoFactory.create(
            codigo_eol="7924897",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )
        HistoricoMatriculaAlunoFactory.create(aluno=aluno_7924897, escola=self.escola)

        AlunoFactory.create(
            codigo_eol="8030441",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )

        mock_get_response_alunos_por_escola.side_effect = [
            self.mocked_response_dados_alunos,
            mocked_response({}, 404),
            self.mocked_response_dados_alunos_2,
            mocked_response({}, 404),
        ]
        self.call_command()
        assert Aluno.objects.count() == 289

        aluno_davi = Aluno.objects.get(nome="DAVI LUCAS THOMAZ NASCIMENTO")
        assert aluno_davi.nao_matriculado is False
        assert aluno_davi.escola == self.escola

        assert aluno_davi.historico.count() == 2
        historico_escola_000086 = aluno_davi.historico.get(escola=self.escola)
        assert historico_escola_000086.data_fim is None

        aluno_kimberlly = Aluno.objects.get(codigo_eol="8030441")
        assert aluno_kimberlly.historico.exists() is True

        aluno_theo = Aluno.objects.get(codigo_eol="7924897")
        assert aluno_theo.historico.count() == 1
        assert aluno_theo.historico.get().data_fim is not None

        assert Aluno.objects.filter(nome="ZOE MOURA VIANA CARDOSO").exists() is False

    @freeze_time("2024-12-12")
    @patch(
        "sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas.Command.get_response_alunos_por_escola"
    )
    @pytest.mark.django_db(transaction=True)
    def test_command_atualiza_alunos_escolas_d_menos_2_rematricula(
        self,
        mock_get_response_alunos_por_escola,
    ) -> None:
        self.setup_escola2_matricula_concluida()

        AlunoFactory.create(
            codigo_eol="7388348",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )

        mock_get_response_alunos_por_escola.side_effect = [
            self.mocked_response_dados_alunos,
            mocked_response({}, 404),
            self.mocked_response_dados_alunos_2,
            mocked_response({}, 404),
        ]
        self.call_command()
        assert Aluno.objects.count() == 288

        aluno_davi = Aluno.objects.get(nome="DAVI LUCAS THOMAZ NASCIMENTO")
        assert aluno_davi.nao_matriculado is False
        assert aluno_davi.escola == self.escola

        assert aluno_davi.historico.count() == 2
        historico_escola_000086 = aluno_davi.historico.get(escola=self.escola)
        assert historico_escola_000086.data_fim is None

        historico_escola_000094 = aluno_davi.historico.get(escola=self.escola2)
        assert historico_escola_000094.data_fim is not None

        assert Aluno.objects.filter(nome="ZOE MOURA VIANA CARDOSO").exists() is False

    @freeze_time("2025-01-01")
    @patch(
        "sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas.Command.get_response_alunos_por_escola"
    )
    @pytest.mark.django_db(transaction=True)
    def test_command_atualiza_alunos_escolas_d_menos_1(
        self,
        mock_get_response_alunos_por_escola,
    ) -> None:
        self.setup_escola2()

        aluno_7924897 = AlunoFactory.create(
            codigo_eol="7924897",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )
        HistoricoMatriculaAlunoFactory.create(aluno=aluno_7924897, escola=self.escola)

        AlunoFactory.create(
            codigo_eol="8030441",
            periodo_escolar=self.periodo_escolar_manha,
            escola=self.escola,
        )

        mock_get_response_alunos_por_escola.side_effect = [
            self.mocked_response_dados_alunos,
            mocked_response({}, 404),
            self.mocked_response_dados_alunos_2,
            mocked_response({}, 404),
        ]
        self.call_command()
        assert Aluno.objects.count() == 289

        aluno_davi = Aluno.objects.get(nome="DAVI LUCAS THOMAZ NASCIMENTO")
        assert aluno_davi.nao_matriculado is False
        assert aluno_davi.escola == self.escola2

        assert aluno_davi.historico.count() == 2
        historico_escola_000086 = aluno_davi.historico.get(escola=self.escola)
        assert historico_escola_000086.data_fim is None

        historico_escola_000094 = aluno_davi.historico.get(escola=self.escola2)
        assert historico_escola_000094.data_fim is None

        aluno_kimberlly = Aluno.objects.get(codigo_eol="8030441")
        assert aluno_kimberlly.historico.exists() is True

        aluno_theo = Aluno.objects.get(codigo_eol="7924897")
        assert aluno_theo.historico.count() == 1
        assert aluno_theo.historico.get().data_fim is not None

        assert Aluno.objects.filter(nome="ZOE MOURA VIANA CARDOSO").exists() is False

    @freeze_time("2025-01-01")
    @patch(
        "sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas.Command.get_response_alunos_por_escola"
    )
    @pytest.mark.django_db(transaction=True)
    def test_command_atualiza_alunos_escolas_d_menos_1_rematricula(
        self,
        mock_get_response_alunos_por_escola,
    ) -> None:
        self.setup_escola2_matricula_concluida()
        mock_get_response_alunos_por_escola.side_effect = [
            self.mocked_response_dados_alunos,
            mocked_response({}, 404),
            self.mocked_response_dados_alunos_2,
            mocked_response({}, 404),
        ]
        self.call_command()
        assert Aluno.objects.count() == 288

        aluno_davi = Aluno.objects.get(nome="DAVI LUCAS THOMAZ NASCIMENTO")
        assert aluno_davi.nao_matriculado is False
        assert aluno_davi.escola == self.escola

        assert aluno_davi.historico.count() == 2
        historico_escola_000086 = aluno_davi.historico.get(escola=self.escola)
        assert historico_escola_000086.data_fim is None

        historico_escola_000094 = aluno_davi.historico.get(escola=self.escola2)
        assert historico_escola_000094.data_fim is not None

        assert Aluno.objects.filter(nome="ZOE MOURA VIANA CARDOSO").exists() is False


class TestObtemAlunosEscola(TestCase):
    def set_up_periodos_escolares(self):
        PeriodoEscolarFactory.create(nome="MANHA", tipo_turno=1)
        PeriodoEscolarFactory.create(nome="INTERMEDIARIO", tipo_turno=2)
        PeriodoEscolarFactory.create(nome="TARDE", tipo_turno=3)
        PeriodoEscolarFactory.create(nome="VESPERTINO", tipo_turno=4)
        PeriodoEscolarFactory.create(nome="NOITE", tipo_turno=5)
        PeriodoEscolarFactory.create(nome="INTEGRAL", tipo_turno=6)

    def setUp(self) -> None:
        self.set_up_periodos_escolares()
        self.escola = EscolaFactory.create(codigo_eol="000086")
        self.command = Command()

    @patch(
        "sme_sigpae_api.escola.management.commands.atualiza_alunos_escolas.Command.get_response_alunos_por_escola"
    )
    @pytest.mark.django_db(transaction=True)
    def test_max_retries_exceeded(self, mock_get_response):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        mock_response.json.return_value = {"error": "Service Unavailable"}
        mock_response.text = "503 service unavailable"
        mock_get_response.return_value = mock_response

        with self.assertRaises(MaxRetriesExceeded) as context:
            self.command._obtem_alunos_escola("000086")

        self.assertEqual(mock_get_response.call_count, 10)
        self.assertIn(
            "Máximo de tentativas alcançada para a escola 000086",
            str(context.exception),
        )
        assert Aluno.objects.count() == 0
