import datetime

import pytest
from model_bakery import baker

from src.escola.models import DiaSuspensaoAtividades
from src.medicao_inicial.models import (
    Medicao,
    ValorMedicao,
)
from src.medicao_inicial.validators import (
    get_dias_com_suspensao,
    get_lista_dias_letivos,
    validate_lancamento_alimentacoes_medicao,
    validate_lancamento_dietas_cei,
    validate_lancamento_inclusoes,
    validate_medicao_cemei,
    validate_solicitacoes_etec,
    validate_solicitacoes_programas_e_projetos,
)

pytestmark = pytest.mark.django_db


MES = 5
ANO = 2025
DIA_SUSPENSO = 5  # segunda-feira útil em maio/2025


def _dia_str(dia):
    return f"{dia:02d}"


def _criar_dia_suspensao(escola, dia, mes=MES, ano=ANO):
    edital = escola.lote.contratos_do_lote.first().edital
    return DiaSuspensaoAtividades.objects.create(
        data=datetime.date(ano, mes, dia),
        tipo_unidade=escola.tipo_unidade,
        edital=edital,
    )


def _criar_dia_letivo(escola, dia, mes=MES, ano=ANO, periodo_escolar=None):
    return baker.make(
        "escola.DiaCalendario",
        escola=escola,
        data=datetime.date(ano, mes, dia),
        dia_letivo=True,
        periodo_escolar=periodo_escolar,
    )


def _criar_log_matriculados(
    escola, periodo_escolar, dia, mes=MES, ano=ANO, quantidade=10
):
    log = baker.make(
        "escola.LogAlunosMatriculadosPeriodoEscola",
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=quantidade,
        tipo_turma="REGULAR",
    )
    log.criado_em = datetime.datetime(ano, mes, dia, 12, 0)
    log.save()
    return log


def _criar_alunos_matriculados(escola, periodo_escolar, quantidade=10):
    return baker.make(
        "escola.AlunosMatriculadosPeriodoEscola",
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=quantidade,
        tipo_turma="REGULAR",
    )


def _criar_solicitacao(escola, mes=MES, ano=ANO):
    tipo_contagem = baker.make("medicao_inicial.TipoContagemAlimentacao", nome="Fichas")
    solicitacao = baker.make(
        "medicao_inicial.SolicitacaoMedicaoInicial",
        mes=f"{mes:02d}",
        ano=str(ano),
        escola=escola,
    )
    solicitacao.tipos_contagem_alimentacao.set([tipo_contagem])
    return solicitacao


def _criar_vinculo_alimentacao(tipo_unidade, periodo_escolar, tipos_alimentacao):
    vinculo = baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=tipo_unidade,
        periodo_escolar=periodo_escolar,
    )
    vinculo.tipos_alimentacao.set(tipos_alimentacao)
    return vinculo


def _criar_edital_e_contrato_para_escola(escola):
    edital = baker.make("terceirizada.Edital", numero="Edital Teste Suspensao")
    contrato = baker.make(
        "terceirizada.Contrato",
        edital=edital,
        encerrado=False,
    )
    contrato.lotes.add(escola.lote)
    return edital, contrato


# ---------------------------- get_dias_com_suspensao ----------------------------


def test_get_dias_com_suspensao_retorna_dias_formatado(escola, periodo_escolar_manha):
    _criar_edital_e_contrato_para_escola(escola)
    _criar_log_matriculados(escola, periodo_escolar_manha, DIA_SUSPENSO)
    solicitacao = _criar_solicitacao(escola)
    _criar_dia_suspensao(escola, DIA_SUSPENSO)

    dias = get_dias_com_suspensao(solicitacao)

    assert dias == [_dia_str(DIA_SUSPENSO)]


def test_get_dias_com_suspensao_vazio_sem_dia_suspensao(escola, periodo_escolar_manha):
    _criar_edital_e_contrato_para_escola(escola)
    solicitacao = _criar_solicitacao(escola)

    dias = get_dias_com_suspensao(solicitacao)

    assert dias == []


def test_get_dias_com_suspensao_ignora_edital_nao_vinculado_a_escola(
    escola, periodo_escolar_manha
):
    _criar_edital_e_contrato_para_escola(escola)
    solicitacao = _criar_solicitacao(escola)
    edital_outro = baker.make("terceirizada.Edital", numero="Edital Outro")
    DiaSuspensaoAtividades.objects.create(
        data=datetime.date(ANO, MES, DIA_SUSPENSO),
        tipo_unidade=escola.tipo_unidade,
        edital=edital_outro,
    )

    dias = get_dias_com_suspensao(solicitacao)

    assert dias == []


# ---------------------------- get_lista_dias_letivos ----------------------------


def test_get_lista_dias_letivos_desconsidera_dia_suspensao(
    escola, periodo_escolar_manha
):
    _criar_edital_e_contrato_para_escola(escola)
    _criar_dia_letivo(escola, DIA_SUSPENSO)
    _criar_log_matriculados(escola, periodo_escolar_manha, DIA_SUSPENSO)
    _criar_dia_suspensao(escola, DIA_SUSPENSO)
    solicitacao = _criar_solicitacao(escola)

    dias = get_lista_dias_letivos(solicitacao, escola, periodo_escolar_manha)

    assert _dia_str(DIA_SUSPENSO) not in dias


def test_get_lista_dias_letivos_sem_dia_suspensao_mantem_dia(
    escola, periodo_escolar_manha
):
    _criar_edital_e_contrato_para_escola(escola)
    _criar_dia_letivo(escola, DIA_SUSPENSO)
    _criar_log_matriculados(escola, periodo_escolar_manha, DIA_SUSPENSO)
    solicitacao = _criar_solicitacao(escola)

    dias = get_lista_dias_letivos(solicitacao, escola, periodo_escolar_manha)

    assert _dia_str(DIA_SUSPENSO) in dias


# ---------------------------- valida_finalizar_medicao_emef_emei ----------------------------


def _setup_emef_emei(escola, periodo_escolar_manha, tipo_alimentacao_refeicao):
    _criar_edital_e_contrato_para_escola(escola)
    _criar_alunos_matriculados(escola, periodo_escolar_manha)
    _criar_log_matriculados(escola, periodo_escolar_manha, DIA_SUSPENSO)
    _criar_dia_letivo(escola, DIA_SUSPENSO)
    _criar_vinculo_alimentacao(
        escola.tipo_unidade, periodo_escolar_manha, [tipo_alimentacao_refeicao]
    )
    solicitacao = _criar_solicitacao(escola)
    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar_manha,
    )
    return solicitacao, medicao


def test_valida_finalizar_medicao_emef_emei_desconsidera_dia_suspensao(
    escola,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
    categoria_medicao,
):
    """Dia com DiaSuspensaoAtividades não deve gerar erro de falta de lançamento."""
    solicitacao, medicao = _setup_emef_emei(
        escola, periodo_escolar_manha, tipo_alimentacao_refeicao
    )
    _criar_dia_suspensao(escola, DIA_SUSPENSO)

    lista_erros = validate_lancamento_alimentacoes_medicao(solicitacao, [])

    assert lista_erros == []


# ---------------------------- valida_finalizar_medicao_cemei ----------------------------


def _setup_cemei(
    escola_cemei,
    faixa_etaria,
    categoria_medicao,
    periodo_escolar_integral,
    make_log_matriculados_faixa_etaria_dia,
):
    _criar_edital_e_contrato_para_escola(escola_cemei)
    solicitacao = _criar_solicitacao(escola_cemei)
    _criar_dia_letivo(escola_cemei, DIA_SUSPENSO)
    make_log_matriculados_faixa_etaria_dia(
        DIA_SUSPENSO, escola_cemei, solicitacao, periodo_escolar_integral
    )
    Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar_integral,
    )
    return solicitacao


def test_valida_finalizar_medicao_cemei_desconsidera_dia_suspensao(
    escola_cemei,
    faixa_etaria,
    categoria_medicao,
    periodo_escolar_integral,
    make_log_matriculados_faixa_etaria_dia,
):
    """Dia com DiaSuspensaoAtividades não deve gerar erro em CEMEI."""
    solicitacao = _setup_cemei(
        escola_cemei,
        faixa_etaria,
        categoria_medicao,
        periodo_escolar_integral,
        make_log_matriculados_faixa_etaria_dia,
    )
    _criar_dia_suspensao(escola_cemei, DIA_SUSPENSO)

    lista_erros = validate_medicao_cemei(solicitacao)

    assert lista_erros == []


# ---------------------------- valida_finalizar_medicao_cei ----------------------------


def _setup_cei(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    classificacao_dieta_tipo_a,
):
    _criar_edital_e_contrato_para_escola(escola_cei)
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_dia_letivo(escola_cei, DIA_SUSPENSO)
    faixa = faixas_etarias_ativas[2]
    baker.make(
        "escola.LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola_cei,
        data=datetime.date(ANO, MES, DIA_SUSPENSO),
        faixa_etaria=faixa,
        periodo_escolar=periodo_escolar_integral,
        quantidade=10,
    )
    baker.make(
        "dieta_especial.LogQuantidadeDietasAutorizadasCEI",
        escola=escola_cei,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=faixa,
        quantidade=2,
        data=datetime.date(ANO, MES, DIA_SUSPENSO),
        classificacao=classificacao_dieta_tipo_a,
    )
    Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar_integral,
    )
    return solicitacao


def test_valida_finalizar_medicao_cei_desconsidera_dia_suspensao_dietas(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    classificacao_dieta_tipo_a,
):
    """Dia com DiaSuspensaoAtividades não deve gerar erro em CEI (dietas)."""
    solicitacao = _setup_cei(
        escola_cei,
        faixas_etarias_ativas,
        periodo_escolar_integral,
        classificacao_dieta_tipo_a,
    )
    _criar_dia_suspensao(escola_cei, DIA_SUSPENSO)

    lista_erros = validate_lancamento_dietas_cei(solicitacao, [])

    assert lista_erros == []


# ---------------------------- valida_finalizar_medicao_escola_sem_alunos_regulares ----------------------------


def _setup_escola_sem_alunos_regulares(
    escola_cmct,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
):
    _criar_edital_e_contrato_para_escola(escola_cmct)
    solicitacao = _criar_solicitacao(escola_cmct)
    grupo_inclusao = baker.make(
        "inclusao_alimentacao.GrupoInclusaoAlimentacaoNormal",
        escola=escola_cmct,
        rastro_escola=escola_cmct,
        rastro_lote=escola_cmct.lote,
        rastro_dre=escola_cmct.lote.diretoria_regional,
        status="CODAE_AUTORIZADO",
    )
    inclusao = baker.make(
        "inclusao_alimentacao.InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao,
        data=datetime.date(ANO, MES, DIA_SUSPENSO),
    )
    qt_periodo = baker.make(
        "inclusao_alimentacao.QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao,
        periodo_escolar=periodo_escolar_manha,
        numero_alunos=10,
    )
    qt_periodo.tipos_alimentacao.add(tipo_alimentacao_refeicao)
    return solicitacao, inclusao


def test_valida_finalizar_medicao_escola_sem_alunos_regulares_desconsidera_dia_suspensao(
    escola_cmct,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
    categoria_medicao,
):
    """Inclusão em dia suspenso não deve gerar erro de falta de lançamento."""
    solicitacao, inclusao = _setup_escola_sem_alunos_regulares(
        escola_cmct, periodo_escolar_manha, tipo_alimentacao_refeicao
    )
    _criar_dia_suspensao(escola_cmct, DIA_SUSPENSO)

    lista_erros = validate_lancamento_inclusoes(solicitacao, [])

    assert lista_erros == []


# ---------------------------- valida_finalizar_medicao_emebs ----------------------------


def _setup_emebs(
    escola_emebs,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
    categoria_medicao,
):
    _criar_edital_e_contrato_para_escola(escola_emebs)
    _criar_dia_letivo(escola_emebs, DIA_SUSPENSO)
    _criar_log_matriculados(escola_emebs, periodo_escolar_manha, DIA_SUSPENSO)
    _criar_alunos_matriculados(escola_emebs, periodo_escolar_manha)
    _criar_vinculo_alimentacao(
        escola_emebs.tipo_unidade, periodo_escolar_manha, [tipo_alimentacao_refeicao]
    )
    log = baker.make(
        "escola.LogAlunosMatriculadosPeriodoEscola",
        escola=escola_emebs,
        periodo_escolar=periodo_escolar_manha,
        quantidade_alunos=10,
        tipo_turma="REGULAR",
        infantil_ou_fundamental="INFANTIL",
    )
    log.criado_em = datetime.datetime(ANO, MES, DIA_SUSPENSO, 12, 0)
    log.save()
    solicitacao = _criar_solicitacao(escola_emebs)
    Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar_manha,
    )
    return solicitacao


def test_valida_finalizar_medicao_emebs_desconsidera_dia_suspensao(
    escola_emebs,
    periodo_escolar_manha,
    tipo_alimentacao_refeicao,
    categoria_medicao,
):
    """Dia com DiaSuspensaoAtividades não deve gerar erro em EMEBS."""
    solicitacao = _setup_emebs(
        escola_emebs,
        periodo_escolar_manha,
        tipo_alimentacao_refeicao,
        categoria_medicao,
    )
    _criar_dia_suspensao(escola_emebs, DIA_SUSPENSO)

    from src.medicao_inicial.validators import (
        validate_lancamento_alimentacoes_medicao_emebs,
    )

    lista_erros = validate_lancamento_alimentacoes_medicao_emebs(solicitacao, [])

    assert lista_erros == []


# ---------------------------- valida_solicitacoes_programas_e_projetos / etec ----------------------------


def _setup_programas_e_projetos(
    escola, periodo_escolar_manha, grupo_programas_e_projetos
):
    _criar_edital_e_contrato_para_escola(escola)
    _criar_dia_letivo(escola, DIA_SUSPENSO)
    motivo = baker.make(
        "inclusao_alimentacao.MotivoInclusaoContinua", nome="Programas e Projetos"
    )
    inclusao = baker.make(
        "inclusao_alimentacao.InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.lote.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        motivo=motivo,
        data_inicial=datetime.date(ANO, MES, 1),
        data_final=datetime.date(ANO, MES, 31),
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "inclusao_alimentacao.QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_escolar_manha,
        numero_alunos=10,
        dias_semana=[0, 1, 2, 3, 4],
    )
    solicitacao = _criar_solicitacao(escola)
    Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo_programas_e_projetos,
    )
    return solicitacao


def test_valida_solicitacoes_programas_e_projetos_desconsidera_dia_suspensao(
    escola,
    periodo_escolar_manha,
    grupo_programas_e_projetos,
    categoria_medicao,
):
    """Dia suspenso não deve gerar erro em programas e projetos."""
    solicitacao = _setup_programas_e_projetos(
        escola, periodo_escolar_manha, grupo_programas_e_projetos
    )
    _criar_dia_suspensao(escola, DIA_SUSPENSO)

    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, [])

    assert all("Restam dias" not in erro.get("erro", "") for erro in lista_erros)


def test_valida_solicitacoes_etec_desconsidera_dia_suspensao(
    escola, periodo_escolar_manha, grupo_etec, categoria_medicao
):
    """Dia suspenso não deve gerar erro em ETEC."""
    _criar_edital_e_contrato_para_escola(escola)
    _criar_dia_letivo(escola, DIA_SUSPENSO)
    motivo = baker.make("inclusao_alimentacao.MotivoInclusaoContinua", nome="ETEC")
    inclusao = baker.make(
        "inclusao_alimentacao.InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.lote.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        motivo=motivo,
        data_inicial=datetime.date(ANO, MES, 1),
        data_final=datetime.date(ANO, MES, 31),
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "inclusao_alimentacao.QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=periodo_escolar_manha,
        numero_alunos=10,
        dias_semana=[0, 1, 2, 3, 4],
    )
    solicitacao = _criar_solicitacao(escola)
    Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo_etec,
    )
    _criar_dia_suspensao(escola, DIA_SUSPENSO)

    lista_erros = validate_solicitacoes_etec(solicitacao, [])

    assert all("Restam dias" not in erro.get("erro", "") for erro in lista_erros)
