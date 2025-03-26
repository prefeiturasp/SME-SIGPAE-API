import datetime

import pytest
from django.http import QueryDict

from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...terceirizada.models import Edital
from ..models import SolicitacaoDietaEspecial
from ..utils import (
    dietas_especiais_a_terminar,
    gera_logs_dietas_escolas_cei,
    gera_logs_dietas_escolas_comuns,
    gerar_filtros_relatorio_historico,
    termina_dietas_especiais,
    unidades_tipo_emebs,
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
    escola_cei, solicitacoes_dieta_especial_ativas_cei
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
    escola_cei, solicitacoes_dieta_especial_ativas_cei_com_solicitacao_medicao
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
    assert len(logs) == 12
    assert len([log for log in logs if log.periodo_escolar == None]) == 6
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


def test_gerar_filtros_relatorio_historico_retona_dicionario_vazio():
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

    filtros, _ = gerar_filtros_relatorio_historico(query_params)
    assert isinstance(filtros, dict)
    assert len(filtros) == 0


def test_unidades_tipo_emebs(escolas_tipo_emebs):
    item, classificacao = escolas_tipo_emebs
    classificacao_dieta = unidades_tipo_emebs(item, classificacao)

    assert isinstance(classificacao_dieta, dict)
    assert classificacao_dieta["total"] == 70
    assert "fundamental" in classificacao_dieta["periodos"]
    assert isinstance(classificacao_dieta["periodos"]["fundamental"], list)
    assert len(classificacao_dieta["periodos"]["fundamental"]) == 1
    periodo = classificacao_dieta["periodos"]["fundamental"][0]
    assert periodo["periodo"] == "TARDE"
    assert periodo["autorizadas"] == 30
