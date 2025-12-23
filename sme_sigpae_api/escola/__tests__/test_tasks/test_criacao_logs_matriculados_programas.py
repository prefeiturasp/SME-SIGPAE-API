import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from sme_sigpae_api.escola.__tests__.conftest import mocked_response
from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola
from sme_sigpae_api.escola.tasks import matriculados_por_escola_e_periodo_regulares

pytestmark = pytest.mark.django_db


class TestUseCaseCriacaoLogsMatriculadosProgramas:

    def _setup_generico(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
    ):
        self.periodo_manha = periodo_escolar_factory.create(nome="MANHA")
        self.periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
        self.periodo_integral = periodo_escolar_factory.create(nome="INTEGRAL")

        self.dre = diretoria_regional_factory.create(
            nome="IPIRANGA", iniciais="IP", codigo_eol="000200"
        )
        self.terceirizada = empresa_factory.create(nome_fantasia="EMPRESA LTDA")
        self.lote = lote_factory.create(
            nome="LOTE 01", diretoria_regional=self.dre, terceirizada=self.terceirizada
        )

    def _setup_escola_emef(self, tipo_unidade_escolar_factory, escola_factory):
        self.tipo_unidade_emef = tipo_unidade_escolar_factory.create(iniciais="EMEF")
        self.escola_emef = escola_factory.create(
            nome="EMEF PERICLES",
            tipo_gestao__nome="TERC TOTAL",
            codigo_eol="000099",
            tipo_unidade=self.tipo_unidade_emef,
            lote=self.lote,
            diretoria_regional=self.dre,
        )

    def _setup_dias_letivos(self, dia_calendario_factory):
        for i in range(1, 31):
            dia_calendario_factory.create(
                escola=self.escola_emef,
                dia_letivo=True,
                data=datetime.date(2025, 11, i),
            )
        for i in range(1, 32):
            dia_calendario_factory.create(
                escola=self.escola_emef,
                dia_letivo=i <= 19,
                data=datetime.date(2025, 12, i),
            )

    def _setup_mock_matriculas_dre(self):
        self.mocked_response_matriculas_dre = [
            {
                "totalMatriculas": 114,
                "codigoEolEscola": "000099",
                "turnos": [
                    {"turno": "Manhã", "tipoTurno": 1, "quantidade": 48},
                    {"turno": "Tarde", "tipoTurno": 3, "quantidade": 66},
                ],
            }
        ]

    def _setup(
        self,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        dia_calendario_factory,
    ):
        self._setup_generico(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
        )
        self._setup_escola_emef(tipo_unidade_escolar_factory, escola_factory)
        self._setup_dias_letivos(dia_calendario_factory)
        self._setup_mock_matriculas_dre()

    @freeze_time("2025-12-19")
    @patch("sme_sigpae_api.escola.utils.EOLServicoSGP.matricula_por_escola")
    def test_matriculados_por_escola_e_periodo_regulares_ultimo_dia_letivo(
        self,
        mock_matricula_por_escola,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        dia_calendario_factory,
    ):
        self._setup(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
            tipo_unidade_escolar_factory,
            escola_factory,
            dia_calendario_factory,
        )
        mock_matricula_por_escola.return_value = self.mocked_response_matriculas_dre

        matriculados_por_escola_e_periodo_regulares()

        assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 4
        assert (
            LogAlunosMatriculadosPeriodoEscola.objects.filter(
                criado_em__date="2025-12-18"
            ).count()
            == 2
        )
        assert (
            LogAlunosMatriculadosPeriodoEscola.objects.filter(
                criado_em__date="2025-12-19"
            ).count()
            == 2
        )

    @freeze_time("2025-12-18")
    @patch("sme_sigpae_api.escola.utils.EOLServicoSGP.matricula_por_escola")
    def test_matriculados_por_escola_e_periodo_regulares_nao_e_ultimo_dia_letivo(
        self,
        mock_matricula_por_escola,
        periodo_escolar_factory,
        diretoria_regional_factory,
        empresa_factory,
        lote_factory,
        tipo_unidade_escolar_factory,
        escola_factory,
        dia_calendario_factory,
    ):
        self._setup(
            periodo_escolar_factory,
            diretoria_regional_factory,
            empresa_factory,
            lote_factory,
            tipo_unidade_escolar_factory,
            escola_factory,
            dia_calendario_factory,
        )
        mock_matricula_por_escola.return_value = self.mocked_response_matriculas_dre

        matriculados_por_escola_e_periodo_regulares()

        assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 2
        assert (
            LogAlunosMatriculadosPeriodoEscola.objects.filter(
                criado_em__date="2025-12-17"
            ).count()
            == 2
        )
        assert (
            LogAlunosMatriculadosPeriodoEscola.objects.filter(
                criado_em__date="2025-12-18"
            ).count()
            == 0
        )
