import pytest
from model_bakery import baker

from src.medicao_inicial.api.filters import (
    ClausulaDeDescontoFilter,
    DiaParaCorrecaoFilter,
    EmpenhoFilter,
    LancheEmergencialDiarioFilter,
    ParametrizacaoFinanceiraFilter,
    RelatorioFinanceiroFilter,
    ValorMedicaoFilter,
)
from src.medicao_inicial.models import (
    GRUPO_RECREIO_NAS_FERIAS,
    GRUPO_RECREIO_NAS_FERIAS_CEMEI_CEI,
    ClausulaDeDesconto,
    DiaParaCorrigir,
    Empenho,
    LancheEmergencialDiario,
    ParametrizacaoFinanceira,
    RelatorioFinanceiro,
    ValorMedicao,
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


def test_valor_medicao_filter_grupo_com_uuid_solicitacao(
    solicitacao_medicao_inicial_com_grupo,
):
    filtro = ValorMedicaoFilter(
        data={
            "uuid_solicitacao_medicao": solicitacao_medicao_inicial_com_grupo.uuid,
            "nome_grupo": "Programas e Projetos",
        },
        queryset=ValorMedicao.objects.all(),
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].medicao == solicitacao_medicao_inicial_com_grupo.medicoes.get()


def test_valor_medicao_filter_sem_grupo_retorna_apenas_medicoes_sem_grupo(
    solicitacao_medicao_inicial,
    valor_medicao,
    categoria_medicao,
):
    grupo = baker.make("GrupoMedicao", nome="Programas e Projetos")
    medicao_com_grupo = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao_medicao_inicial,
        periodo_escolar=valor_medicao.medicao.periodo_escolar,
        grupo=grupo,
    )
    baker.make(
        "ValorMedicao",
        valor="99",
        nome_campo="observacoes",
        medicao=medicao_com_grupo,
        categoria_medicao=categoria_medicao,
    )

    filtro = ValorMedicaoFilter(
        data={
            "uuid_solicitacao_medicao": solicitacao_medicao_inicial.uuid,
            "nome_periodo_escolar": valor_medicao.medicao.periodo_escolar.nome,
        },
        queryset=ValorMedicao.objects.all(),
    )

    assert list(filtro.qs) == [valor_medicao]


def test_valor_medicao_filter_normaliza_grupo_legado_recreio_cei(
    escola_cei,
    categoria_medicao,
):
    grupo_recreio = baker.make("GrupoMedicao", nome=GRUPO_RECREIO_NAS_FERIAS)
    grupo_recreio_legado = baker.make(
        "GrupoMedicao", nome=GRUPO_RECREIO_NAS_FERIAS_CEMEI_CEI
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2025,
        escola=escola_cei,
    )
    medicao_legada = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo_recreio_legado,
    )
    valor_medicao = baker.make(
        "ValorMedicao",
        valor="10",
        nome_campo="observacoes",
        medicao=medicao_legada,
        categoria_medicao=categoria_medicao,
    )

    filtro = ValorMedicaoFilter(
        data={
            "uuid_solicitacao_medicao": solicitacao.uuid,
            "nome_grupo": GRUPO_RECREIO_NAS_FERIAS,
        },
        queryset=ValorMedicao.objects.all(),
    )

    assert list(filtro.qs) == [valor_medicao]

    medicao_legada.refresh_from_db()

    assert medicao_legada.grupo == grupo_recreio


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
        data={"edital": clausula_desconto.edital.uuid},
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
        for unidade in parametrizacao_financeira_emef.grupo_unidade_escolar.tipos_unidades.all()
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


def test_lanche_emergencial_diario_filter_periodo_com_data_final_nula(escola):
    lanche = LancheEmergencialDiario.objects.create(
        escola=escola,
        data_inicial="2026-03-01",
        data_final=None,
    )
    LancheEmergencialDiario.objects.create(
        escola=escola,
        data_inicial="2026-05-01",
        data_final="2026-05-31",
    )

    filtro = LancheEmergencialDiarioFilter(
        data={"escola_uuid": escola.uuid, "mes": "04", "ano": "2026"},
        queryset=LancheEmergencialDiario.objects.all(),
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0] == lanche


def test_lanche_emergencial_diario_filter_periodo_fechado(escola):
    lanche = LancheEmergencialDiario.objects.create(
        escola=escola,
        data_inicial="2026-03-10",
        data_final="2026-04-05",
    )
    LancheEmergencialDiario.objects.create(
        escola=escola,
        data_inicial="2026-05-01",
        data_final=None,
    )

    filtro = LancheEmergencialDiarioFilter(
        data={"escola_uuid": escola.uuid, "mes": "04", "ano": "2026"},
        queryset=LancheEmergencialDiario.objects.all(),
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0] == lanche
