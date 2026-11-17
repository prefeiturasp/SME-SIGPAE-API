from datetime import date

import pytest
from model_bakery import baker

from src.dados_comuns.constants import StringsValoresMedicao
from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    ClassificacaoDieta,
)
from src.medicao_inicial.api.serializers_create import (
    SolicitacaoMedicaoInicialCreateSerializer,
)
from src.medicao_inicial.models import CategoriaMedicao

pytestmark = pytest.mark.django_db

MES = 9
ANO = 2023


def _prepara_periodo_com_alunos(escola, periodo_escolar):
    """Garante que o período apareça em ``periodos_escolares`` da escola."""
    baker.make(
        "AlunosMatriculadosPeriodoEscola",
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=10,
    )
    log = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=10,
    )
    log.criado_em = date(ANO, MES, 1)
    log.save()


def _cria_solicitacao(escola):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes=str(MES),
        ano=str(ANO),
    )


def _cria_medicao(solicitacao, periodo_escolar):
    return baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar,
    )


def _cria_categoria_alimentacao():
    return CategoriaMedicao.objects.get_or_create(nome=CategoriaMedicao.ALIMENTACAO)[0]


def _cria_log_matriculados_faixa(escola, periodo, faixa, dia, quantidade):
    return baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola,
        periodo_escolar=periodo,
        faixa_etaria=faixa,
        data=date(ANO, MES, dia),
        quantidade=quantidade,
    )


def _cria_log_dieta_autorizada(escola, periodo, classificacao, dia, quantidade):
    return LogQuantidadeDietasAutorizadas.objects.create(
        escola=escola,
        periodo_escolar=periodo,
        classificacao=classificacao,
        data=date(ANO, MES, dia),
        quantidade=quantidade,
    )


def _cria_log_dieta_autorizada_cei(
    escola, periodo, classificacao, faixa, dia, quantidade
):
    return LogQuantidadeDietasAutorizadasCEI.objects.create(
        escola=escola,
        periodo_escolar=periodo,
        classificacao=classificacao,
        faixa_etaria=faixa,
        data=date(ANO, MES, dia),
        quantidade=quantidade,
    )


def test_cria_valores_matriculados_emef_usa_log_mais_recente_do_dia(
    escola, periodo_escolar_manha
):
    _prepara_periodo_com_alunos(escola, periodo_escolar_manha)
    log_recente = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar_manha,
        quantidade_alunos=25,
    )
    log_recente.criado_em = date(ANO, MES, 5)
    log_recente.save()
    solicitacao = _cria_solicitacao(escola)
    categoria = _cria_categoria_alimentacao()

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_alunos_matriculados_emef_emei(
        solicitacao
    )

    medicao = solicitacao.medicoes.get(periodo_escolar=periodo_escolar_manha)
    valores = medicao.valores_medicao.filter(
        categoria_medicao=categoria,
        nome_campo=StringsValoresMedicao.MATRICULADOS.value,
    )
    assert valores.count() == 30
    assert valores.get(dia="05").valor == "25"
    assert valores.get(dia="02").valor == "0"


def test_nao_sobrescreve_valor_matriculados_emef_existente(
    escola, periodo_escolar_manha
):
    _prepara_periodo_com_alunos(escola, periodo_escolar_manha)
    solicitacao = _cria_solicitacao(escola)
    categoria = _cria_categoria_alimentacao()
    medicao = _cria_medicao(solicitacao, periodo_escolar_manha)
    baker.make(
        "ValorMedicao",
        medicao=medicao,
        categoria_medicao=categoria,
        dia="05",
        nome_campo=StringsValoresMedicao.MATRICULADOS.value,
        valor="99",
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_alunos_matriculados_emef_emei(
        solicitacao
    )

    valores_dia = medicao.valores_medicao.filter(
        categoria_medicao=categoria,
        nome_campo=StringsValoresMedicao.MATRICULADOS.value,
        dia="05",
    )
    assert valores_dia.count() == 1
    assert valores_dia.first().valor == "99"


def test_cria_valores_matriculados_cei_por_faixa_etaria(
    escola_cei, periodo_escolar, faixa_etaria
):
    _prepara_periodo_com_alunos(escola_cei, periodo_escolar)
    outra_faixa = baker.make("FaixaEtaria", inicio=5, fim=8)
    _cria_log_matriculados_faixa(
        escola_cei, periodo_escolar, faixa_etaria, dia=5, quantidade=7
    )
    _cria_log_matriculados_faixa(
        escola_cei, periodo_escolar, outra_faixa, dia=5, quantidade=3
    )
    baker.make(
        "LogAlunosMatriculadosFaixaEtariaDia",
        escola=escola_cei,
        periodo_escolar=periodo_escolar,
        faixa_etaria=faixa_etaria,
        data=date(ANO, 10, 5),
        quantidade=100,
    )
    solicitacao = _cria_solicitacao(escola_cei)
    categoria = _cria_categoria_alimentacao()

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_alunos_matriculados_cei(
        solicitacao
    )

    medicao = solicitacao.medicoes.get(periodo_escolar=periodo_escolar)
    valores_dia_5 = medicao.valores_medicao.filter(
        categoria_medicao=categoria,
        nome_campo=StringsValoresMedicao.MATRICULADOS.value,
        dia="05",
    )
    assert valores_dia_5.count() == 2
    assert valores_dia_5.get(faixa_etaria=faixa_etaria).valor == "7"
    assert valores_dia_5.get(faixa_etaria=outra_faixa).valor == "3"
    assert not medicao.valores_medicao.filter(dia="05", valor="100").exists()


def test_cria_valores_dietas_autorizadas_emef_tipo_b(
    escola, periodo_escolar_manha, categoria_dieta_b
):
    _prepara_periodo_com_alunos(escola, periodo_escolar_manha)
    solicitacao = _cria_solicitacao(escola)
    medicao = _cria_medicao(solicitacao, periodo_escolar_manha)
    classificacao = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO B - SEM LACTOSE"
    )
    _cria_log_dieta_autorizada(
        escola, periodo_escolar_manha, classificacao, dia=5, quantidade=7
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_dietas_autorizadas_emef_emei(
        solicitacao
    )

    valores = medicao.valores_medicao.filter(
        categoria_medicao=categoria_dieta_b,
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
    )
    assert valores.count() == 30
    assert valores.get(dia="05").valor == "7"
    assert valores.get(dia="06").valor == "0"


def test_cria_valores_dietas_autorizadas_emef_enteral_e_aminoacidos(
    escola, periodo_escolar_manha
):
    _prepara_periodo_com_alunos(escola, periodo_escolar_manha)
    categoria = baker.make(
        "CategoriaMedicao",
        nome=CategoriaMedicao.DIETA_ESPECIAL_TIPO_A_ENTERAL_RESTRICAO_AMINOACIDOS,
    )
    solicitacao = _cria_solicitacao(escola)
    medicao = _cria_medicao(solicitacao, periodo_escolar_manha)
    classificacao_enteral = ClassificacaoDieta.objects.create(
        nome=ClassificacaoDieta.TIPO_A_ENTERAL
    )
    classificacao_aminoacidos = ClassificacaoDieta.objects.create(
        nome=ClassificacaoDieta.TIPO_A_RESTRICAO_AMINOACIDOS
    )
    _cria_log_dieta_autorizada(
        escola, periodo_escolar_manha, classificacao_enteral, dia=5, quantidade=4
    )
    _cria_log_dieta_autorizada(
        escola,
        periodo_escolar_manha,
        classificacao_aminoacidos,
        dia=5,
        quantidade=3,
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_dietas_autorizadas_emef_emei(
        solicitacao
    )

    valor_dia_5 = medicao.valores_medicao.get(
        categoria_medicao=categoria,
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        dia="05",
    )
    assert valor_dia_5.valor == "7"


def test_nao_sobrescreve_valor_dieta_autorizada_emef_existente(
    escola, periodo_escolar_manha, categoria_dieta_b
):
    _prepara_periodo_com_alunos(escola, periodo_escolar_manha)
    solicitacao = _cria_solicitacao(escola)
    medicao = _cria_medicao(solicitacao, periodo_escolar_manha)
    classificacao = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO B - SEM LACTOSE"
    )
    _cria_log_dieta_autorizada(
        escola, periodo_escolar_manha, classificacao, dia=5, quantidade=7
    )
    baker.make(
        "ValorMedicao",
        medicao=medicao,
        categoria_medicao=categoria_dieta_b,
        dia="05",
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        valor="99",
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_dietas_autorizadas_emef_emei(
        solicitacao
    )

    valores_dia = medicao.valores_medicao.filter(
        categoria_medicao=categoria_dieta_b,
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        dia="05",
    )
    assert valores_dia.count() == 1
    assert valores_dia.first().valor == "99"


def test_cria_valores_dietas_autorizadas_cei_tipo_a_soma_por_faixa(
    escola_cei, periodo_escolar, faixa_etaria, categoria_dieta_a
):
    _prepara_periodo_com_alunos(escola_cei, periodo_escolar)
    solicitacao = _cria_solicitacao(escola_cei)
    medicao = _cria_medicao(solicitacao, periodo_escolar)
    outra_faixa = baker.make("FaixaEtaria", inicio=5, fim=8)
    classificacao_1 = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO A - SEM LACTOSE"
    )
    classificacao_2 = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO A - APENAS FRUTA"
    )
    _cria_log_dieta_autorizada_cei(
        escola_cei, periodo_escolar, classificacao_1, faixa_etaria, 5, 4
    )
    _cria_log_dieta_autorizada_cei(
        escola_cei, periodo_escolar, classificacao_2, faixa_etaria, 5, 3
    )
    _cria_log_dieta_autorizada_cei(
        escola_cei, periodo_escolar, classificacao_1, outra_faixa, 5, 10
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_dietas_autorizadas_cei(
        solicitacao
    )

    valores_dia_5 = medicao.valores_medicao.filter(
        categoria_medicao=categoria_dieta_a,
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        dia="05",
    )
    assert valores_dia_5.count() == 2
    assert valores_dia_5.get(faixa_etaria=faixa_etaria).valor == "7"
    assert valores_dia_5.get(faixa_etaria=outra_faixa).valor == "10"


def test_nao_sobrescreve_valor_dieta_autorizada_cei_existente(
    escola_cei, periodo_escolar, faixa_etaria, categoria_dieta_a
):
    _prepara_periodo_com_alunos(escola_cei, periodo_escolar)
    solicitacao = _cria_solicitacao(escola_cei)
    medicao = _cria_medicao(solicitacao, periodo_escolar)
    classificacao = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO A - SEM LACTOSE"
    )
    _cria_log_dieta_autorizada_cei(
        escola_cei, periodo_escolar, classificacao, faixa_etaria, 5, 7
    )
    baker.make(
        "ValorMedicao",
        medicao=medicao,
        categoria_medicao=categoria_dieta_a,
        dia="05",
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        valor="99",
        faixa_etaria=faixa_etaria,
    )

    SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_dietas_autorizadas_cei(
        solicitacao
    )

    valores_dia = medicao.valores_medicao.filter(
        categoria_medicao=categoria_dieta_a,
        nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
        dia="05",
        faixa_etaria=faixa_etaria,
    )
    assert valores_dia.count() == 1
    assert valores_dia.first().valor == "99"


def test_valores_inclusoes_continuas_somam_dias_da_semana_ativos():
    escola = baker.make("Escola")
    solicitacao = _cria_solicitacao(escola)
    motivo = baker.make("MotivoInclusaoContinua", nome="Programas/Projetos Contínuos")
    inclusao_segunda = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=date(ANO, MES, 1),
        data_final=date(ANO, MES, 30),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    inclusao_todos_os_dias = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        data_inicial=date(ANO, MES, 1),
        data_final=date(ANO, MES, 30),
        motivo=motivo,
        status="CODAE_AUTORIZADO",
    )
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_segunda,
        periodo_escolar=periodo,
        numero_alunos=10,
        dias_semana=[0],
        encerrado_a_partir_de=None,
        cancelado=False,
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_todos_os_dias,
        periodo_escolar=periodo,
        numero_alunos=5,
        dias_semana=[0, 1, 2, 3, 4, 5, 6],
        encerrado_a_partir_de=None,
        cancelado=False,
    )

    valores_por_dia = SolicitacaoMedicaoInicialCreateSerializer()._valores_numero_alunos_inclusoes_continuas_por_dia(
        solicitacao,
        escola.inclusoes_alimentacao_continua.all(),
        30,
    )

    # Setembro de 2023 tem segundas-feiras nos dias 4, 11, 18 e 25.
    assert valores_por_dia[4] == 15
    assert valores_por_dia[5] == 5
    assert set(valores_por_dia.keys()) == set(range(1, 31))
