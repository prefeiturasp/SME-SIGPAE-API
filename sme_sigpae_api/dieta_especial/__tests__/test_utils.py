import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict

from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...terceirizada.models import Edital
from ..models import SolicitacaoDietaEspecial
from ..utils import (
    dados_dietas_escolas_cei,
    dados_dietas_escolas_comuns,
    dietas_especiais_a_terminar,
    formatar_informacoes_historioco_dietas,
    formatar_periodos_cei,
    formatar_periodos_cemei,
    formatar_periodos_emebs,
    formatar_periodos_emei_emef_cieja,
    gera_dicionario_historico_dietas,
    gera_logs_dietas_escolas_cei,
    gera_logs_dietas_escolas_comuns,
    gerar_filtros_relatorio_historico,
    termina_dietas_especiais,
    transformar_dados_escolas,
    unidades_tipo_cei,
    unidades_tipo_cemei,
    unidades_tipo_emebs,
    unidades_tipos_cmct_ceugestao,
    unidades_tipos_emei_emef_cieja,
)

pytestmark = pytest.mark.django_db


def test_dietas_especiais_a_terminar(solicitacoes_dieta_especial_com_data_termino):
    assert dietas_especiais_a_terminar().count() == 3


def test_termina_dietas_especiais(
    solicitacoes_dieta_especial_com_data_termino, usuario_admin
):
    termina_dietas_especiais(usuario_admin)
    assert dietas_especiais_a_terminar().count() == 0
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            status=DietaEspecialWorkflow.TERMINADA_AUTOMATICAMENTE_SISTEMA
        ).count()
        == 3
    )


def test_registrar_historico_criacao(
    protocolo_padrao_dieta_especial_2, substituicao_padrao_dieta_especial_2
):
    from ..utils import log_create

    log_create(protocolo_padrao_dieta_especial_2)
    assert protocolo_padrao_dieta_especial_2.historico


def test_diff_protocolo_padrao(
    protocolo_padrao_dieta_especial_2, substituicao_padrao_dieta_especial_2, edital
):
    from ..utils import diff_protocolo_padrao

    validated_data = {
        "nome_protocolo": "Alergia a manga",
        "orientacoes_gerais": "Uma orientação",
        "status": "I",
        "editais": [edital.uuid],
    }
    old_editais = protocolo_padrao_dieta_especial_2.editais
    new_editais = validated_data.get("editais")
    new_editais = Edital.objects.filter(uuid__in=new_editais)
    changes = diff_protocolo_padrao(
        protocolo_padrao_dieta_especial_2, validated_data, old_editais, old_editais
    )
    assert changes


def test_gera_logs_dietas_escolas_comuns(escola, solicitacoes_dieta_especial_ativas):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    logs = gera_logs_dietas_escolas_comuns(
        escola, solicitacoes_dieta_especial_ativas, ontem
    )
    assert len(logs) == 6
    assert len([log for log in logs if log.classificacao.nome == "Tipo A"]) == 2


def test_gera_logs_dietas_escolas_cei(
    escola_cei,
    solicitacoes_dieta_especial_ativas_cei,
    log_aluno_integral_cei,
    log_alunos_matriculados_integral_cei,
):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    logs = gera_logs_dietas_escolas_cei(
        escola_cei, solicitacoes_dieta_especial_ativas_cei, ontem
    )
    assert len(logs) == 2
    assert len([log for log in logs if log.classificacao.nome == "Tipo A"]) == 1
    assert [log for log in logs if log.classificacao.nome == "Tipo A"][
        0
    ].quantidade == 2


def test_gera_logs_dietas_escolas_cemei(
    escola_cemei, solicitacoes_dieta_especial_ativas_cemei
):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    logs = gera_logs_dietas_escolas_comuns(
        escola_cemei, solicitacoes_dieta_especial_ativas_cemei, ontem
    )
    assert len(logs) == 12
    assert [
        log
        for log in logs
        if log.cei_ou_emei == "N/A" and log.classificacao.nome == "Tipo A"
    ][0].quantidade == 3
    assert [
        log
        for log in logs
        if log.cei_ou_emei == "CEI" and log.classificacao.nome == "Tipo A"
    ][0].quantidade == 2
    assert [
        log
        for log in logs
        if log.cei_ou_emei == "EMEI" and log.classificacao.nome == "Tipo A"
    ][0].quantidade == 1


def test_gera_logs_dietas_escolas_cei_com_solicitacao_medicao(
    escola_cei,
    solicitacoes_dieta_especial_ativas_cei_com_solicitacao_medicao,
    log_aluno_integral_cei,
    log_alunos_matriculados_integral_cei,
):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    logs = gera_logs_dietas_escolas_cei(
        escola_cei,
        solicitacoes_dieta_especial_ativas_cei_com_solicitacao_medicao,
        ontem,
    )
    assert len(logs) == 3
    assert len([log for log in logs if log.classificacao.nome == "Tipo B"]) == 1
    assert [log for log in logs if log.classificacao.nome == "Tipo A Enteral"][
        0
    ].quantidade == 1
    assert [log for log in logs if log.classificacao.nome == "Tipo B"][
        0
    ].quantidade == 2


def test_gera_logs_dietas_escolas_emebs(
    escola_emebs, solicitacoes_dieta_especial_ativas_emebs
):
    hoje = datetime.date.today()
    ontem = hoje - datetime.timedelta(days=1)
    logs = gera_logs_dietas_escolas_comuns(
        escola_emebs, solicitacoes_dieta_especial_ativas_emebs, ontem
    )
    assert len(logs) == 15
    assert len([log for log in logs if log.periodo_escolar == None]) == 9
    assert (
        len(
            [
                log
                for log in logs
                if log.infantil_ou_fundamental == "INFANTIL"
                and log.classificacao.nome == "Tipo A"
            ]
        )
        == 2
    )


def test_gerar_filtros_relatorio_historico(
    escola, escola_emebs, periodo_escolar_integral, classificacoes_dietas
):
    query_params = QueryDict(mutable=True)
    query_params.setlist(
        "unidades_educacionais_selecionadas[]",
        [
            str(escola.uuid),
            str(escola_emebs.uuid),
        ],
    )
    query_params.setlist(
        "tipos_unidades_selecionadas[]",
        [str(escola_emebs.tipo_unidade.uuid)],
    )
    query_params.setlist(
        "periodos_escolares_selecionadas[]",
        [str(periodo_escolar_integral.uuid)],
    )
    query_params.setlist(
        "classificacoes_selecionadas[]",
        [classificacao.id for classificacao in classificacoes_dietas],
    )
    query_params["tipo_gestao"] = str(escola_emebs.tipo_gestao.uuid)
    query_params["lote"] = str(escola_emebs.lote.uuid)
    query_params["data"] = "12/04/2025"

    filtros, _ = gerar_filtros_relatorio_historico(query_params)

    assert isinstance(filtros["escola__uuid__in"], list)
    assert len(filtros["escola__uuid__in"]) == 2
    assert set(filtros["escola__uuid__in"]) == {
        str(escola.uuid),
        str(escola_emebs.uuid),
    }

    assert isinstance(filtros["escola__tipo_unidade__uuid__in"], list)
    assert len(filtros["escola__tipo_unidade__uuid__in"]) == 1
    assert (
        str(escola_emebs.tipo_unidade.uuid) in filtros["escola__tipo_unidade__uuid__in"]
    )

    assert isinstance(filtros["periodo_escolar__uuid__in"], list)
    assert len(filtros["periodo_escolar__uuid__in"]) == 1
    assert str(periodo_escolar_integral.uuid) in filtros["periodo_escolar__uuid__in"]

    assert isinstance(filtros["classificacao__id__in"], list)
    assert len(filtros["classificacao__id__in"]) == 3
    for classificacao in classificacoes_dietas:
        assert classificacao.id in filtros["classificacao__id__in"]

    assert filtros["escola__tipo_gestao__uuid"] == str(escola_emebs.tipo_gestao.uuid)
    assert filtros["escola__lote__uuid"] == str(escola_emebs.lote.uuid)
    assert filtros["data__day"] == 12
    assert filtros["data__month"] == 4
    assert filtros["data__year"] == 2025
    assert filtros["quantidade__gt"] == 0


def test_gerar_filtros_relatorio_historico_somente_com_data():
    query_params = QueryDict(mutable=True)
    query_params["data"] = "20/04/2025"

    filtros, _ = gerar_filtros_relatorio_historico(query_params)
    assert filtros["data__day"] == 20
    assert filtros["data__month"] == 4
    assert filtros["data__year"] == 2025
    assert filtros["quantidade__gt"] == 0


def test_gerar_filtros_relatorio_historico_retona_data_obrigatoria():
    query_params = QueryDict(mutable=True)
    query_params.setlist(
        "unidades_educacionais_selecionadas[]",
        [],
    )
    query_params.setlist(
        "tipos_unidades_selecionadas[]",
        [],
    )
    query_params.setlist(
        "periodos_escolares_selecionadas[]",
        [],
    )
    query_params.setlist(
        "classificacoes_selecionadas[]",
        [],
    )
    query_params["tipo_gestao"] = None
    query_params["lote"] = None
    query_params["data"] = None

    with pytest.raises(ValidationError, match="Data é um parâmetro obrigatório"):
        gerar_filtros_relatorio_historico(query_params)


def test_gerar_filtros_relatorio_historico_retona_data_padrao_incorreto():
    query_params = QueryDict(mutable=True)
    query_params["data"] = "2025-04-20"

    with pytest.raises(
        ValidationError,
        match="A data 2025-04-20 não corresponde ao formato esperado 'dd/mm/YYYY'.",
    ):
        gerar_filtros_relatorio_historico(query_params)


def test_unidades_tipo_emebs(escolas_tipo_emebs):
    item, item_somatorio, classificacao = escolas_tipo_emebs
    total_dietas = 0

    dietas = unidades_tipo_emebs(item, classificacao)
    assert dietas == 0
    informacao_classificacao = classificacao["Escola EMEBS"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "fundamental" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["fundamental"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "TARDE" in periodo
    assert periodo["TARDE"] == 6

    dietas = unidades_tipo_emebs(item_somatorio, classificacao)
    assert dietas == 6
    informacao_classificacao = classificacao["Escola EMEBS"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "fundamental" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["fundamental"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "TARDE" in periodo
    assert periodo["TARDE"] == 6


def test_unidades_tipos_emei_emef_cieja(escolas_tipo_emei_emef_cieja):
    item, item_somatorio, classificacao = escolas_tipo_emei_emef_cieja
    total_dietas = 0

    dietas = unidades_tipos_emei_emef_cieja(item, classificacao)
    assert dietas == 0
    informacao_classificacao = classificacao["Escola EMEF"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "periodos" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["periodos"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "TARDE" in periodo
    assert periodo["TARDE"] == 6

    dietas = unidades_tipos_emei_emef_cieja(item_somatorio, classificacao)
    assert dietas == 6
    informacao_classificacao = classificacao["Escola EMEF"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "periodos" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["periodos"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "TARDE" in periodo
    assert periodo["TARDE"] == 6


def test_unidades_tipos_cmct_ceugestao(escolas_tipos_cmct_ceugestao):
    item, item_somatorio, classificacao = escolas_tipos_cmct_ceugestao
    total_dietas = classificacao["Escola CEU GESTAO"]["classificacoes"]["Tipo A"][
        "total"
    ]

    dietas = unidades_tipos_cmct_ceugestao(item, classificacao)
    assert dietas == 10
    informacao_classificacao = classificacao["Escola CEU GESTAO"]["classificacoes"][
        "Tipo A"
    ]
    total_dietas += dietas
    assert informacao_classificacao["total"] == total_dietas

    dietas = unidades_tipos_cmct_ceugestao(item_somatorio, classificacao)
    assert dietas == 5
    informacao_classificacao = classificacao["Escola CEU GESTAO"]["classificacoes"][
        "Tipo A"
    ]
    total_dietas += dietas
    assert informacao_classificacao["total"] == total_dietas


def test_unidades_tipo_cei(escolas_tipo_cei):
    item, item_somatorio, classificacao = escolas_tipo_cei
    total_dietas = 0

    dietas = unidades_tipo_cei(item, classificacao)
    assert dietas == 0
    informacao_classificacao = classificacao["Escola CEI DIRET"]["classificacoes"][
        "Tipo A"
    ]
    total_dietas += dietas
    assert "periodos" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["periodos"]["INTEGRAL"]
    assert isinstance(periodo, list)
    assert len(periodo) == 2
    assert periodo[1]["autorizadas"] == 3
    assert periodo[1]["faixa"] == "07 a 11 meses"

    dietas = unidades_tipo_cei(item_somatorio, classificacao)
    assert dietas == 4
    informacao_classificacao = classificacao["Escola CEI DIRET"]["classificacoes"][
        "Tipo A"
    ]
    total_dietas += dietas
    assert "periodos" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["periodos"]["INTEGRAL"]
    assert isinstance(periodo, list)
    assert len(periodo) == 2
    assert periodo[1]["autorizadas"] == 3
    assert periodo[1]["faixa"] == "07 a 11 meses"


def test_unidades_tipo_cemei_por_faixa_etaria(escolas_tipo_cemei_por_faixa_etaria):
    item, item_somatorio, classificacao = escolas_tipo_cemei_por_faixa_etaria
    total_dietas = 0

    dietas = unidades_tipo_cemei(item, classificacao)
    assert dietas == 0
    informacao_classificacao = classificacao["Escola CEMEI"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "por_idade" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["por_idade"]
    assert isinstance(periodo, dict)
    assert "INTEGRAL" in periodo
    assert len(periodo["INTEGRAL"]) == 2

    dietas = unidades_tipo_cemei(item_somatorio, classificacao)
    assert dietas == 4
    informacao_classificacao = classificacao["Escola CEMEI"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "por_idade" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["por_idade"]
    assert isinstance(periodo, dict)
    assert "INTEGRAL" in periodo
    assert len(periodo["INTEGRAL"]) == 2


def test_unidades_tipo_cemei_por_periodo(escolas_tipo_cemei_por_periodo):
    item, item_somatorio, classificacao = escolas_tipo_cemei_por_periodo
    total_dietas = 0

    dietas = unidades_tipo_cemei(item, classificacao)
    assert dietas == 0
    informacao_classificacao = classificacao["Escola CEMEI"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "turma_infantil" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["turma_infantil"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "INTEGRAL" in periodo
    assert periodo["INTEGRAL"] == 3

    dietas = unidades_tipo_cemei(item_somatorio, classificacao)
    assert dietas == 4
    informacao_classificacao = classificacao["Escola CEMEI"]["classificacoes"]["Tipo A"]
    total_dietas += dietas
    assert "turma_infantil" in informacao_classificacao
    assert informacao_classificacao["total"] == total_dietas
    periodo = informacao_classificacao["turma_infantil"]
    assert isinstance(periodo, dict)
    assert len(periodo) == 1
    assert "INTEGRAL" in periodo
    assert periodo["INTEGRAL"] == 3


def test_gera_dicionario_historico_dietas(
    log_dietas_autorizadas, log_dietas_autorizadas_cei
):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
    }
    informacoes = gera_dicionario_historico_dietas(filtros)
    assert informacoes["total_dietas"] == 72
    assert len(informacoes["resultados"]) == 4
    resultados = informacoes["resultados"]
    assert resultados[0]["unidade_educacional"] == "CEI DIRET JOAO MENDES"
    assert resultados[0]["classificacao"] == "Tipo B"
    assert resultados[0]["total"] == 21

    assert resultados[1]["unidade_educacional"] == "CEMEI"
    assert resultados[1]["classificacao"] == "Tipo A"
    assert resultados[1]["total"] == 25

    assert resultados[2]["unidade_educacional"] == "CEMEI"
    assert resultados[2]["classificacao"] == "Tipo B"
    assert resultados[2]["total"] == 15

    assert resultados[3]["unidade_educacional"] == "EMEBS"
    assert resultados[3]["classificacao"] == "Tipo A"
    assert resultados[3]["total"] == 11


def test_gera_dicionario_historico_dietas_escola_cemei(
    log_dietas_autorizadas, log_dietas_autorizadas_cei, escola_cemei
):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
        "escola__uuid__in": [escola_cemei.uuid],
    }
    informacoes = gera_dicionario_historico_dietas(filtros)
    assert informacoes["total_dietas"] == 40
    assert len(informacoes["resultados"]) == 2
    resultados = informacoes["resultados"]
    assert resultados[0]["unidade_educacional"] == "CEMEI"
    assert resultados[0]["classificacao"] == "Tipo A"
    assert resultados[0]["total"] == 25

    assert resultados[1]["unidade_educacional"] == "CEMEI"
    assert resultados[1]["classificacao"] == "Tipo B"
    assert resultados[1]["total"] == 15


def test_gera_dicionario_historico_dietas_escola_cei(
    log_dietas_autorizadas_cei, escola_cei
):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
        "escola__uuid__in": [escola_cei.uuid],
    }
    informacoes = gera_dicionario_historico_dietas(filtros)
    assert informacoes["total_dietas"] == 21
    assert len(informacoes["resultados"]) == 1
    resultados = informacoes["resultados"]
    assert resultados[0]["unidade_educacional"] == "CEI DIRET JOAO MENDES"
    assert resultados[0]["classificacao"] == "Tipo B"
    assert resultados[0]["total"] == 21


def test_gera_dicionario_historico_dietas_escola_emebs(
    log_dietas_autorizadas, escola_emebs
):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
        "escola__uuid__in": [escola_emebs.uuid],
    }
    informacoes = gera_dicionario_historico_dietas(filtros)
    assert informacoes["total_dietas"] == 11
    assert len(informacoes["resultados"]) == 1
    resultados = informacoes["resultados"]
    assert resultados[0]["unidade_educacional"] == "EMEBS"
    assert resultados[0]["classificacao"] == "Tipo A"
    assert resultados[0]["total"] == 11


def test_cria_dicionario_historico_dietas_autorizadas_cei(log_dietas_autorizadas_cei):
    informacoes_logs = dados_dietas_escolas_cei({})
    informacoes, total_dietas = transformar_dados_escolas(informacoes_logs)

    assert total_dietas == 46
    assert isinstance(informacoes, dict)
    assert len(informacoes) == 2
    assert "CEI DIRET JOAO MENDES" in informacoes
    assert "CEMEI" in informacoes


def test_cria_dicionario_historico_dietas_autorizadas(log_dietas_autorizadas):
    informacoes_logs = dados_dietas_escolas_comuns({})
    informacoes, total_dietas = transformar_dados_escolas(informacoes_logs)

    assert total_dietas == 26
    assert isinstance(informacoes, dict)
    assert len(informacoes) == 2
    assert "CEMEI" in informacoes
    assert "EMEBS" in informacoes


def test_dados_dietas_escolas_cei(log_dietas_autorizadas_cei):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
    }
    logs = dados_dietas_escolas_cei(filtros)
    assert len(logs) == 6
    assert logs[0]["nome_escola"] == "CEI DIRET JOAO MENDES"
    assert logs[0]["nome_classificacao"] == "Tipo B"
    assert logs[0]["nome_periodo_escolar"] == "INTEGRAL"

    assert logs[1]["nome_escola"] == "CEI DIRET JOAO MENDES"
    assert logs[1]["nome_classificacao"] == "Tipo B"
    assert logs[1]["nome_periodo_escolar"] == "MANHA"

    assert logs[2]["nome_escola"] == "CEI DIRET JOAO MENDES"
    assert logs[2]["nome_classificacao"] == "Tipo B"
    assert logs[2]["nome_periodo_escolar"] == "INTEGRAL"
    assert logs[2]["inicio"] is None
    assert logs[2]["fim"] is None

    assert logs[3]["nome_escola"] == "CEMEI"
    assert logs[3]["nome_classificacao"] == "Tipo A"
    assert logs[3]["nome_periodo_escolar"] == "INTEGRAL"

    assert logs[4]["nome_escola"] == "CEMEI"
    assert logs[4]["nome_classificacao"] == "Tipo A"
    assert logs[4]["nome_periodo_escolar"] == "MANHA"

    assert logs[5]["nome_escola"] == "CEMEI"
    assert logs[5]["nome_classificacao"] == "Tipo A"
    assert logs[5]["nome_periodo_escolar"] == "INTEGRAL"
    assert logs[5]["inicio"] is None
    assert logs[5]["fim"] is None


def test_dados_dietas_escolas_comuns(log_dietas_autorizadas):
    data = datetime.date(2024, 3, 20)
    filtros = {
        "data__day": data.day,
        "data__month": data.month,
        "data__year": data.year,
    }
    logs = dados_dietas_escolas_comuns(filtros)
    assert len(logs) == 6

    assert logs[0]["nome_escola"] == "CEMEI"
    assert logs[0]["nome_classificacao"] == "Tipo B"
    assert logs[0]["nome_periodo_escolar"] == "INTEGRAL"

    assert logs[1]["nome_escola"] == "CEMEI"
    assert logs[1]["nome_classificacao"] == "Tipo B"
    assert logs[1]["nome_periodo_escolar"] == "MANHA"

    assert logs[2]["nome_escola"] == "CEMEI"
    assert logs[2]["nome_classificacao"] == "Tipo B"
    assert logs[2]["nome_periodo_escolar"] is None

    assert logs[3]["nome_escola"] == "EMEBS"
    assert logs[3]["nome_classificacao"] == "Tipo A"
    assert logs[3]["nome_periodo_escolar"] == "INTEGRAL"

    assert logs[4]["nome_escola"] == "EMEBS"
    assert logs[4]["nome_classificacao"] == "Tipo A"
    assert logs[4]["nome_periodo_escolar"] == "MANHA"

    assert logs[5]["nome_escola"] == "EMEBS"
    assert logs[5]["nome_classificacao"] == "Tipo A"
    assert logs[5]["nome_periodo_escolar"] is None


def test_formatar_periodos_emebs():
    informacao = {
        "data": datetime.date(2024, 2, 12),
        "unidade_educacional": "Escola EMEBS",
        "tipo_unidade": "EMEBS",
        "lote": "Lote EMEBS",
        "classificacao": "Tipo A",
        "total": 2,
    }
    classificacao = {
        "infantil": {"MANHA": 1},
        "fundamental": {"TARDE": 1},
        "periodos": {},
        "por_idade": {},
        "turma_infantil": {},
        "faixa_etaria": {},
        "total": 2,
    }
    formatar_periodos_emebs(informacao, classificacao)
    assert "periodos" in informacao
    assert isinstance(informacao["periodos"], dict)

    assert "fundamental" in informacao["periodos"]
    assert isinstance(informacao["periodos"]["fundamental"], list)
    assert len(informacao["periodos"]["fundamental"]) == 1
    assert {"periodo": "TARDE", "autorizadas": 1} == informacao["periodos"][
        "fundamental"
    ][0]

    assert "infantil" in informacao["periodos"]
    assert isinstance(informacao["periodos"]["infantil"], list)
    assert len(informacao["periodos"]["infantil"]) == 1
    assert {"periodo": "MANHA", "autorizadas": 1} == informacao["periodos"]["infantil"][
        0
    ]


def test_formatar_periodos_emei_emef_cieja(escolas_tipo_emei_emef_cieja):
    _, _, classificacao = escolas_tipo_emei_emef_cieja
    informacao = {
        "data": datetime.date(2024, 2, 12),
        "unidade_educacional": "Escola EMEF",
        "tipo_unidade": "EMEF",
        "lote": "LOTE EMEF",
        "classificacao": "Tipo A",
        "total": 1,
    }
    formatar_periodos_emei_emef_cieja(
        informacao, classificacao["Escola EMEF"]["classificacoes"]["Tipo A"]
    )
    assert "periodos" in informacao
    assert isinstance(informacao["periodos"], list)
    assert len(informacao["periodos"]) == 1
    assert {"periodo": "TARDE", "autorizadas": 1} == informacao["periodos"][0]


def test_formatar_periodos_cemei():
    informacao = {
        "data": datetime.date(2024, 2, 12),
        "unidade_educacional": "Escola CEMEI",
        "tipo_unidade": "CEMEI",
        "lote": "LOTE CEMEI",
        "classificacao": "Tipo A",
        "total": 2,
    }
    classificacao = {
        "infantil": {},
        "fundamental": {},
        "periodos": {},
        "por_idade": {
            "INTEGRAL": [{"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1}]
        },
        "turma_infantil": {"INTEGRAL": 1},
        "faixa_etaria": {},
        "total": 2,
    }
    formatar_periodos_cemei(informacao, classificacao)

    assert "periodos" in informacao
    assert isinstance(informacao["periodos"], dict)

    assert "turma_infantil" in informacao["periodos"]
    assert isinstance(informacao["periodos"]["turma_infantil"], list)
    assert len(informacao["periodos"]["turma_infantil"]) == 1
    assert {"periodo": "INTEGRAL", "autorizadas": 1} == informacao["periodos"][
        "turma_infantil"
    ][0]

    assert "por_idade" in informacao["periodos"]
    assert isinstance(informacao["periodos"]["por_idade"], list)
    assert len(informacao["periodos"]["por_idade"]) == 1
    assert "periodo" in informacao["periodos"]["por_idade"][0]
    assert "faixa_etaria" in informacao["periodos"]["por_idade"][0]

    assert [{"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1}] == informacao[
        "periodos"
    ]["por_idade"][0]["faixa_etaria"]


def test_formatar_periodos_cei(escolas_tipo_cei):
    _, _, classificacao = escolas_tipo_cei
    informacao = {
        "data": datetime.date(2024, 2, 12),
        "unidade_educacional": "Escola CEI DIRET",
        "tipo_unidade": "CEI DIRET",
        "lote": "LOTE CEI DIRET",
        "classificacao": "Tipo A",
        "total": 1,
    }

    formatar_periodos_cei(
        informacao, classificacao["Escola CEI DIRET"]["classificacoes"]["Tipo A"]
    )

    assert "periodos" in informacao
    assert isinstance(informacao["periodos"], list)
    assert "periodo" in informacao["periodos"][0]
    assert "faixa_etaria" in informacao["periodos"][0]
    assert [{"faixa": "01 ano a 03 anos e 11 meses", "autorizadas": 1}] == informacao[
        "periodos"
    ][0]["faixa_etaria"]


def test_formatar_informacoes_historioco_dietas(
    escolas_tipo_emebs,
    escolas_tipo_emei_emef_cieja,
    escolas_tipos_cmct_ceugestao,
    escolas_tipo_cei,
    escolas_tipo_cemei_por_faixa_etaria,
    escolas_tipo_cemei_por_periodo,
):
    _, _, emebs = escolas_tipo_emebs
    _, _, emef = escolas_tipo_emei_emef_cieja
    _, _, ceu_gestao = escolas_tipos_cmct_ceugestao
    _, _, cei = escolas_tipo_cei
    _, _, cemei_cei = escolas_tipo_cemei_por_faixa_etaria
    _, _, cemei_emei = escolas_tipo_cemei_por_periodo

    escolas = {**emebs, **emef, **ceu_gestao, **cei, **cemei_cei, **cemei_emei}
    total_dietas = 8
    resultado = formatar_informacoes_historioco_dietas(escolas, total_dietas)
    assert isinstance(resultado, dict)
    assert "total_dietas" in resultado
    assert resultado["total_dietas"] == total_dietas
    assert "resultados" in resultado
    assert isinstance(resultado["resultados"], list)
    assert len(resultado["resultados"]) == 5
    assert resultado["resultados"][0]["unidade_educacional"] == "Escola EMEBS"
    assert resultado["resultados"][1]["unidade_educacional"] == "Escola EMEF"
    assert resultado["resultados"][2]["unidade_educacional"] == "Escola CEU GESTAO"
    assert resultado["resultados"][3]["unidade_educacional"] == "Escola CEI DIRET"
    assert resultado["resultados"][4]["unidade_educacional"] == "Escola CEMEI"
