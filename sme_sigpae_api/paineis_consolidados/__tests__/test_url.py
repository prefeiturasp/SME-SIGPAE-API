import datetime

from freezegun import freeze_time
from rest_framework import status

from ...dados_comuns.constants import SEM_FILTRO
from ...escola.models import TipoUnidadeEscolar
from ...terceirizada.models import Terceirizada
from ..api.constants import (
    AGUARDANDO_CODAE,
    AUTORIZADOS,
    CANCELADOS,
    INCLUSOES_AUTORIZADAS,
    NEGADOS,
    PENDENTES_AUTORIZACAO,
    PENDENTES_VALIDACAO_DRE,
    PESQUISA,
    RELATORIO_PERIODO,
    RELATORIO_RESUMO_MES_ANO,
    RESUMO_ANO,
    RESUMO_MES,
    SUSPENSOES_AUTORIZADAS,
    TIPO_VISAO_SOLICITACOES,
)


def base_diretoria_regional(client_autenticado_dre, resource):
    endpoint = f"/diretoria-regional-solicitacoes/{resource}/"
    response = client_autenticado_dre.get(endpoint)
    assert response.status_code == status.HTTP_200_OK
    return response


def base_codae(client_autenticado, resource):
    endpoint = f"/codae-solicitacoes/{resource}/"
    response = client_autenticado.get(endpoint)
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_painel_dre_pendentes_validacao(
    client_autenticado_dre_paineis_consolidados,
):
    response = base_diretoria_regional(
        client_autenticado_dre_paineis_consolidados,
        f"{PENDENTES_VALIDACAO_DRE}/{SEM_FILTRO}/{TIPO_VISAO_SOLICITACOES}",
    )
    # TODO: Revisar esse teste, vive dando problema pois os valores sempre se alteram
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_painel_dre_aguardando_codae(
    client_autenticado_dre_paineis_consolidados,
):
    response = base_diretoria_regional(
        client_autenticado_dre_paineis_consolidados, f"{AGUARDANDO_CODAE}"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_painel_codae_pendentes_autorizacao(
    client_autenticado_codae_gestao_alimentacao,
):
    base_codae(
        client_autenticado_codae_gestao_alimentacao,
        f"{PENDENTES_AUTORIZACAO}/{SEM_FILTRO}",
    )


def test_url_endpoint_painel_codae_aprovados(
    client_autenticado_codae_gestao_alimentacao,
):
    base_codae(client_autenticado_codae_gestao_alimentacao, AUTORIZADOS)


def test_url_endpoint_painel_codae_cancelados(
    client_autenticado_codae_gestao_alimentacao,
):
    base_codae(client_autenticado_codae_gestao_alimentacao, CANCELADOS)


def test_url_endpoint_painel_codae_negados(client_autenticado_codae_gestao_alimentacao):
    base_codae(client_autenticado_codae_gestao_alimentacao, NEGADOS)


def test_ceu_gestao_periodos_com_solicitacoes_autorizadas(
    client_autenticado_escola_paineis_consolidados, escola, vinculo_periodo_alimentacao
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    response = client.get(
        "/escola-solicitacoes/ceu-gestao-periodos-com-solicitacoes-autorizadas/"
        f"?escola_uuid={escola.uuid}&mes=07&ano=2023"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["nome"] == "MANHA"


def test_inclusoes_normais_autorizadas(
    client_autenticado_escola_paineis_consolidados, escola
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    response = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=07&ano=2023"
        "&periodos_escolares[]=MANHA&excluir_inclusoes_continuas=true"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["numero_alunos"] == 100


def test_inclusoes_continuas_autorizadas(
    client_autenticado_escola_paineis_consolidados,
    escola,
    inclusao_alimentacao_continua_entre_dois_meses,
    inclusao_alimentacao_continua_unico_mes,
    inclusao_alimentacao_continua_varios_meses,
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    response_mes_03 = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=03&ano=2023"
        "&periodos_escolares[]=MANHA&periodos_escolares[]=TARDE&tipo_doc=INC_ALIMENTA_CONTINUA"
    )
    assert response_mes_03.status_code == status.HTTP_200_OK
    assert len(response_mes_03.data["results"]) == 12
    assert response_mes_03.data["results"][0]["dia"] == "20"
    assert response_mes_03.data["results"][0]["numero_alunos"] == 50
    assert (
        response_mes_03.data["results"][len(response_mes_03.data["results"]) - 1]["dia"]
        == "31"
    )

    response_mes_04 = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=04&ano=2023"
        "&periodos_escolares[]=MANHA&periodos_escolares[]=TARDE&tipo_doc=INC_ALIMENTA_CONTINUA"
    )
    assert response_mes_04.status_code == status.HTTP_200_OK
    assert len(response_mes_04.data["results"]) == 10
    assert response_mes_04.data["results"][0]["dia"] == "01"
    assert response_mes_04.data["results"][0]["numero_alunos"] == 50
    assert (
        response_mes_04.data["results"][len(response_mes_04.data["results"]) - 1]["dia"]
        == "10"
    )

    response_mes_02 = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=02&ano=2023"
        "&periodos_escolares[]=MANHA&periodos_escolares[]=TARDE&tipo_doc=INC_ALIMENTA_CONTINUA"
    )
    assert response_mes_02.status_code == status.HTTP_200_OK
    assert len(response_mes_02.data["results"]) == 21
    assert response_mes_02.data["results"][0]["dia"] == "05"
    assert response_mes_02.data["results"][0]["numero_alunos"] == 100
    assert (
        response_mes_02.data["results"][len(response_mes_02.data["results"]) - 1]["dia"]
        == "25"
    )

    response_mes_07 = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=07&ano=2023"
        "&periodos_escolares[]=MANHA&periodos_escolares[]=TARDE&tipo_doc=INC_ALIMENTA_CONTINUA"
    )
    assert response_mes_07.status_code == status.HTTP_200_OK
    assert len(response_mes_07.data["results"]) == 31
    assert response_mes_07.data["results"][0]["dia"] == "01"
    assert response_mes_07.data["results"][0]["numero_alunos"] == 75
    assert (
        response_mes_07.data["results"][len(response_mes_07.data["results"]) - 1]["dia"]
        == "31"
    )


def test_inclusoes_cei_autorizadas(
    client_autenticado_escola_paineis_consolidados, escola, inclusao_alimentacao_cei
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    response_manha = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=08&ano=2023"
        "&periodos_escolares[]=MANHA&excluir_inclusoes_continuas=true"
    )
    assert response_manha.status_code == status.HTTP_200_OK
    assert len(response_manha.data["results"]) == 0

    response_parcial = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=08&ano=2023"
        "&periodos_escolares[]=PARCIAL&excluir_inclusoes_continuas=true"
    )
    assert response_parcial.status_code == status.HTTP_200_OK
    assert len(response_parcial.data["results"]) == 1
    assert response_parcial.data["results"][0]["dia"] == 10

    response_integral = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=08&ano=2023"
        "&periodos_escolares[]=INTEGRAL&excluir_inclusoes_continuas=true"
    )
    assert response_integral.status_code == status.HTTP_200_OK
    assert len(response_integral.data["results"]) == 0

    response_tarde = client.get(
        f"/escola-solicitacoes/{INCLUSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Inclusão de&mes=08&ano=2023"
        "&periodos_escolares[]=TARDE&excluir_inclusoes_continuas=true"
    )
    assert response_tarde.status_code == status.HTTP_200_OK
    assert len(response_tarde.data["results"]) == 0


def test_suspensoes_autorizadas(
    client_autenticado_escola_paineis_consolidados, escola, suspensoes_alimentacao_cei
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    response_manha_cei = client.get(
        f"/escola-solicitacoes/{SUSPENSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Suspensão&mes=07&ano=2023"
        "&nome_periodo_escolar=MANHA"
    )
    assert response_manha_cei.status_code == status.HTTP_200_OK
    assert len(response_manha_cei.data["results"]) == 1
    assert response_manha_cei.data["results"][0]["dia"] == "15"
    assert response_manha_cei.data["results"][0]["periodo"] == "MANHA"

    response_parcial_cei = client.get(
        f"/escola-solicitacoes/{SUSPENSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Suspensão&mes=07&ano=2023"
        "&nome_periodo_escolar=PARCIAL"
    )
    assert response_parcial_cei.status_code == status.HTTP_200_OK
    assert len(response_parcial_cei.data["results"]) == 1
    assert response_parcial_cei.data["results"][0]["dia"] == "15"
    assert response_parcial_cei.data["results"][0]["periodo"] == "INTEGRAL"

    response_suspensao_manha = client.get(
        f"/escola-solicitacoes/{SUSPENSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Suspensão&mes=08&ano=2023"
        "&nome_periodo_escolar=MANHA"
    )
    assert response_suspensao_manha.status_code == status.HTTP_200_OK
    assert len(response_suspensao_manha.data["results"]) == 1
    assert response_suspensao_manha.data["results"][0]["numero_alunos"] == 75
    assert response_suspensao_manha.data["results"][0]["periodo"] == "MANHA"

    response_suspensao_integral = client.get(
        f"/escola-solicitacoes/{SUSPENSOES_AUTORIZADAS}/"
        f"?escola_uuid={escola.uuid}&tipo_solicitacao=Suspensão&mes=08&ano=2023"
        "&nome_periodo_escolar=INTEGRAL"
    )
    assert response_suspensao_integral.status_code == status.HTTP_200_OK
    assert len(response_suspensao_integral.data["results"]) == 1
    assert response_suspensao_integral.data["results"][0]["numero_alunos"] == 50
    assert response_suspensao_integral.data["results"][0]["periodo"] == "INTEGRAL"


def test_solicitacoes_detalhadas_inc_alimentacao(
    client_autenticado_escola_paineis_consolidados,
    inclusoes_normais,
    inclusao_alimentacao_continua_unico_mes,
    inclusao_alimentacao_cei,
    inclusao_alimentacao_cemei,
    eolservicosgp_get_lista_alunos,
    periodo_escolar_factory,
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    periodo_escolar_factory.create(tipo_turno=1, nome="INTEGRAL")
    response = client.get(
        "/solicitacoes-genericas/solicitacoes-detalhadas/"
        "?solicitacoes[]="
        "%7B%22tipo_doc%22:%22INC_ALIMENTA%22,%22uuid%22:%22a4639e26-f4fd-43e9-a8cc-2d0da995c8ef%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22INC_ALIMENTA_CONTINUA%22,%22uuid%22:%22ec27137e-9b8f-419c-adaa-7ed238d40bae%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22INC_ALIMENTA_CEI%22,%22uuid%22:%2250830aed-33ad-442a-8890-5b508e54a0d8%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22INC_ALIMENTA_CEMEI%22,%22uuid%22:%22ba5551b3-b770-412b-a923-b0e78301d1fd%22%7D"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) == 4


def test_solicitacoes_detalhadas_kit_lanche(
    client_autenticado_escola_paineis_consolidados,
    solicitacoes_kit_lanche,
    solicitacao_unificada,
    kit_lanche_cei,
    kit_lanche_cemei,
    eolservicosgp_get_lista_alunos,
    periodo_escolar_factory,
):
    client, usuario = client_autenticado_escola_paineis_consolidados
    periodo_escolar_factory.create(tipo_turno=1, nome="INTEGRAL")
    response = client.get(
        "/solicitacoes-genericas/solicitacoes-detalhadas/"
        "?solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_AVULSA%22,%22uuid%22:%22ac0b6f5b-36b0-47d2-99a2-3bc9825b31fb%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_AVULSA%22,%22uuid%22:%22d15f17d5-d4c5-47f5-a09a-55677dbc65bf%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_AVULSA%22,%22uuid%22:%22c9715ddb-7e95-4156-91a5-c60c8621806b%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_AVULSA%22,%22uuid%22:%228827b394-ef39-4757-8136-6e09d5c7c486%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_UNIFICADA%22,%22uuid%22:%22d0d3ec92-a2db-4060-a4da-b7ed9d88a7c3%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_AVULSA_CEI%22,%22uuid%22:%22318ca781-943a-4121-b970-70ac4d4ccc8a%22%7D"
        "&solicitacoes[]="
        "%7B%22tipo_doc%22:%22KIT_LANCHE_CEMEI%22,%22uuid%22:%222fdb22fe-370c-4379-94f4-a52478c03e6e%22%7D"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) == 7


def test_filtrar_solicitacoes_ga_cards_totalizadores_rede_municipal_educacao(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    keys = [list(dict_.keys())[0] for dict_ in response.json()["results"]]
    assert {"Rede Municipal de Educação": 5} in response.json()["results"]
    assert "Total" not in keys


def test_filtrar_solicitacoes_ga_cards_totalizadores_tipo_solicitacao(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {
        "status": "AUTORIZADOS",
        "tipos_solicitacao": ["INC_ALIMENTA", "KIT_LANCHE_AVULSA"],
    }
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert {"Total": 5} in results
    assert {"Kit Lanche Passeio": 4} in results
    assert {"Inclusão de Alimentação": 1} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_tipos_unidade(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "tipos_unidade": [escola.tipo_unidade.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert {"Total": 5} in results
    assert {escola.tipo_unidade.iniciais: 5} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_lotes(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "lotes": [escola.lote.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert {"Total": 5} in results
    assert {f"{escola.lote.nome} - {escola.lote.diretoria_regional.nome}": 5} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_unidade_educacional(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "unidades_educacionais": [escola.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert {"Total": 5} in results
    assert {escola.nome: 5} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_periodo_de(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "de": "01/01/2020"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert "Total" not in keys
    assert {"Período: a partir de 01/01/2020": 2} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_periodo_ate(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "ate": "01/01/2024"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert "Total" not in keys
    assert {"Período: até 01/01/2024": 5} in results


def test_filtrar_solicitacoes_ga_cards_totalizadores_periodo_de_ate(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS", "de": "01/01/2017", "ate": "01/01/2024"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-cards-totalizadores/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    keys = [list(dict_.keys())[0] for dict_ in results]

    assert "Rede Municipal de Educação" not in keys
    assert "Total" not in keys
    assert {"Período: 01/01/2017 até 01/01/2024": 5} in results


def test_filtrar_solicitacoes_ga_graficos(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    escola_outro_lote,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()[0]["labels"]) == 2

    data = {"status": "AUTORIZADOS", "unidades_educacionais": [escola.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()[0]["labels"]) == 6

    data = {"status": "AUTORIZADOS", "lotes": [escola.lote.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()[0]["labels"]) == 1


def test_filtrar_solicitacoes_ga_graficos_tipo_unidade(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    escola_outro_lote,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()[3]["datasets"][0]["label"]
        == "Total de Solicitações Autorizadas por Tipo de Unidade"
    )
    assert (
        len(response.json()[3]["labels"])
        == TipoUnidadeEscolar.objects.filter(
            pertence_relatorio_solicitacoes_alimentacao=True
        ).count()
    )

    data = {"status": "AUTORIZADOS", "tipos_unidade": [escola.tipo_unidade.uuid]}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()[3]["labels"]) == 1


def test_filtrar_solicitacoes_ga_graficos_empresa_terceirizada_codae(
    client_autenticado_codae_gestao_alimentacao,
    escola,
    escola_outro_lote,
    solicitacoes_kit_lanche_autorizadas,
    inclusoes_normais,
):
    data = {"status": "AUTORIZADOS"}
    response = client_autenticado_codae_gestao_alimentacao.post(
        "/solicitacoes-genericas/filtrar-solicitacoes-graficos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()[4]["datasets"][0]["label"]
        == "Total de Solicitações Autorizadas por Empresa Terceirizada"
    )
    assert (
        len(response.json()[4]["labels"])
        == Terceirizada.objects.filter(tipo_empresa=Terceirizada.TERCEIRIZADA).count()
    )


def test_exportar_xlsx(client_autenticado_vinculo_escola):
    data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    response = client_autenticado_vinculo_escola.post(
        "/escola-solicitacoes/exportar-xlsx/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["detail"]
        == "Solicitação de geração de arquivo recebida com sucesso."
    )


def test_exportar_pdf(client_autenticado_vinculo_escola):
    data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    response = client_autenticado_vinculo_escola.post(
        "/escola-solicitacoes/exportar-pdf/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["detail"]
        == "Solicitação de geração de arquivo recebida com sucesso."
    )
