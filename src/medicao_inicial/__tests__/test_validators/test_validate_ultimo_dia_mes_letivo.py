import calendar
import datetime

import pytest
from django.utils import timezone

from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    ValorMedicao,
)
from src.medicao_inicial.validators import validate_ultimo_dia_mes_letivo

pytestmark = pytest.mark.django_db


def _get_mes_ano():
    return 4, 2025


def _ultimo_dia(mes, ano):
    return calendar.monthrange(ano, mes)[1]


def _dia_str(dia):
    return f"{dia:02d}"


def _setup_solicitacao(
    solicitacao_medicao_inicial_factory,
    dia_calendario_factory,
    escola,
    mes,
    ano,
    ultimo_dia_eh_letivo,
):
    solicitacao = solicitacao_medicao_inicial_factory.create(
        escola=escola,
        mes=f"{mes:02d}",
        ano=str(ano),
    )
    if ultimo_dia_eh_letivo is not None:
        dia_calendario_factory.create(
            escola=escola,
            data=datetime.date(ano, mes, _ultimo_dia(mes, ano)),
            dia_letivo=ultimo_dia_eh_letivo,
        )
    return solicitacao


def _cria_medicao_e_valores(solicitacao, periodo_escolar_factory, dia, escola=None):
    periodo = periodo_escolar_factory.create(nome="MANHA")
    if escola:
        _tornar_escola_com_alunos_regulares(
            escola, periodo, int(solicitacao.mes), int(solicitacao.ano)
        )
    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    if dia is not None:
        categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)
        ValorMedicao.objects.create(
            medicao=medicao,
            categoria_medicao=categoria,
            dia=_dia_str(dia),
            nome_campo="matriculados",
            valor="10",
        )
    return medicao


def _tornar_escola_com_alunos_regulares(escola, periodo, mes, ano):
    from src.escola.models import (
        AlunosMatriculadosPeriodoEscola,
        LogAlunosMatriculadosPeriodoEscola,
    )

    if not AlunosMatriculadosPeriodoEscola.objects.filter(
        escola=escola, periodo_escolar=periodo
    ).exists():
        AlunosMatriculadosPeriodoEscola.objects.create(
            escola=escola,
            periodo_escolar=periodo,
            quantidade_alunos=10,
            tipo_turma="REGULAR",
        )

    log = LogAlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=periodo,
        quantidade_alunos=10,
        tipo_turma="REGULAR",
    )
    data_log = timezone.make_aware(datetime.datetime(ano, mes, 1, 12))
    LogAlunosMatriculadosPeriodoEscola.objects.filter(pk=log.pk).update(
        criado_em=data_log
    )


class TestValidateUltimoDiaMesLetivo:

    def test_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1
        assert (
            f"O último dia do mês ({_dia_str(ultimo)}/{mes:02d}) é letivo"
            in result[0]["erro"]
        )

    def test_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ultimo_dia_nao_letivo(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=False,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ultimo_dia_sem_calendario(
        self,
        solicitacao_medicao_inicial_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            None,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=None,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_emei_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_emei,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_emei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_emei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_emei_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_emei,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_emei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_emei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_cemei_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cemei,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cemei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_cemei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_cemei_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cemei,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cemei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_cemei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_cei_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cei,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_cei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_cei_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cei,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_cei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ceu_gestao_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_gestao,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_gestao,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(solicitacao, periodo_escolar_factory, dia=None)
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ceu_gestao_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_gestao,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_gestao,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(solicitacao, periodo_escolar_factory, dia=ultimo)
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_emebs_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_emebs,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_emebs,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_emebs
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_emebs_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_emebs,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_emebs,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_emebs
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_multiplos_periodos_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        periodo_manha = periodo_escolar_factory.create(nome="MANHA")
        periodo_tarde = periodo_escolar_factory.create(nome="TARDE")
        _tornar_escola_com_alunos_regulares(escola, periodo_manha, mes, ano)
        _tornar_escola_com_alunos_regulares(escola, periodo_tarde, mes, ano)
        categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)
        for periodo in [periodo_manha, periodo_tarde]:
            medicao = Medicao.objects.create(
                solicitacao_medicao_inicial=solicitacao,
                periodo_escolar=periodo,
            )
            ValorMedicao.objects.create(
                medicao=medicao,
                categoria_medicao=categoria,
                dia="01",
                nome_campo="lanche",
                valor="10",
            )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 2
        for erro in result:
            assert (
                f"O último dia do mês ({_dia_str(ultimo)}/{mes:02d}) é letivo"
                in erro["erro"]
            )

    def test_ultimo_dia_fim_de_semana_nao_valida(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = 5, 2025
        ultimo = 31
        assert datetime.date(ano, mes, ultimo).weekday() >= 5
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ultimo_dia_letivo_com_campo_auto_criado_apenas(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        periodo = periodo_escolar_factory.create(nome="MANHA")
        medicao = Medicao.objects.create(
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=periodo,
        )
        categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)
        ValorMedicao.objects.create(
            medicao=medicao,
            categoria_medicao=categoria,
            dia=_dia_str(_ultimo_dia(mes, ano)),
            nome_campo="matriculados",
            valor="0",
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_exclui_medicoes_de_grupo(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        grupo_programas_e_projetos,
        grupo_etec,
        grupo_solicitacoes_alimentacao,
        escola,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)
        periodo = periodo_escolar_factory.create(nome="MANHA")
        medicao_manha = Medicao.objects.create(
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=periodo,
        )
        ValorMedicao.objects.create(
            medicao=medicao_manha,
            categoria_medicao=categoria,
            dia=_dia_str(ultimo),
            nome_campo="lanche",
            valor="10",
        )
        for grupo in [
            grupo_programas_e_projetos,
            grupo_etec,
            grupo_solicitacoes_alimentacao,
        ]:
            Medicao.objects.create(
                solicitacao_medicao_inicial=solicitacao,
                grupo=grupo,
            )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_cieja_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cieja,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cieja,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_cieja
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_cieja_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cieja,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cieja,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_cieja
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_cmct_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cmct,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cmct,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_cmct
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_cmct_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cmct,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cmct,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_cmct
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ceu_cemei_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_cemei,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_cemei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_ceu_cemei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_ceu_cemei_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_cemei,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_cemei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_ceu_cemei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_ceu_emei_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_emei,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_emei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_ceu_emei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_ceu_emei_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_ceu_emei,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_ceu_emei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_ceu_emei
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    def test_cci_ultimo_dia_letivo_sem_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cci,
    ):
        mes, ano = _get_mes_ano()
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cci,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=None, escola=escola_cci
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 1

    def test_cci_ultimo_dia_letivo_com_preenchimento(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cci,
    ):
        mes, ano = _get_mes_ano()
        ultimo = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cci,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao, periodo_escolar_factory, dia=ultimo, escola=escola_cci
        )
        lista_erros = []

        result = validate_ultimo_dia_mes_letivo(solicitacao, lista_erros)

        assert len(result) == 0

    @pytest.mark.parametrize("regular_preenchido", [True, False])
    def test_periodo_sem_alunos_nao_exige_ultimo_dia(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_emei,
        regular_preenchido,
    ):
        mes, ano = 12, 2025
        ultimo_dia = _ultimo_dia(mes, ano)
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_emei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        medicao_regular = _cria_medicao_e_valores(
            solicitacao,
            periodo_escolar_factory,
            dia=ultimo_dia if regular_preenchido else None,
            escola=escola_emei,
        )
        periodo_evento = periodo_escolar_factory.create(nome="NOITE")
        medicao_evento = Medicao.objects.create(
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=periodo_evento,
        )
        categoria, _ = CategoriaMedicao.objects.get_or_create(
            nome=CategoriaMedicao.ALIMENTACAO
        )
        ValorMedicao.objects.create(
            medicao=medicao_evento,
            categoria_medicao=categoria,
            dia="20",
            nome_campo="refeicao",
            valor="100",
        )

        erros = validate_ultimo_dia_mes_letivo(solicitacao, [])

        if regular_preenchido:
            assert erros == []
        else:
            assert erros == [
                {
                    "periodo_escolar": medicao_regular.nome_periodo_grupo,
                    "erro": (
                        "O último dia do mês (31/12) é letivo "
                        "e não foi preenchido."
                    ),
                }
            ]

    def test_preserva_validacao_de_grupo_cemei(
        self,
        solicitacao_medicao_inicial_factory,
        dia_calendario_factory,
        periodo_escolar_factory,
        escola_cemei,
    ):
        mes, ano = 12, 2025
        solicitacao = _setup_solicitacao(
            solicitacao_medicao_inicial_factory,
            dia_calendario_factory,
            escola_cemei,
            mes,
            ano,
            ultimo_dia_eh_letivo=True,
        )
        _cria_medicao_e_valores(
            solicitacao,
            periodo_escolar_factory,
            dia=31,
            escola=escola_cemei,
        )
        grupo = GrupoMedicao.objects.create(nome="Infantil MANHA")
        medicao = Medicao.objects.create(
            solicitacao_medicao_inicial=solicitacao,
            grupo=grupo,
        )

        erros = validate_ultimo_dia_mes_letivo(solicitacao, [])

        assert erros == [
            {
                "periodo_escolar": medicao.nome_periodo_grupo,
                "erro": (
                    "O último dia do mês (31/12) é letivo "
                    "e não foi preenchido."
                ),
            }
        ]
