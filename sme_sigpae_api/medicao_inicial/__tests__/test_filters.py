import pytest

from sme_sigpae_api.medicao_inicial.api.filters import (
    ClausulaDeDescontoFilter,
    DiaParaCorrecaoFilter,
    EmpenhoFilter,
    ParametrizacaoFinanceiraFilter,
    RelatorioFinanceiroFilter,
)
from sme_sigpae_api.medicao_inicial.models import (
    ClausulaDeDesconto,
    DiaParaCorrigir,
    Empenho,
    ParametrizacaoFinanceira,
    RelatorioFinanceiro,
)

pytestmark = pytest.mark.django_db


def test_dia_para_corrigir_filter_solicitacao(dia_para_corrigir):
    filtro = DiaParaCorrecaoFilter(
        data={
            "uuid_solicitacao_medicao": dia_para_corrigir.medicao.solicitacao_medicao_inicial.uuid
        },
        queryset=DiaParaCorrigir.objects.filter(habilitado_correcao=True),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == dia_para_corrigir


def test_dia_para_corrigir_filter_grupo():
    filtro = DiaParaCorrecaoFilter(
        data={"nome_grupo": "Solicitações de Alimentação"},
        queryset=DiaParaCorrigir.objects.filter(habilitado_correcao=True),
    )
    assert filtro.qs.count() == 0


def test_dia_para_corrigir_filter_periodo(dia_para_corrigir):
    filtro = DiaParaCorrecaoFilter(
        data={"nome_periodo_escolar": dia_para_corrigir.medicao.periodo_escolar.nome},
        queryset=DiaParaCorrigir.objects.filter(habilitado_correcao=True),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == dia_para_corrigir


def test_empenho_filter_numero(empenho):
    filtro = EmpenhoFilter(
        data={"numero": empenho.numero},
        queryset=Empenho.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == empenho


def test_empenho_filter_contrato(empenho):
    filtro = EmpenhoFilter(
        data={"contrato": empenho.contrato.uuid},
        queryset=Empenho.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == empenho


def test_empenho_filter_edital(empenho):
    filtro = EmpenhoFilter(
        data={"edital": empenho.contrato.edital.uuid},
        queryset=Empenho.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == empenho


def test_clausula_desconto_filter_numero_clausula(clausula_desconto):
    filtro = ClausulaDeDescontoFilter(
        data={"numero_clausula": clausula_desconto.numero_clausula},
        queryset=ClausulaDeDesconto.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == clausula_desconto


def test_clausula_desconto_filter_porcentagem_desconto(clausula_desconto):
    filtro = ClausulaDeDescontoFilter(
        data={"porcentagem_desconto": clausula_desconto.porcentagem_desconto},
        queryset=ClausulaDeDesconto.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == clausula_desconto


def test_clausula_desconto_filter_edital(clausula_desconto):
    filtro = ClausulaDeDescontoFilter(
        data={"edital": clausula_desconto.edital},
        queryset=ClausulaDeDesconto.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == clausula_desconto


def test_parametrizacao_financeira_filter_lote(parametrizacao_financeira_emef):
    filtro = ParametrizacaoFinanceiraFilter(
        data={"lote": parametrizacao_financeira_emef.lote},
        queryset=ParametrizacaoFinanceira.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == parametrizacao_financeira_emef


def test_parametrizacao_financeira_filter_tipos_unidades(
    parametrizacao_financeira_emef,
):
    uuid_unidades = [
        str(unidade.uuid)
        for unidade in parametrizacao_financeira_emef.tipos_unidades.all()
    ]

    filtro = ParametrizacaoFinanceiraFilter(
        data={"tipos_unidades": ",".join(uuid_unidades)},
        queryset=ParametrizacaoFinanceira.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == parametrizacao_financeira_emef


def test_parametrizacao_financeira_filter_edital(parametrizacao_financeira_emef):
    filtro = ParametrizacaoFinanceiraFilter(
        data={"edital": parametrizacao_financeira_emef.edital},
        queryset=ParametrizacaoFinanceira.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == parametrizacao_financeira_emef


def test_relatorio_financeiro_filter_lote(relatorio_financeiro):
    filtro = RelatorioFinanceiroFilter(
        data={"lote": str(relatorio_financeiro.lote.uuid)},
        queryset=RelatorioFinanceiro.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == relatorio_financeiro


def test_relatorio_financeiro_filter_grupo_unidade_escolar(relatorio_financeiro):
    filtro = RelatorioFinanceiroFilter(
        data={"grupo_unidade_escolar": relatorio_financeiro.grupo_unidade_escolar.uuid},
        queryset=RelatorioFinanceiro.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == relatorio_financeiro


def test_relatorio_financeiro_filter_mes_ano(relatorio_financeiro):
    filtro = RelatorioFinanceiroFilter(
        data={"mes_ano": f"{relatorio_financeiro.mes}_{relatorio_financeiro.ano}"},
        queryset=RelatorioFinanceiro.objects.all(),
    )
    assert filtro.qs.count() == 1
    assert filtro.qs[0] == relatorio_financeiro
