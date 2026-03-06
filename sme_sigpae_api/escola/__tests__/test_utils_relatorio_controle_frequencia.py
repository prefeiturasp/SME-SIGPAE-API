"""Testes unitários para a lógica de histórico de matrícula no relatório de controle de frequência.

Focam em verificar que apenas alunos com vínculo ativo na escola requisitante aparecem
no PDF gerado, independentemente de históricos anteriores.
"""

import datetime

import pytest

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    HistoricoMatriculaAlunoFactory,
    LogAlunosMatriculadosFaixaEtariaDiaFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.escola.models import LogAlunoPorDia
from sme_sigpae_api.escola.utils import _coleta_alunos_por_dia, aluno_pertence_a_escola

pytestmark = pytest.mark.django_db


def _cria_log_aluno_por_dia(log_faixa_dia, aluno):
    return LogAlunoPorDia.objects.create(
        log_alunos_matriculados_faixa_dia=log_faixa_dia,
        aluno=aluno,
    )


def _formata_nome_aluno(aluno):
    dn = aluno.data_nascimento
    return f"{aluno.nome} - {dn.day:02d}/{dn.month:02d}/{dn.year}"


# ---------------------------------------------------------------------------
# Testes unitários: aluno_pertence_a_escola
# ---------------------------------------------------------------------------


class TestAlunoPertenceAEscola:
    """Verifica a função aluno_pertence_a_escola em todos os cenários relevantes."""

    def test_aluno_com_escola_fk_direta_retorna_true(self):
        """FK aluno.escola aponta para a escola consultada → sempre True."""
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=escola)
        assert aluno_pertence_a_escola(aluno, escola) is True

    def test_aluno_sem_historico_e_escola_diferente_retorna_false(self):
        """Aluno sem historico + escola FK diferente → False."""
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)
        assert aluno_pertence_a_escola(aluno, escola_a) is False

    def test_historico_mais_recente_na_escola_sem_data_fim_retorna_true(self):
        """Historico mais recente: escola=A, data_fim=None → True para escola A."""
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_a)

        # Histórico antigo na escola B
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_b,
            data_inicio=datetime.date(2024, 1, 1),
            data_fim=datetime.date(2024, 12, 31),
        )
        # Histórico mais recente na escola A, sem data_fim
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )

        assert aluno_pertence_a_escola(aluno, escola_a) is True

    def test_historico_mais_recente_em_outra_escola_retorna_false(self):
        """
        Aluno com histórico mais recente na escola B (data_fim=None).
        Consulta para escola A → False.

        Ex.: escola A: data_inicio 01/01/2025, data_fim None
             escola B: data_inicio 01/01/2026, data_fim None
        Requisição da escola A: NÃO deve exibir o aluno.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_b,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=None,
        )

        assert aluno_pertence_a_escola(aluno, escola_a) is False

    def test_historico_mais_recente_em_outra_escola_retorna_true_para_escola_atual(
        self,
    ):
        """
        Mesmo cenário acima, mas consultando escola B → True.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_b,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=None,
        )

        assert aluno_pertence_a_escola(aluno, escola_b) is True

    def test_historico_com_data_fim_posterior_ao_data_final_param_retorna_true(self):
        """
        Historico mais recente: escola=A, data_fim=2026-03-10.
        data_final param = 2026-03-07 → data_fim (10) > data_final (7) → True.
        O aluno ainda estava matriculado durante todo o período consultado.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 10),
        )

        data_final = datetime.date(2026, 3, 7)
        assert aluno_pertence_a_escola(aluno, escola_a, data_final=data_final) is True

    def test_historico_com_data_fim_anterior_ao_data_final_param_retorna_false(self):
        """
        Historico mais recente: escola=A, data_fim=2026-03-05.
        data_final param = 2026-03-07 → data_fim (5) não > data_final (7) → False.
        O aluno saiu antes do fim do período consultado.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 5),
        )

        data_final = datetime.date(2026, 3, 7)
        assert aluno_pertence_a_escola(aluno, escola_a, data_final=data_final) is False

    def test_historico_com_data_fim_sem_data_final_param_retorna_false(self):
        """
        Historico mais recente: escola=A, data_fim definida, mas sem data_final param.
        Sem param, apenas data_fim=None é aceito → False.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 10),
        )

        assert aluno_pertence_a_escola(aluno, escola_a, data_final=None) is False

    def test_aluno_sem_historico_e_escola_fk_igual_retorna_true(self):
        """Aluno sem nenhum historico, mas FK direta bate → True."""
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=escola)
        # sem historicos
        assert aluno_pertence_a_escola(aluno, escola) is True


# ---------------------------------------------------------------------------
# Testes de integração: _coleta_alunos_por_dia
# ---------------------------------------------------------------------------


class TestColetaAlunosPorDia:
    """Verifica que _coleta_alunos_por_dia filtra corretamente pelo histórico."""

    def _cria_log_faixa_dia(self, escola, data=None):
        periodo = PeriodoEscolarFactory(nome="MANHA")
        faixa = FaixaEtariaFactory(inicio=0, fim=12)
        return LogAlunosMatriculadosFaixaEtariaDiaFactory(
            escola=escola,
            periodo_escolar=periodo,
            faixa_etaria=faixa,
            data=data or datetime.date(2026, 3, 5),
        )

    def test_aluno_com_escola_fk_aparece(self):
        """Aluno cuja FK escola == escola_A aparece na coleta."""
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=escola)
        log_faixa = self._cria_log_faixa_dia(escola)
        _cria_log_aluno_por_dia(log_faixa, aluno)

        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola, None
        )

        assert _formata_nome_aluno(aluno) in alunos_por_dia
        assert _formata_nome_aluno(aluno) in alunos_por_faixa

    def test_aluno_transferido_nao_aparece_sem_data_final(self):
        """Aluno que foi para outra escola (historico mais recente em B) não aparece."""
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        # Historico antigo em A, recente em B
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_b,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=None,
        )

        log_faixa = self._cria_log_faixa_dia(escola_a)
        _cria_log_aluno_por_dia(log_faixa, aluno)

        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola_a, None
        )

        assert _formata_nome_aluno(aluno) not in alunos_por_dia
        assert _formata_nome_aluno(aluno) not in alunos_por_faixa

    def test_aluno_com_historico_ativo_na_escola_aparece(self):
        """Aluno com historico mais recente (data_fim=None) em escola_A aparece."""
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)  # FK atual aponta para B

        # Mas o historico mais recente aponta para A, sem data_fim
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_b,
            data_inicio=datetime.date(2024, 1, 1),
            data_fim=datetime.date(2024, 12, 31),
        )
        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )

        log_faixa = self._cria_log_faixa_dia(escola_a)
        _cria_log_aluno_por_dia(log_faixa, aluno)

        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola_a, None
        )

        assert _formata_nome_aluno(aluno) in alunos_por_dia

    def test_alunos_mistos_apenas_ativo_aparece(self):
        """Dois alunos no mesmo log: apenas o que tem vínculo ativo aparece."""
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()

        aluno_ativo = AlunoFactory(escola=escola_a)
        aluno_transferido = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno_transferido,
            escola=escola_a,
            data_inicio=datetime.date(2025, 1, 1),
            data_fim=None,
        )
        HistoricoMatriculaAlunoFactory(
            aluno=aluno_transferido,
            escola=escola_b,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=None,
        )

        log_faixa = self._cria_log_faixa_dia(escola_a)
        _cria_log_aluno_por_dia(log_faixa, aluno_ativo)
        _cria_log_aluno_por_dia(log_faixa, aluno_transferido)

        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola_a, None
        )

        assert _formata_nome_aluno(aluno_ativo) in alunos_por_dia
        assert _formata_nome_aluno(aluno_transferido) not in alunos_por_dia

    def test_aluno_com_data_fim_historico_posterior_ao_data_final_aparece(self):
        """
        data_final param = 2026-03-07, historico data_fim = 2026-03-10 → aparece.
        O aluno estava matriculado em toda a faixa consultada.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 10),
        )

        log_faixa = self._cria_log_faixa_dia(escola_a, data=datetime.date(2026, 3, 1))
        _cria_log_aluno_por_dia(log_faixa, aluno)

        data_final = datetime.date(2026, 3, 7)
        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola_a, data_final
        )

        assert _formata_nome_aluno(aluno) in alunos_por_dia

    def test_aluno_com_data_fim_historico_anterior_ao_data_final_nao_aparece(self):
        """
        data_final param = 2026-03-07, historico data_fim = 2026-03-05 → não aparece.
        O aluno saiu antes do fim do período consultado.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 5),
        )

        log_faixa = self._cria_log_faixa_dia(escola_a, data=datetime.date(2026, 3, 1))
        _cria_log_aluno_por_dia(log_faixa, aluno)

        data_final = datetime.date(2026, 3, 7)
        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola_a, data_final
        )

        assert _formata_nome_aluno(aluno) not in alunos_por_dia

    def test_sem_filtro_escola_todos_alunos_aparecem(self):
        """Quando escola=None, _coleta_alunos_por_dia não filtra ninguém."""
        escola = EscolaFactory()
        aluno_a = AlunoFactory(escola=escola)
        aluno_b = AlunoFactory(escola=EscolaFactory())

        log_faixa = self._cria_log_faixa_dia(escola)
        _cria_log_aluno_por_dia(log_faixa, aluno_a)
        _cria_log_aluno_por_dia(log_faixa, aluno_b)

        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa, alunos_por_dia, alunos_por_faixa, escola=None, data_final=None
        )

        assert len(alunos_por_dia) == 2
