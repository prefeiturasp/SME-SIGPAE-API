"""Testes unitários para a lógica de histórico de matrícula no relatório de controle de frequência.

Focam em verificar que apenas alunos com vínculo ativo na escola requisitante aparecem
no PDF gerado, independentemente de históricos anteriores.
"""

import datetime

import pytest
from freezegun import freeze_time

from src.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    HistoricoMatriculaAlunoFactory,
    LogAlunosMatriculadosFaixaEtariaDiaFactory,
    PeriodoEscolarFactory,
)
from src.escola.models import (
    FaixaEtaria,
    LogAlunoPorDia,
    LogAlunosMatriculadosFaixaEtariaDia,
)
from src.escola.utils import (
    _coleta_alunos_por_dia,
    _filtra_alunos_faixa_para_extensao,
    aluno_pertence_a_escola,
    formata_periodos_pdf_controle_frequencia,
    trata_dados_futuro_mes_atual,
)

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
        Historico: escola=A, data_inicio=01/01/2026, data_fim=10/03/2026.
        Intervalo consultado: 01/03/2026 a 07/03/2026.
        Sobreposição: 01/03 <= 10/03 E 01/01 <= 07/03 → True.
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

        data_inicial = datetime.date(2026, 3, 1)
        data_final = datetime.date(2026, 3, 7)
        assert (
            aluno_pertence_a_escola(
                aluno, escola_a, data_inicial=data_inicial, data_final=data_final
            )
            is True
        )

    def test_historico_com_data_fim_anterior_ao_data_final_param_retorna_false(self):
        """
        Historico: escola=A, data_inicio=01/01/2026, data_fim=28/02/2026.
        Intervalo consultado: 01/03/2026 a 07/03/2026.
        Sobreposição: 01/03 <= 28/02? Não → False.
        O aluno saiu antes do início do período consultado.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 2, 28),
        )

        data_inicial = datetime.date(2026, 3, 1)
        data_final = datetime.date(2026, 3, 7)
        assert (
            aluno_pertence_a_escola(
                aluno, escola_a, data_inicial=data_inicial, data_final=data_final
            )
            is False
        )

    def test_historico_com_data_fim_sem_params_de_data_retorna_false(self):
        """
        Historico mais recente: escola=A, data_fim definida, sem params de data.
        Sem intervalo, apenas data_fim=None é aceito → False.
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

        assert aluno_pertence_a_escola(aluno, escola_a) is False

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
        Historico: data_inicio=01/01/2026, data_fim=10/03/2026.
        Intervalo consultado: 01/03 a 07/03 → sobreposição → aparece.
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

        data_inicial = datetime.date(2026, 3, 1)
        data_final = datetime.date(2026, 3, 7)
        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa,
            alunos_por_dia,
            alunos_por_faixa,
            escola_a,
            data_inicial,
            data_final,
        )

        assert _formata_nome_aluno(aluno) in alunos_por_dia

    def test_aluno_com_data_fim_historico_anterior_ao_data_final_nao_aparece(self):
        """
        Historico: data_inicio=01/01/2026, data_fim=28/02/2026.
        Intervalo consultado: 01/03 a 07/03 → sem sobreposição → não aparece.
        O aluno saiu antes do início do período consultado.
        """
        escola_a = EscolaFactory()
        escola_b = EscolaFactory()
        aluno = AlunoFactory(escola=escola_b)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola_a,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 2, 28),
        )

        log_faixa = self._cria_log_faixa_dia(escola_a, data=datetime.date(2026, 3, 1))
        _cria_log_aluno_por_dia(log_faixa, aluno)

        data_inicial = datetime.date(2026, 3, 1)
        data_final = datetime.date(2026, 3, 7)
        alunos_por_dia = []
        alunos_por_faixa = []
        _coleta_alunos_por_dia(
            log_faixa,
            alunos_por_dia,
            alunos_por_faixa,
            escola_a,
            data_inicial,
            data_final,
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
            log_faixa,
            alunos_por_dia,
            alunos_por_faixa,
            escola=None,
            data_inicial=None,
            data_final=None,
        )

        assert len(alunos_por_dia) == 2


class TestFormataPeriodosPdfControleFrequencia:
    def _cria_log_faixa_dia(self, escola, data=None):
        periodo = PeriodoEscolarFactory(nome="MANHA")
        faixa = FaixaEtariaFactory(inicio=0, fim=12)
        return LogAlunosMatriculadosFaixaEtariaDiaFactory(
            escola=escola,
            periodo_escolar=periodo,
            faixa_etaria=faixa,
            data=data or datetime.date(2026, 3, 15),
        )

    def _qtd_matriculados(self, periodo):
        return {"periodos": {periodo.nome: 1}}

    def test_periodo_padrao_do_mes_inclui_aluno_com_historico_encerrado_no_mes(self):
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=EscolaFactory())
        log_faixa = self._cria_log_faixa_dia(escola, data=datetime.date(2026, 3, 15))
        _cria_log_aluno_por_dia(log_faixa, aluno)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 15),
        )

        periodos = formata_periodos_pdf_controle_frequencia(
            self._qtd_matriculados(log_faixa.periodo_escolar),
            log_faixa.__class__.objects.filter(pk=log_faixa.pk),
            {"mes_ano": "03_2026"},
            escola,
            mes_seguinte=False,
        )

        assert (
            _formata_nome_aluno(aluno) in periodos[0]["faixas"][0]["alunos_por_faixa"]
        )

    def test_periodo_explicito_do_mes_inclui_aluno_com_historico_encerrado_no_mes(self):
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=EscolaFactory())
        log_faixa = self._cria_log_faixa_dia(escola, data=datetime.date(2026, 3, 15))
        _cria_log_aluno_por_dia(log_faixa, aluno)

        HistoricoMatriculaAlunoFactory(
            aluno=aluno,
            escola=escola,
            data_inicio=datetime.date(2026, 1, 1),
            data_fim=datetime.date(2026, 3, 15),
        )

        periodos = formata_periodos_pdf_controle_frequencia(
            self._qtd_matriculados(log_faixa.periodo_escolar),
            log_faixa.__class__.objects.filter(pk=log_faixa.pk),
            {
                "mes_ano": "03_2026",
                "data_inicial": "2026-03-01",
                "data_final": "2026-03-31",
            },
            escola,
            mes_seguinte=False,
        )

        assert (
            _formata_nome_aluno(aluno) in periodos[0]["faixas"][0]["alunos_por_faixa"]
        )


class TestFiltraAlunosFaixaParaExtensao:
    """Verifica a lógica de filtragem de alunos por faixa etária para extensão futura."""

    def test_aluno_na_faixa_permanece(self):
        """Aluno cujo nascimento pertence à faixa na data de referência → permanece."""
        # "00 meses" (inicio=0, fim=1): em 25/05/2026, abrange nascidos em [25/04, 25/05)
        faixa = FaixaEtaria(inicio=0, fim=1)
        aluno_str = "JOAO SILVA - 20/05/2026"  # 5 dias → dentro de "00 meses"
        resultado = _filtra_alunos_faixa_para_extensao(
            [aluno_str], faixa, datetime.date(2026, 5, 25)
        )
        assert aluno_str in resultado

    def test_aluno_fora_da_faixa_removido(self):
        """Aluno cujo nascimento não pertence mais à faixa na data de referência → removido."""
        # LEVI nascido 10/04/2026: em 25/05/2026 tem 1 mês e 15 dias → fora de "00 meses"
        faixa = FaixaEtaria(inicio=0, fim=1)
        aluno_str = "LEVI BRITO DA COSTA - 10/04/2026"
        resultado = _filtra_alunos_faixa_para_extensao(
            [aluno_str], faixa, datetime.date(2026, 5, 25)
        )
        assert aluno_str not in resultado

    def test_lista_vazia_retorna_lista_vazia(self):
        faixa = FaixaEtaria(inicio=0, fim=1)
        assert (
            _filtra_alunos_faixa_para_extensao([], faixa, datetime.date(2026, 5, 25))
            == []
        )

    def test_aluno_com_formato_invalido_permanece_por_seguranca(self):
        """String sem separador ' - ' esperado → mantém o aluno por segurança."""
        faixa = FaixaEtaria(inicio=0, fim=1)
        aluno_str = "SEM FORMATO PADRAO"
        resultado = _filtra_alunos_faixa_para_extensao(
            [aluno_str], faixa, datetime.date(2026, 5, 25)
        )
        assert aluno_str in resultado

    def test_aluno_com_data_invalida_permanece_por_seguranca(self):
        """Data mal-formada no separador → mantém o aluno por segurança."""
        faixa = FaixaEtaria(inicio=0, fim=1)
        aluno_str = "NOME ALUNO - nao/e/data"
        resultado = _filtra_alunos_faixa_para_extensao(
            [aluno_str], faixa, datetime.date(2026, 5, 25)
        )
        assert aluno_str in resultado

    def test_filtra_alunos_mistos_apenas_na_faixa_permanece(self):
        """Dois alunos: um na faixa e outro fora → apenas o da faixa permanece."""
        faixa = FaixaEtaria(inicio=0, fim=1)
        # Em 25/05/2026, "00 meses" abrange nascidos em [25/04/2026, 25/05/2026)
        aluno_na_faixa = "JOSE - 01/05/2026"  # 24 dias → dentro de "00 meses"
        aluno_fora = "LEVI - 10/04/2026"  # ~45 dias → fora de "00 meses"
        resultado = _filtra_alunos_faixa_para_extensao(
            [aluno_na_faixa, aluno_fora], faixa, datetime.date(2026, 5, 25)
        )
        assert aluno_na_faixa in resultado
        assert aluno_fora not in resultado


class TestTrataDadosFuturoMesAtualMudancaFaixa:
    """
    Verifica que a extensão para dias futuros no mês corrente não propaga
    alunos que mudaram de faixa etária no decorrer do mês (aniversário).
    """

    @freeze_time("2026-05-25")
    def test_aluno_que_mudou_de_faixa_nao_aparece_nos_dias_estendidos(self):
        """
        LEVI nasceu em 10/04/2026. Os logs de "00 meses" cobrem os dias 06-09 de maio
        (antes do aniversário de 1 mês). Em 25/05/2026 LEVI pertence a "01 a 03 meses",
        portanto a extensão para 10-31/05 em "00 meses" NÃO deve incluí-lo.
        """
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=escola, data_nascimento=datetime.date(2026, 4, 10))
        periodo = PeriodoEscolarFactory(nome="INTEGRAL")
        faixa_00meses = FaixaEtariaFactory(inicio=0, fim=1)

        logs = [
            LogAlunosMatriculadosFaixaEtariaDiaFactory(
                escola=escola,
                periodo_escolar=periodo,
                faixa_etaria=faixa_00meses,
                data=datetime.date(2026, 5, dia),
            )
            for dia in range(6, 10)  # dias 6, 7, 8, 9
        ]
        for log in logs:
            _cria_log_aluno_por_dia(log, aluno)

        ultimo_log = logs[-1]  # dia 9
        queryset = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
            pk__in=[l.pk for l in logs]
        )

        levi_str = _formata_nome_aluno(aluno)
        alunos_por_dia = [levi_str]
        dias = [{"dia": "09", "alunos_por_dia": list(alunos_por_dia)}]

        trata_dados_futuro_mes_atual(
            queryset,
            ultimo_log,
            dias,
            alunos_por_dia,
            31,  # maio tem 31 dias
            {"mes_ano": "05_2026"},
        )

        dias_estendidos = [d for d in dias if int(d["dia"]) >= 10]
        assert len(dias_estendidos) == 22  # dias 10-31
        for dia_dict in dias_estendidos:
            assert (
                levi_str not in dia_dict["alunos_por_dia"]
            ), f"LEVI não deveria aparecer em 'dia={dia_dict['dia']}' de '00 meses'"

    @freeze_time("2026-05-25")
    def test_aluno_ainda_na_faixa_aparece_nos_dias_estendidos(self):
        """
        Aluno nascido em 01/05/2026 ainda está em "00 meses" em 25/05/2026.
        A extensão deve incluí-lo normalmente nos dias futuros.
        """
        escola = EscolaFactory()
        aluno = AlunoFactory(escola=escola, data_nascimento=datetime.date(2026, 5, 1))
        periodo = PeriodoEscolarFactory(nome="INTEGRAL")
        faixa_00meses = FaixaEtariaFactory(inicio=0, fim=1)

        logs = [
            LogAlunosMatriculadosFaixaEtariaDiaFactory(
                escola=escola,
                periodo_escolar=periodo,
                faixa_etaria=faixa_00meses,
                data=datetime.date(2026, 5, dia),
            )
            for dia in range(1, 25)  # dias 1-24
        ]
        for log in logs:
            _cria_log_aluno_por_dia(log, aluno)

        ultimo_log = logs[-1]  # dia 24
        queryset = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
            pk__in=[l.pk for l in logs]
        )

        aluno_str = _formata_nome_aluno(aluno)
        alunos_por_dia = [aluno_str]
        dias = [{"dia": "24", "alunos_por_dia": list(alunos_por_dia)}]

        trata_dados_futuro_mes_atual(
            queryset,
            ultimo_log,
            dias,
            alunos_por_dia,
            31,
            {"mes_ano": "05_2026"},
        )

        dias_estendidos = [d for d in dias if int(d["dia"]) >= 25]
        assert len(dias_estendidos) == 7  # dias 25-31
        for dia_dict in dias_estendidos:
            assert (
                aluno_str in dia_dict["alunos_por_dia"]
            ), f"Aluno deveria aparecer em 'dia={dia_dict['dia']}' de '00 meses'"
