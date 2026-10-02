import datetime

import pytest
from model_bakery import baker

from src.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    Medicao,
    PermissaoLancamentoEspecial,
)
from src.medicao_inicial.utils import get_linhas_da_tabela
from src.medicao_inicial.validators import (
    filtrar_alimentacoes_permitidas_pela_inclusao,
    validate_lancamento_inclusoes,
)

pytestmark = pytest.mark.django_db

MES = 5
ANO = 2025
DIA = 5

ALIMENTACOES_ESPECIAIS = [
    "2ª Refeição 1ª oferta",
    "Repetição 2ª Refeição",
    "2ª Sobremesa 1ª oferta",
    "Repetição 2ª Sobremesa",
    "2º Lanche 4h",
    "2º Lanche 5h",
    "Lanche Extra",
]


def _criar_solicitacao(escola):
    return baker.make(
        "SolicitacaoMedicaoInicial", mes=f"{MES:02d}", ano=str(ANO), escola=escola
    )


def _criar_inclusao_normal(escola, periodo_escolar, tipos_alimentacao):
    grupo = baker.make(
        "inclusao_alimentacao.GrupoInclusaoAlimentacaoNormal",
        escola=escola,
        rastro_escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.lote.diretoria_regional,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "inclusao_alimentacao.InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo,
        data=datetime.date(ANO, MES, DIA),
    )
    qt_periodo = baker.make(
        "inclusao_alimentacao.QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo,
        periodo_escolar=periodo_escolar,
        numero_alunos=10,
    )
    qt_periodo.tipos_alimentacao.set(tipos_alimentacao)


def _criar_permissao_especial(escola, periodo_escolar):
    alimentacoes = []
    for nome in ALIMENTACOES_ESPECIAIS:
        alimentacao, _ = AlimentacaoLancamentoEspecial.objects.get_or_create(nome=nome)
        alimentacoes.append(alimentacao)
    return baker.make(
        "PermissaoLancamentoEspecial",
        escola=escola,
        diretoria_regional=escola.lote.diretoria_regional,
        periodo_escolar=periodo_escolar,
        alimentacoes_lancamento_especial=alimentacoes,
        criado_por=baker.make("Usuario"),
        data_inicial=datetime.date(ANO, MES, 1),
        data_final=None,
    )


def _eh_numero_alunos(solicitacao, periodo_escolar):
    return (
        periodo_escolar
        not in solicitacao.escola.periodos_escolares(
            ano=solicitacao.ano, mes=solicitacao.mes
        )
    )


def _criar_valores(solicitacao, periodo_escolar, categoria_medicao, alimentacoes):
    eh_numero_alunos = _eh_numero_alunos(solicitacao, periodo_escolar)
    linhas_da_tabela = get_linhas_da_tabela(alimentacoes, eh_numero_alunos)
    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo_escolar,
    )
    for nome_campo in linhas_da_tabela:
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            nome_campo=nome_campo,
            dia=f"{DIA:02d}",
            categoria_medicao=categoria_medicao,
            valor="1",
        )
    return linhas_da_tabela


class TestFiltrarAlimentacoesPermitidasPelaInclusao:
    def test_permite_apenas_lanches_quando_inclusao_tem_lanche(self):
        resultado = filtrar_alimentacoes_permitidas_pela_inclusao(
            ["Lanche"], ALIMENTACOES_ESPECIAIS
        )
        assert resultado == ["2º Lanche 4h", "2º Lanche 5h", "Lanche Extra"]

    def test_permite_apenas_refeicao_quando_inclusao_tem_refeicao(self):
        resultado = filtrar_alimentacoes_permitidas_pela_inclusao(
            ["Refeição"], ALIMENTACOES_ESPECIAIS
        )
        assert resultado == ["2ª Refeição 1ª oferta", "Repetição 2ª Refeição"]

    def test_permite_apenas_sobremesa_quando_inclusao_tem_sobremesa(self):
        resultado = filtrar_alimentacoes_permitidas_pela_inclusao(
            ["Sobremesa"], ALIMENTACOES_ESPECIAIS
        )
        assert resultado == ["2ª Sobremesa 1ª oferta", "Repetição 2ª Sobremesa"]

    def test_lanche_4h_conta_como_lanche(self):
        resultado = filtrar_alimentacoes_permitidas_pela_inclusao(
            ["Lanche 4h"], ALIMENTACOES_ESPECIAIS
        )
        assert resultado == ["2º Lanche 4h", "2º Lanche 5h", "Lanche Extra"]

    def test_nao_permite_nenhum_especial_sem_alimentacao_na_inclusao(self):
        resultado = filtrar_alimentacoes_permitidas_pela_inclusao(
            [], ALIMENTACOES_ESPECIAIS
        )
        assert resultado == []


class TestValidateLancamentoInclusoes:
    def test_nao_gera_erro_quando_permissao_especial_nao_tem_parzinho_na_inclusao(
        self,
        escola_cmct,
        periodo_escolar_manha,
        tipo_alimentacao_lanche,
        categoria_medicao,
    ):
        _criar_inclusao_normal(
            escola_cmct, periodo_escolar_manha, [tipo_alimentacao_lanche]
        )
        _criar_permissao_especial(escola_cmct, periodo_escolar_manha)
        solicitacao = _criar_solicitacao(escola_cmct)
        _criar_valores(
            solicitacao,
            periodo_escolar_manha,
            categoria_medicao,
            ["Lanche", "2º Lanche 4h", "2º Lanche 5h", "Lanche Extra"],
        )

        lista_erros = validate_lancamento_inclusoes(solicitacao, [])

        assert lista_erros == []

    def test_gera_erro_quando_falta_2_refeicao_e_inclusao_tem_refeicao(
        self,
        escola_cmct,
        periodo_escolar_manha,
        tipo_alimentacao_refeicao,
        categoria_medicao,
    ):
        _criar_inclusao_normal(
            escola_cmct, periodo_escolar_manha, [tipo_alimentacao_refeicao]
        )
        _criar_permissao_especial(escola_cmct, periodo_escolar_manha)
        solicitacao = _criar_solicitacao(escola_cmct)
        _criar_valores(
            solicitacao,
            periodo_escolar_manha,
            categoria_medicao,
            ["Refeição"],
        )

        lista_erros = validate_lancamento_inclusoes(solicitacao, [])

        assert lista_erros == [
            {
                "periodo_escolar": periodo_escolar_manha.nome,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        ]

    def test_nao_gera_erro_quando_lanca_2_refeicao_e_inclusao_tem_refeicao(
        self,
        escola_cmct,
        periodo_escolar_manha,
        tipo_alimentacao_refeicao,
        categoria_medicao,
    ):
        _criar_inclusao_normal(
            escola_cmct, periodo_escolar_manha, [tipo_alimentacao_refeicao]
        )
        _criar_permissao_especial(escola_cmct, periodo_escolar_manha)
        solicitacao = _criar_solicitacao(escola_cmct)
        _criar_valores(
            solicitacao,
            periodo_escolar_manha,
            categoria_medicao,
            ["Refeição", "2ª Refeição 1ª oferta", "Repetição 2ª Refeição"],
        )

        lista_erros = validate_lancamento_inclusoes(solicitacao, [])

        assert lista_erros == []