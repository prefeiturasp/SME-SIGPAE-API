import datetime

import pytest
from model_bakery import baker

from src.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from src.inclusao_alimentacao.fixtures.factories.base_factory import (
    MotivoInclusaoNormalFactory,
)
from src.medicao_inicial.validators import (
    _get_dias_kit_lanche_passeio_cei,
    validate_lancamento_alimentacoes_medicao_cei,
    validate_lancamento_dietas_cei,
    validate_medicao_cemei_cei,
)

pytestmark = pytest.mark.django_db

MES = 5
ANO = 2025
DIA_SABADO = 10
DATA_SABADO = datetime.date(ANO, MES, DIA_SABADO)


def _criar_solicitacao(escola):
    tipo_contagem = baker.make("medicao_inicial.TipoContagemAlimentacao", nome="Fichas")
    solicitacao = baker.make(
        "medicao_inicial.SolicitacaoMedicaoInicial",
        mes=f"{MES:02d}",
        ano=str(ANO),
        escola=escola,
    )
    solicitacao.tipos_contagem_alimentacao.set([tipo_contagem])
    return solicitacao


def _criar_medicao(solicitacao, periodo_escolar_integral):
    return baker.make(
        "medicao_inicial.Medicao",
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar_integral,
    )


def _criar_kit_lanche_cei(escola, faixas_etarias):
    solicitacao_kit_lanche = baker.make(
        "kit_lanche.SolicitacaoKitLanche",
        data=DATA_SABADO,
    )
    kit = baker.make(
        "kit_lanche.SolicitacaoKitLancheCEIAvulsa",
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
    )
    for faixa_etaria in faixas_etarias:
        baker.make(
            "kit_lanche.FaixaEtariaSolicitacaoKitLancheCEIAvulsa",
            solicitacao_kit_lanche_avulsa=kit,
            faixa_etaria=faixa_etaria,
            quantidade=10,
        )
    return kit


def _criar_kit_lanche_cemei_cei(escola, faixas_etarias):
    kit = baker.make(
        "kit_lanche.SolicitacaoKitLancheCEMEI",
        escola=escola,
        data=DATA_SABADO,
        alunos_cei_e_ou_emei="CEI",
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
    )
    solicitacao_cei = baker.make(
        "kit_lanche.SolicitacaoKitLancheCEIdaCEMEI",
        solicitacao_kit_lanche_cemei=kit,
    )
    for faixa_etaria in faixas_etarias:
        baker.make(
            "kit_lanche.FaixasQuantidadesKitLancheCEIdaCEMEI",
            solicitacao_kit_lanche_cei_da_cemei=solicitacao_cei,
            faixa_etaria=faixa_etaria,
            quantidade_alunos=10,
        )
    return kit


def _criar_inclusao_cei(escola):
    inclusao = baker.make(
        "inclusao_alimentacao.InclusaoAlimentacaoDaCEI",
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_lote=escola.lote,
        status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
    )
    baker.make(
        "inclusao_alimentacao.DiasMotivosInclusaoDeAlimentacaoCEI",
        inclusao_cei=inclusao,
        motivo=MotivoInclusaoNormalFactory.create(),
        data=DATA_SABADO,
        cancelado=False,
    )
    return inclusao


def _criar_inclusao_cemei(escola, faixa_etaria, periodo_escolar_integral):
    inclusao = baker.make(
        "inclusao_alimentacao.InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        rastro_lote=escola.lote,
        status=PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
    )
    baker.make(
        "inclusao_alimentacao.DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        motivo=MotivoInclusaoNormalFactory.create(),
        data=DATA_SABADO,
        cancelado=False,
    )
    baker.make(
        "inclusao_alimentacao.QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        faixa_etaria=faixa_etaria,
        quantidade_alunos=10,
        periodo_escolar=periodo_escolar_integral,
    )
    return inclusao


def _criar_frequencia(medicao, categoria_medicao, faixa_etaria, valor="10"):
    return baker.make(
        "medicao_inicial.ValorMedicao",
        medicao=medicao,
        nome_campo="frequencia",
        categoria_medicao=categoria_medicao,
        faixa_etaria=faixa_etaria,
        dia=f"{DIA_SABADO:02d}",
        valor=valor,
    )


def _criar_log_dieta_cei(
    escola,
    periodo_escolar_integral,
    faixa_etaria,
    classificacao_dieta_tipo_a,
    quantidade=2,
):
    return baker.make(
        "dieta_especial.LogQuantidadeDietasAutorizadasCEI",
        escola=escola,
        periodo_escolar=periodo_escolar_integral,
        faixa_etaria=faixa_etaria,
        classificacao=classificacao_dieta_tipo_a,
        quantidade=quantidade,
        data=DATA_SABADO,
    )


def _houve_erro_de_alimentacao(lista_erros):
    return any("alimentações" in erro["erro"] for erro in lista_erros)


def _houve_erro_de_dietas(lista_erros):
    return any("dietas" in erro["erro"] for erro in lista_erros)


def test_cei_kit_lanche_sem_frequencia_gera_erro_na_finalizacao(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    _criar_kit_lanche_cei(escola_cei, [faixas_etarias_ativas[5]])

    lista_erros = validate_lancamento_alimentacoes_medicao_cei(solicitacao, [])

    assert _houve_erro_de_alimentacao(lista_erros)


def test_cei_kit_lanche_com_frequencia_nao_gera_erro_na_finalizacao(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cei)
    medicao = _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cei(escola_cei, [faixa_etaria])
    _criar_frequencia(medicao, categoria_medicao, faixa_etaria)

    lista_erros = validate_lancamento_alimentacoes_medicao_cei(solicitacao, [])

    assert not _houve_erro_de_alimentacao(lista_erros)


def test_cei_kit_lanche_com_uma_faixa_sem_frequencia_gera_erro(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cei)
    medicao = _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_com_frequencia = faixas_etarias_ativas[5]
    _criar_kit_lanche_cei(
        escola_cei,
        [faixa_com_frequencia, faixas_etarias_ativas[6]],
    )
    _criar_frequencia(medicao, categoria_medicao, faixa_com_frequencia)

    lista_erros = validate_lancamento_alimentacoes_medicao_cei(solicitacao, [])

    assert _houve_erro_de_alimentacao(lista_erros)


def test_cei_kit_lanche_somente_menor_de_um_ano_nao_gera_erro(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    _criar_kit_lanche_cei(escola_cei, [faixas_etarias_ativas[0]])

    lista_erros = validate_lancamento_alimentacoes_medicao_cei(solicitacao, [])

    assert not _houve_erro_de_alimentacao(lista_erros)


def test_cei_kit_lanche_com_dieta_autorizada_sem_frequencia_gera_erro(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao_dieta_a,
    classificacao_dieta_tipo_a,
):
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cei(escola_cei, [faixa_etaria])
    _criar_log_dieta_cei(
        escola_cei,
        periodo_escolar_integral,
        faixa_etaria,
        classificacao_dieta_tipo_a,
    )

    lista_erros = validate_lancamento_dietas_cei(solicitacao, [])

    assert _houve_erro_de_dietas(lista_erros)


def test_cei_kit_lanche_com_dieta_autorizada_e_frequencia_nao_gera_erro(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao_dieta_a,
    classificacao_dieta_tipo_a,
):
    solicitacao = _criar_solicitacao(escola_cei)
    medicao = _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cei(escola_cei, [faixa_etaria])
    _criar_log_dieta_cei(
        escola_cei,
        periodo_escolar_integral,
        faixa_etaria,
        classificacao_dieta_tipo_a,
    )
    _criar_frequencia(medicao, categoria_medicao_dieta_a, faixa_etaria)

    lista_erros = validate_lancamento_dietas_cei(solicitacao, [])

    assert not _houve_erro_de_dietas(lista_erros)


def test_cei_kit_lanche_com_dieta_somente_menor_de_um_ano_nao_gera_erro(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao_dieta_a,
    classificacao_dieta_tipo_a,
):
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[0]
    _criar_kit_lanche_cei(escola_cei, [faixa_etaria])
    _criar_log_dieta_cei(
        escola_cei,
        periodo_escolar_integral,
        faixa_etaria,
        classificacao_dieta_tipo_a,
    )

    lista_erros = validate_lancamento_dietas_cei(solicitacao, [])

    assert not _houve_erro_de_dietas(lista_erros)


def test_cei_com_inclusao_autorizada_nao_valida_kit_lanche(
    escola_cei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
):
    solicitacao = _criar_solicitacao(escola_cei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    _criar_kit_lanche_cei(escola_cei, [faixas_etarias_ativas[5]])
    _criar_inclusao_cei(escola_cei)

    dias_kit_lanche = _get_dias_kit_lanche_passeio_cei(solicitacao)

    assert DATA_SABADO not in dias_kit_lanche


def test_cemei_cei_kit_lanche_sem_frequencia_gera_erro_na_finalizacao(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixas_etarias_ativas[5]])

    lista_erros = validate_medicao_cemei_cei(solicitacao, [])

    assert _houve_erro_de_alimentacao(lista_erros)


def test_cemei_cei_kit_lanche_com_frequencia_nao_gera_erro_na_finalizacao(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    medicao = _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixa_etaria])
    _criar_frequencia(medicao, categoria_medicao, faixa_etaria)

    lista_erros = validate_medicao_cemei_cei(solicitacao, [])

    assert not _houve_erro_de_alimentacao(lista_erros)


def test_cemei_cei_kit_lanche_somente_menor_de_um_ano_nao_gera_erro(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixas_etarias_ativas[0]])

    lista_erros = validate_medicao_cemei_cei(solicitacao, [])

    assert not _houve_erro_de_alimentacao(lista_erros)


def test_cemei_cei_com_inclusao_autorizada_nao_valida_kit_lanche(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixa_etaria])
    _criar_inclusao_cemei(escola_cemei, faixa_etaria, periodo_escolar_integral)

    dias_kit_lanche = _get_dias_kit_lanche_passeio_cei(solicitacao)

    assert DATA_SABADO not in dias_kit_lanche


def test_cemei_cei_kit_lanche_com_dieta_autorizada_sem_frequencia_gera_erro(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao_dieta_a,
    classificacao_dieta_tipo_a,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixa_etaria])
    _criar_log_dieta_cei(
        escola_cemei,
        periodo_escolar_integral,
        faixa_etaria,
        classificacao_dieta_tipo_a,
    )

    lista_erros = validate_medicao_cemei_cei(solicitacao, [])

    assert _houve_erro_de_dietas(lista_erros)


def test_cemei_cei_kit_lanche_com_dieta_autorizada_e_frequencia_nao_gera_erro(
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_integral,
    categoria_medicao_dieta_a,
    classificacao_dieta_tipo_a,
):
    solicitacao = _criar_solicitacao(escola_cemei)
    medicao = _criar_medicao(solicitacao, periodo_escolar_integral)
    faixa_etaria = faixas_etarias_ativas[5]
    _criar_kit_lanche_cemei_cei(escola_cemei, [faixa_etaria])
    _criar_log_dieta_cei(
        escola_cemei,
        periodo_escolar_integral,
        faixa_etaria,
        classificacao_dieta_tipo_a,
    )
    _criar_frequencia(medicao, categoria_medicao_dieta_a, faixa_etaria)

    lista_erros = validate_medicao_cemei_cei(solicitacao, [])

    assert not _houve_erro_de_dietas(lista_erros)
