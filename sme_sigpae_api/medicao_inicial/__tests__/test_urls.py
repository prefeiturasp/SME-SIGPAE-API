import datetime
import json

import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.medicao_inicial.models import (
    DiaParaCorrigir,
    DiaSobremesaDoce,
    Empenho,
    Medicao,
)


def test_url_endpoint_cria_dias_sobremesa_doce(client_autenticado_coordenador_codae):
    data = {
        "data": "2022-08-08",
        "cadastros_calendario": [
            {
                "editais": [
                    "85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
                    "10b56d45-b82d-4cce-9a14-36bbb082ac4d",
                ],
                "tipo_unidades": [
                    "1cc3253b-e297-42b3-8e57-ebfd115a1aba",
                    "40ee89a7-dc70-4abb-ae21-369c67f2b9e3",
                ],
            },
            {
                "editais": [
                    "85d4bdf1-79d3-4f93-87d7-9999ae4cd9c2",
                    "00f008ea-3410-4547-99e6-4e91e0168af8",
                ],
                "tipo_unidades": [
                    "ac4858ff-1c11-41f3-b539-7a02696d6d1b",
                ],
            },
        ],
    }
    response = client_autenticado_coordenador_codae.post(
        "/medicao-inicial/dias-sobremesa-doce/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSobremesaDoce.objects.count() == 6

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/dias-sobremesa-doce/lista-dias/?mes=8&ano=2022"
        "&escola_uuid=95ad02fb-d746-4e0c-95f4-0181a99bc192",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/dias-sobremesa-doce/?mes=8&ano=2022",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 6
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/dias-sobremesa-doce/?mes=9&ano=2022",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0
    data = {"data": "2022-08-08", "cadastros_calendario": []}
    response = client_autenticado_coordenador_codae.post(
        "/medicao-inicial/dias-sobremesa-doce/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert DiaSobremesaDoce.objects.count() == 0


def test_url_endpoint_list_dias_erro(client_autenticado_coordenador_codae):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/dias-sobremesa-doce/lista-dias/?mes=8&ano=2022"
        "&escola_uuid=95ad02fb-d746-4e0c-95f4-0181a99bc193",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_solicitacao_medicao_inicial(
    client_autenticado_da_escola,
    escola,
    solicitacao_medicao_inicial,
    solicitacao_medicao_inicial_sem_arquivo,
    responsavel,
    tipo_contagem_alimentacao,
    aluno,
    faixas_etarias_ativas,
    periodos_integral_parcial_e_logs,
):
    assert escola.modulo_gestao == "TERCEIRIZADA"
    response = client_autenticado_da_escola.get(
        f"/medicao-inicial/solicitacao-medicao-inicial/?escola={escola.uuid}&mes=09&ano=2022",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0
    data_create = {
        "ano": 2022,
        "mes": 11,
        "escola": escola.uuid,
        "responsaveis": [{"nome": responsavel.nome, "rf": responsavel.rf}],
        "tipo_contagem_alimentacoes": [tipo_contagem_alimentacao.uuid],
        "alunos_periodo_parcial": [
            {"aluno": aluno.uuid, "data": "05/12/2022", "data_removido": "10/12/2022"}
        ],
    }
    response = client_autenticado_da_escola.post(
        "/medicao-inicial/solicitacao-medicao-inicial/",
        content_type="application/json",
        data=data_create,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data_update = {
        "escola": str(escola.uuid),
        "tipo_contagem_alimentacoes[]": [tipo_contagem_alimentacao.uuid],
        "com_ocorrencias": True,
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_sem_arquivo.uuid}/",
        content_type="application/json",
        data=data_update,
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_nao_tem_permissao_para_encerrar_medicao(
    client_autenticado_adm_da_escola,
    escola,
    solicitacao_medicao_inicial,
    solicitacao_medicao_inicial_sem_arquivo,
    responsavel,
    tipo_contagem_alimentacao,
):
    data_update = {
        "escola": str(escola.uuid),
        "tipo_contagem_alimentacoes": str(tipo_contagem_alimentacao.uuid),
        "com_ocorrencias": True,
        "finaliza_medicao": True,
    }
    response = client_autenticado_adm_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_sem_arquivo.uuid}/",
        content_type="application/json",
        data=data_update,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    json = response.json()
    assert json == {"detail": "Você não tem permissão para executar essa ação."}


def test_url_endpoint_valores_medicao_com_grupo(
    client_autenticado_da_escola, solicitacao_medicao_inicial_com_grupo
):
    url = "/medicao-inicial/valores-medicao/?nome_periodo_escolar=MANHA&nome_grupo=Programas e Projetos"
    url += f"&uuid_solicitacao_medicao={solicitacao_medicao_inicial_com_grupo.uuid}"
    response = client_autenticado_da_escola.get(url, content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_url_endpoint_valores_medicao(
    client_autenticado_da_escola, solicitacao_medicao_inicial
):
    url = "/medicao-inicial/valores-medicao/?nome_periodo_escolar=MANHA"
    url += f"&uuid_solicitacao_medicao={solicitacao_medicao_inicial.uuid}"
    response = client_autenticado_da_escola.get(url, content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_url_endpoint_medicao(
    client_autenticado_da_escola,
    solicitacao_medicao_inicial,
    periodo_escolar,
    categoria_medicao,
    medicao,
):
    data = {
        "periodo_escolar": periodo_escolar.nome,
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "valores_medicao": [
            {
                "categoria_medicao": categoria_medicao.id,
                "dia": "01",
                "nome_campo": "repeticao_refeicao",
                "tipo_alimentacao": "",
                "valor": "100",
            }
        ],
    }
    response = client_autenticado_da_escola.post(
        "/medicao-inicial/medicao/", content_type="application/json", data=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/medicao/{medicao.uuid}/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    data_valor_0 = {
        "periodo_escolar": periodo_escolar.nome,
        "solicitacao_medicao_inicial": solicitacao_medicao_inicial.uuid,
        "valores_medicao": [
            {
                "categoria_medicao": categoria_medicao.id,
                "dia": "01",
                "nome_campo": "repeticao_refeicao",
                "tipo_alimentacao": "",
                "valor": 0,
            }
        ],
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/medicao/{medicao.uuid}/",
        content_type="application/json",
        data=data_valor_0,
    )
    assert response.status_code == status.HTTP_200_OK

    response = client_autenticado_da_escola.delete(
        f"/medicao-inicial/valores-medicao/{medicao.valores_medicao.first().uuid}/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@freeze_time("2022-07-25")
def test_url_endpoint_feriados_no_mes(client_autenticado_da_escola):
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/medicao/feriados-no-mes/?mes=09&ano=2022",
        content_type="application/json",
    )
    assert response.data["results"] == ["07"]
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_meses_anos(
    client_autenticado_diretoria_regional, solicitacoes_medicao_inicial
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/meses-anos/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 4


def test_url_endpoint_periodos_grupos_medicao(
    client_autenticado_diretoria_regional,
    solicitacao_medicao_inicial_com_valores_repeticao,
):
    uuid_solicitacao = solicitacao_medicao_inicial_com_valores_repeticao.uuid
    response = client_autenticado_diretoria_regional.get(
        f"/medicao-inicial/solicitacao-medicao-inicial/periodos-grupos-medicao/?uuid_solicitacao={uuid_solicitacao}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert [r["periodo_escolar"] for r in results] == [
        "MANHA",
        "TARDE",
        "INTEGRAL",
        "NOITE",
        None,
        None,
        None,
    ]
    assert [r["grupo"] for r in results] == [
        None,
        None,
        None,
        None,
        "Programas e Projetos",
        "Solicitações de Alimentação",
        "ETEC",
    ]
    assert [r["nome_periodo_grupo"] for r in results] == [
        "MANHA",
        "TARDE",
        "INTEGRAL",
        "NOITE",
        "Programas e Projetos",
        "Solicitações de Alimentação",
        "ETEC",
    ]


def test_url_endpoint_quantidades_alimentacoes_lancadas_periodo_grupo_escola_comum(
    client_autenticado_da_escola, solicitacao_medicao_inicial_com_valores_repeticao
):
    uuid_solicitacao = solicitacao_medicao_inicial_com_valores_repeticao.uuid
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/solicitacao-medicao-inicial/quantidades-alimentacoes-lancadas-periodo-grupo/"
        f"?uuid_solicitacao={uuid_solicitacao}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        len([r for r in response.data["results"] if r["nome_periodo_grupo"] == "MANHA"])
        == 1
    )
    assert [r for r in response.data["results"] if r["nome_periodo_grupo"] == "MANHA"][
        0
    ]["valor_total"] == 350


def test_url_endpoint_quantidades_alimentacoes_lancadas_periodo_grupo_escola_cei(
    client_autenticado_da_escola_cei,
    solicitacao_medicao_inicial_varios_valores_escola_cei,
):
    uuid_solicitacao = solicitacao_medicao_inicial_varios_valores_escola_cei.uuid
    response = client_autenticado_da_escola_cei.get(
        "/medicao-inicial/solicitacao-medicao-inicial/quantidades-alimentacoes-lancadas-periodo-grupo/"
        f"?uuid_solicitacao={uuid_solicitacao}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        len(
            [
                r
                for r in response.data["results"]
                if r["nome_periodo_grupo"] == "INTEGRAL"
            ]
        )
        == 1
    )
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "INTEGRAL"
    ][0]["quantidade_alunos"] == 20
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "INTEGRAL"
    ][0]["valor_total"] == 100
    assert (
        len(
            [
                r
                for r in response.data["results"]
                if r["nome_periodo_grupo"] == "PARCIAL"
            ]
        )
        == 1
    )
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "PARCIAL"
    ][0]["quantidade_alunos"] == 36
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "PARCIAL"
    ][0]["valor_total"] == 108
    assert (
        len([r for r in response.data["results"] if r["nome_periodo_grupo"] == "TARDE"])
        == 1
    )
    assert [r for r in response.data["results"] if r["nome_periodo_grupo"] == "TARDE"][
        0
    ]["quantidade_alunos"] == 52
    assert [r for r in response.data["results"] if r["nome_periodo_grupo"] == "TARDE"][
        0
    ]["valor_total"] == 104


def test_url_endpoint_quantidades_alimentacoes_lancadas_periodo_grupo_escola_cemei(
    client_autenticado_da_escola_cemei,
    solicitacao_medicao_inicial_varios_valores_escola_cemei,
):
    uuid_solicitacao = solicitacao_medicao_inicial_varios_valores_escola_cemei.uuid
    response = client_autenticado_da_escola_cemei.get(
        "/medicao-inicial/solicitacao-medicao-inicial/quantidades-alimentacoes-lancadas-periodo-grupo/"
        f"?uuid_solicitacao={uuid_solicitacao}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        len(
            [
                r
                for r in response.data["results"]
                if r["nome_periodo_grupo"] == "INTEGRAL"
            ]
        )
        == 1
    )
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "INTEGRAL"
    ][0]["quantidade_alunos"] == 30
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "INTEGRAL"
    ][0]["valor_total"] == 150
    assert (
        len(
            [
                r
                for r in response.data["results"]
                if r["nome_periodo_grupo"] == "PARCIAL"
            ]
        )
        == 1
    )
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "PARCIAL"
    ][0]["quantidade_alunos"] == 60
    assert [
        r for r in response.data["results"] if r["nome_periodo_grupo"] == "PARCIAL"
    ][0]["valor_total"] == 180
    assert (
        len(
            [
                r
                for r in response.data["results"]
                if r["nome_periodo_grupo"] == "Infantil MANHA"
            ]
        )
        == 1
    )
    with pytest.raises(KeyError):
        [
            r
            for r in response.data["results"]
            if r["nome_periodo_grupo"] == "Infantil MANHA"
        ][0]["quantidade_alunos"]
    assert [
        r
        for r in response.data["results"]
        if r["nome_periodo_grupo"] == "Infantil MANHA"
    ][0]["valor_total"] == 80


def test_url_endpoint_relatorio_pdf(
    client_autenticado_da_escola, solicitacao_medicao_inicial_com_valores_repeticao
):
    uuid_solicitacao = solicitacao_medicao_inicial_com_valores_repeticao.uuid
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/solicitacao-medicao-inicial/relatorio-pdf/"
        f"?uuid={uuid_solicitacao}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "detail": "Solicitação de geração de arquivo recebida com sucesso."
    }


def test_url_endpoint_relatorio_unificado_pdf_sem_mes_referencia(
    client_autenticado_diretoria_regional,
    grupo_escolar,
    escola,
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/relatorio-unificado/"
        f"?grupo_escolar={grupo_escolar}&status=MEDICAO_APROVADA_PELA_CODAE&dre={escola.diretoria_regional.uuid}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == "É necessário informar o mês/ano de referência"


def test_url_endpoint_relatorio_unificado_pdf(
    client_autenticado_diretoria_regional,
    grupo_escolar,
    escola,
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/relatorio-unificado/"
        f"?mes=05&ano=2023&grupo_escolar={grupo_escolar}&status=MEDICAO_APROVADA_PELA_CODAE&dre={escola.diretoria_regional.uuid}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "erro": "Não foram encontradas Medições Iniciais para o grupo e mês de referência selecionados"
    }


def test_url_endpoint_medicao_dashboard_dre(
    client_autenticado_diretoria_regional, solicitacoes_medicao_inicial
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 9
    assert response.json()["results"][1]["status"] == "MEDICAO_ENVIADA_PELA_UE"
    assert response.json()["results"][1]["total"] == 2
    assert response.json()["results"][2]["status"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert response.json()["results"][2]["total"] == 1
    assert response.json()["results"][7]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][7]["total"] == 0
    assert response.json()["results"][8]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][8]["total"] == 4


def test_url_endpoint_medicao_dashboard_dre_com_filtros(
    client_autenticado_diretoria_regional, solicitacoes_medicao_inicial
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/?status=MEDICAO_ENVIADA_PELA_UE",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 9
    assert response.json()["results"][1]["status"] == "MEDICAO_ENVIADA_PELA_UE"
    assert response.json()["results"][1]["total"] == 2
    assert response.json()["results"][2]["status"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert response.json()["results"][2]["total"] == 1
    assert response.json()["results"][7]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][7]["total"] == 0
    assert response.json()["results"][8]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][8]["total"] == 4


def test_url_endpoint_medicao_dashboard_escola(
    client_autenticado_da_escola, solicitacoes_medicao_inicial
):
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 7
    assert response.json()["results"][0]["status"] == "MEDICAO_ENVIADA_PELA_UE"
    assert response.json()["results"][0]["total"] == 2
    assert response.json()["results"][1]["status"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert response.json()["results"][1]["total"] == 1
    assert response.json()["results"][5]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][5]["total"] == 0
    assert response.json()["results"][6]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][6]["total"] == 3


def test_url_endpoint_medicao_dashboard_escola_com_filtros(
    client_autenticado_da_escola, solicitacoes_medicao_inicial
):
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/?status=MEDICAO_ENVIADA_PELA_UE",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 7
    assert response.json()["results"][0]["status"] == "MEDICAO_ENVIADA_PELA_UE"
    assert response.json()["results"][0]["total"] == 2
    assert response.json()["results"][1]["status"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert response.json()["results"][1]["total"] == 1
    assert response.json()["results"][5]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][5]["total"] == 0
    assert response.json()["results"][6]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][6]["total"] == 3


def test_url_endpoint_medicao_dashboard_codae(
    client_autenticado_coordenador_codae, solicitacoes_medicao_inicial_codae
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 5
    assert response.json()["results"][0]["status"] == "MEDICAO_APROVADA_PELA_DRE"
    assert response.json()["results"][0]["total"] == 2
    assert (
        response.json()["results"][1]["status"] == "MEDICAO_CORRECAO_SOLICITADA_CODAE"
    )
    assert response.json()["results"][1]["total"] == 1
    assert response.json()["results"][2]["status"] == "MEDICAO_CORRIGIDA_PARA_CODAE"
    assert response.json()["results"][2]["total"] == 1
    assert response.json()["results"][3]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][3]["total"] == 1
    assert response.json()["results"][4]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][4]["total"] == 5


def test_url_endpoint_medicao_dashboard_codae_com_filtros(
    client_autenticado_coordenador_codae, solicitacoes_medicao_inicial_codae
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard/?dre=3972e0e9-2d8e-472a-9dfa-30cd219a6d9a",
        content_type="application/json",
    )
    assert len(response.json()["results"]) == 5
    assert response.json()["results"][0]["status"] == "MEDICAO_APROVADA_PELA_DRE"
    assert response.json()["results"][0]["total"] == 2
    assert (
        response.json()["results"][1]["status"] == "MEDICAO_CORRECAO_SOLICITADA_CODAE"
    )
    assert response.json()["results"][1]["total"] == 1
    assert response.json()["results"][2]["status"] == "MEDICAO_CORRIGIDA_PARA_CODAE"
    assert response.json()["results"][2]["total"] == 1
    assert response.json()["results"][3]["status"] == "MEDICAO_APROVADA_PELA_CODAE"
    assert response.json()["results"][3]["total"] == 1
    assert response.json()["results"][4]["status"] == "TODOS_OS_LANCAMENTOS"
    assert response.json()["results"][4]["total"] == 5


def test_url_dre_aprova_medicao(
    client_autenticado_diretoria_regional,
    medicao_status_enviada_pela_ue,
    medicao_aprovada_pela_dre,
):
    viewset_url = "/medicao-inicial/medicao/"
    uuid = medicao_status_enviada_pela_ue.uuid
    response = client_autenticado_diretoria_regional.patch(
        f"{viewset_url}{uuid}/dre-aprova-medicao/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "MEDICAO_APROVADA_PELA_DRE"

    uuid = medicao_aprovada_pela_dre.uuid
    response = client_autenticado_diretoria_regional.patch(
        f"{viewset_url}{uuid}/dre-aprova-medicao/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_dre_solicita_correcao_periodo(
    client_autenticado_diretoria_regional,
    medicao_status_enviada_pela_ue,
    medicao_status_inicial,
    categoria_medicao,
):
    data = {
        "uuids_valores_medicao_para_correcao": ["0b599490-477f-487b-a49e-c8e7cfdcd00b"],
        "justificativa": "<p>TESTE JUSTIFICATIVA</p>",
        "dias_para_corrigir": [
            {"dia": "01", "categoria_medicao_uuid": str(categoria_medicao.uuid)},
            {"dia": "10", "categoria_medicao_uuid": str(categoria_medicao.uuid)},
        ],
    }
    viewset_url = "/medicao-inicial/medicao/"
    uuid = medicao_status_enviada_pela_ue.uuid
    response = client_autenticado_diretoria_regional.patch(
        f"{viewset_url}{uuid}/dre-pede-correcao-medicao/",
        content_type="application/json",
        data=data,
    )

    medicao_uuid = str(response.data["valores_medicao"][0]["medicao_uuid"])
    medicao = Medicao.objects.filter(uuid=medicao_uuid).first()
    assert DiaParaCorrigir.objects.count() == 2

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "MEDICAO_CORRECAO_SOLICITADA"
    assert medicao.logs.last().justificativa == data["justificativa"]

    data["uuids_valores_medicao_para_correcao"] = [
        "128f36e2-ea93-4e05-9641-50b0c79ddb5e"
    ]
    uuid = medicao_status_inicial.uuid
    response = client_autenticado_diretoria_regional.patch(
        f"{viewset_url}{uuid}/dre-pede-correcao-medicao/",
        content_type="application/json",
        data=data,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_escola_corrige_medicao_para_dre_sucesso(
    client_autenticado_da_escola,
    solicitacao_medicao_inicial_medicao_correcao_solicitada,
):
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_correcao_solicitada.uuid}/"
        f"escola-corrige-medicao-para-dre/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_correcao_solicitada.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_correcao_solicitada.status
        == solicitacao_medicao_inicial_medicao_correcao_solicitada.workflow_class.MEDICAO_CORRIGIDA_PELA_UE
    )

    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_correcao_solicitada.uuid}/"
        f"escola-corrige-medicao-para-dre/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: solicitação já está no status Corrigido para DRE"
    }


def test_url_escola_corrige_medicao_para_dre_erro_transicao(
    client_autenticado_da_escola, solicitacao_medicao_inicial
):
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"escola-corrige-medicao-para-dre/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'ue_corrige' isn't available from state "
        "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE'."
    }


def test_url_escola_corrige_medicao_para_dre_erro_403(
    client_autenticado_diretoria_regional, solicitacao_medicao_inicial
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"escola-corrige-medicao-para-dre/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dre_solicita_correcao_medicao(
    client_autenticado_diretoria_regional,
    solicitacao_medicao_inicial_medicao_enviada_pela_ue,
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_enviada_pela_ue.uuid}/"
        f"dre-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_enviada_pela_ue.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_enviada_pela_ue.status
        == solicitacao_medicao_inicial_medicao_enviada_pela_ue.workflow_class.MEDICAO_CORRECAO_SOLICITADA
    )


def test_url_dre_solicita_correcao_medicao_erro_transicao(
    client_autenticado_diretoria_regional, solicitacao_medicao_inicial
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"dre-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_pede_correcao' isn't available from state "
        "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE'."
    }


def test_url_dre_solicita_correcao_medicao_erro_403(
    client_autenticado_da_escola, solicitacao_medicao_inicial_medicao_enviada_pela_ue
):
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_enviada_pela_ue.uuid}/"
        f"dre-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dre_solicita_correcao_ocorrencia(
    client_autenticado_diretoria_regional,
    anexo_ocorrencia_medicao_inicial,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    data = {"justificativa": "TESTE JUSTIFICATIVA"}
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/ocorrencia/{anexo_ocorrencia_medicao_inicial.uuid}/dre-pede-correcao-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.data["logs"][-1]["status_evento_explicacao"] == "Correção solicitada"
    )
    assert response.data["logs"][-1]["justificativa"] == data["justificativa"]

    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/ocorrencia/{anexo_ocorrencia_medicao_inicial_status_inicial.uuid}"
        f"/dre-pede-correcao-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_dre_aprova_ocorrencia(
    client_autenticado_diretoria_regional,
    anexo_ocorrencia_medicao_inicial,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/ocorrencia/{anexo_ocorrencia_medicao_inicial.uuid}/dre-aprova-ocorrencia/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["logs"][-1]["status_evento_explicacao"] == "Aprovado pela DRE"

    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/ocorrencia/{anexo_ocorrencia_medicao_inicial_status_inicial.uuid}"
        f"/dre-pede-correcao-ocorrencia/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_ue_atualiza_ocorrencia_para_dre(
    client_autenticado_da_escola,
    sol_med_inicial_devolvida_pela_dre_para_ue,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    solicitacao = sol_med_inicial_devolvida_pela_dre_para_ue
    data = {"com_ocorrencias": "false", "justificativa": "TESTE 1"}
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["com_ocorrencias"] is False
    assert len(response.data["ocorrencia"]["logs"][-1]["anexos"]) == 0
    assert (
        response.data["ocorrencia"]["logs"][-1]["status_evento_explicacao"]
        == "Corrigido para DRE"
    )

    anexos = [
        {"nome": "2.pdf", "base64": "data:application/pdf;base64,"},
        {
            "nome": "1.xlsx",
            "base64": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,",
        },
    ]
    anexos_json_string = json.dumps(anexos)
    data = {
        "com_ocorrencias": "true",
        "justificativa": "TESTE 2",
        "anexos": anexos_json_string,
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["com_ocorrencias"] is True
    assert len(response.data["ocorrencia"]["logs"][-1]["anexos"]) == 2
    assert (
        response.data["ocorrencia"]["logs"][-1]["status_evento_explicacao"]
        == "Corrigido para DRE"
    )

    solicitacao = (
        anexo_ocorrencia_medicao_inicial_status_inicial.solicitacao_medicao_inicial
    )
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_ue_atualiza_ocorrencia_para_codae(
    client_autenticado_da_escola,
    sol_med_inicial_devolvida_pela_codae_para_ue,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    solicitacao = sol_med_inicial_devolvida_pela_codae_para_ue
    data = {"com_ocorrencias": "false", "justificativa": "TESTE 1"}
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["com_ocorrencias"] is False
    assert len(response.data["ocorrencia"]["logs"][-1]["anexos"]) == 0
    assert (
        response.data["ocorrencia"]["logs"][-1]["status_evento_explicacao"]
        == "Corrigido para CODAE"
    )

    anexos = [
        {"nome": "2.pdf", "base64": "data:application/pdf;base64,"},
        {
            "nome": "1.xlsx",
            "base64": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,",
        },
    ]
    anexos_json_string = json.dumps(anexos)
    data = {
        "com_ocorrencias": "true",
        "justificativa": "TESTE 2",
        "anexos": anexos_json_string,
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["com_ocorrencias"] is True
    assert len(response.data["ocorrencia"]["logs"][-1]["anexos"]) == 2
    assert (
        response.data["ocorrencia"]["logs"][-1]["status_evento_explicacao"]
        == "Corrigido para CODAE"
    )

    solicitacao = (
        anexo_ocorrencia_medicao_inicial_status_inicial.solicitacao_medicao_inicial
    )
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao.uuid}/ue-atualiza-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


@freeze_time("2023-07-18")
def test_url_endpoint_solicitacoes_lancadas(
    client_autenticado_da_escola, escola, solicitacoes_medicao_inicial
):
    assert escola.modulo_gestao == "TERCEIRIZADA"
    response = client_autenticado_da_escola.get(
        f"/medicao-inicial/solicitacao-medicao-inicial/solicitacoes-lancadas/?escola={escola.uuid}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


def test_url_dre_aprova_solicitacao_medicao(
    client_autenticado_diretoria_regional,
    solicitacao_medicao_inicial_medicao_enviada_pela_ue,
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_enviada_pela_ue.uuid}/"
        f"dre-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_enviada_pela_ue.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_enviada_pela_ue.status
        == solicitacao_medicao_inicial_medicao_enviada_pela_ue.workflow_class.MEDICAO_APROVADA_PELA_DRE
    )


def test_url_dre_aprova_solicitacao_medicao_erro_pendencias(
    client_autenticado_diretoria_regional,
    solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok,
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok.uuid}/"
        f"dre-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Erro: existe(m) pendência(s) de análise"}


def test_url_dre_aprova_solicitacao_medicao_erro_transicao(
    client_autenticado_diretoria_regional,
    solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok__2,
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/"
        f"{solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok__2.uuid}/"
        f"dre-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'dre_aprova' isn't available from state "
        "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE'."
    }


def test_url_codae_aprova_solicitacao_medicao(
    client_autenticado_codae_medicao,
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok,
):
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.uuid}/"
        f"codae-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.status
        == solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.workflow_class.MEDICAO_APROVADA_PELA_CODAE
    )


def test_url_codae_aprova_solicitacao_medicao_erro_pendencias(
    client_autenticado_codae_medicao,
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_nok,
):
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/"
        f"{solicitacao_medicao_inicial_medicao_aprovada_pela_dre_nok.uuid}/"
        f"codae-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Erro: existe(m) pendência(s) de análise"}


def test_url_codae_aprova_solicitacao_medicao_erro_transicao(
    client_autenticado_codae_medicao,
    solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok,
):
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_enviada_pela_ue_nok.uuid}/"
        f"codae-aprova-solicitacao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_aprova_medicao' isn't available from state "
        "'MEDICAO_ENVIADA_PELA_UE'."
    }


def test_url_codae_solicita_correcao_medicao(
    client_autenticado_codae_medicao,
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok,
):
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.uuid}/"
        f"codae-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.status
        == solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE
    )


def test_url_codae_solicita_correcao_medicao_erro_transicao(
    client_autenticado_codae_medicao, solicitacao_medicao_inicial
):
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"codae-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'codae_pede_correcao_medicao' isn't available from state "
        "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE'."
    }


def test_url_codae_solicita_correcao_medicao_erro_403(
    client_autenticado_da_escola,
    solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok,
):
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_medicao_aprovada_pela_dre_ok.uuid}/"
        f"codae-solicita-correcao-medicao/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_codae_solicita_correcao_ocorrencia(
    client_autenticado_codae_medicao,
    anexo_ocorrencia_medicao_inicial_status_aprovado_dre,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    data = {"justificativa": "TESTE JUSTIFICATIVA"}
    viewset_url = "/medicao-inicial/ocorrencia/"
    uuid = anexo_ocorrencia_medicao_inicial_status_aprovado_dre.uuid
    response = client_autenticado_codae_medicao.patch(
        f"{viewset_url}{uuid}/codae-pede-correcao-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.data["logs"][-1]["status_evento_explicacao"]
        == "Correção solicitada pela CODAE"
    )
    assert response.data["logs"][-1]["justificativa"] == data["justificativa"]

    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/ocorrencia/{anexo_ocorrencia_medicao_inicial_status_inicial.uuid}"
        f"/dre-pede-correcao-ocorrencia/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_codae_solicita_correcao_periodo(
    client_autenticado_codae_medicao, medicao_aprovada_pela_dre, medicao_status_inicial
):
    data = {
        "uuids_valores_medicao_para_correcao": ["0b599490-477f-487b-a49e-c8e7cfdcd00b"],
        "justificativa": "<p>TESTE JUSTIFICATIVA</p>",
    }
    viewset_url = "/medicao-inicial/medicao/"
    uuid = medicao_aprovada_pela_dre.uuid
    response = client_autenticado_codae_medicao.patch(
        f"{viewset_url}{uuid}/codae-pede-correcao-periodo/",
        content_type="application/json",
        data=data,
    )

    medicao_uuid = str(response.data["valores_medicao"][0]["medicao_uuid"])
    medicao = Medicao.objects.filter(uuid=medicao_uuid).first()

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "MEDICAO_CORRECAO_SOLICITADA_CODAE"
    assert medicao.logs.last().justificativa == data["justificativa"]

    data["uuids_valores_medicao_para_correcao"] = [
        "128f36e2-ea93-4e05-9641-50b0c79ddb5e"
    ]
    uuid = medicao_status_inicial.uuid
    response = client_autenticado_codae_medicao.patch(
        f"{viewset_url}{uuid}/codae-pede-correcao-periodo/",
        content_type="application/json",
        data=data,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_escola_corrige_medicao_para_codae_sucesso(
    client_autenticado_da_escola,
    solicitacao_medicao_inicial_medicao_correcao_solicitada_codae,
):
    response = client_autenticado_da_escola.patch(
        "/medicao-inicial/solicitacao-medicao-inicial/"
        f"{solicitacao_medicao_inicial_medicao_correcao_solicitada_codae.uuid}/"
        f"escola-corrige-medicao-para-codae/"
    )
    assert response.status_code == status.HTTP_200_OK
    solicitacao_medicao_inicial_medicao_correcao_solicitada_codae.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_medicao_correcao_solicitada_codae.status
        == solicitacao_medicao_inicial_medicao_correcao_solicitada_codae.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE
    )

    response = client_autenticado_da_escola.patch(
        "/medicao-inicial/solicitacao-medicao-inicial/"
        f"{solicitacao_medicao_inicial_medicao_correcao_solicitada_codae.uuid}/"
        f"escola-corrige-medicao-para-codae/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: solicitação já está no status Corrigido para CODAE"
    }


def test_url_escola_corrige_medicao_para_codae_erro_transicao(
    client_autenticado_da_escola, solicitacao_medicao_inicial
):
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"escola-corrige-medicao-para-codae/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Erro de transição de estado: Transition 'ue_corrige_medicao_para_codae' isn't available from state "
        "'MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE'."
    }


def test_url_escola_corrige_medicao_para_codae_erro_403(
    client_autenticado_diretoria_regional, solicitacao_medicao_inicial
):
    response = client_autenticado_diretoria_regional.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial.uuid}/"
        f"escola-corrige-medicao-para-codae/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_codae_aprova_ocorrencia(
    client_autenticado_codae_medicao,
    anexo_ocorrencia_medicao_inicial_status_aprovado_dre,
    anexo_ocorrencia_medicao_inicial_status_inicial,
):
    uuid = anexo_ocorrencia_medicao_inicial_status_aprovado_dre.uuid
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/ocorrencia/{uuid}/codae-aprova-ocorrencia/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.data["logs"][-1]["status_evento_explicacao"] == "Aprovado pela CODAE"
    )

    uuid = anexo_ocorrencia_medicao_inicial_status_inicial.uuid
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/ocorrencia/{uuid}" f"/codae-pede-correcao-ocorrencia/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_codae_aprova_periodo(
    client_autenticado_codae_medicao, medicao_aprovada_pela_dre, medicao_status_inicial
):
    viewset_url = "/medicao-inicial/medicao/"
    uuid = medicao_aprovada_pela_dre.uuid
    response = client_autenticado_codae_medicao.patch(
        f"{viewset_url}{uuid}/codae-aprova-periodo/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "MEDICAO_APROVADA_PELA_CODAE"

    uuid = medicao_status_inicial.uuid
    response = client_autenticado_codae_medicao.patch(
        f"{viewset_url}{uuid}/codae-aprova-periodo/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erro de transição de estado:" in response.data["detail"]


def test_url_ceu_gestao_frequencias_dietas(
    client_autenticado_da_escola, solicitacao_medicao_inicial_com_grupo
):
    response = client_autenticado_da_escola.get(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_com_grupo.uuid}"
        f"/ceu-gestao-frequencias-dietas/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_finaliza_medicao_inicial_salva_logs(
    client_autenticado_da_escola,
    solicitacao_medicao_inicial_teste_salvar_logs,
    periodo_escolar_manha,
    periodo_escolar_tarde,
    periodo_escolar_noite,
):
    tipos_contagem = (
        solicitacao_medicao_inicial_teste_salvar_logs.tipos_contagem_alimentacao.all()
    )
    tipos_contagem_uuids = tipos_contagem.values_list("uuid", flat=True)
    tipos_contagem_uuids = [str(uuid) for uuid in tipos_contagem_uuids]
    data_update = {
        "escola": str(solicitacao_medicao_inicial_teste_salvar_logs.escola.uuid),
        "tipo_contagem_alimentacoes[]": tipos_contagem_uuids,
        "com_ocorrencias": False,
        "finaliza_medicao": True,
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_teste_salvar_logs.uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_200_OK

    solicitacao_medicao_inicial_teste_salvar_logs.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_teste_salvar_logs.status
        == "MEDICAO_ENVIADA_PELA_UE"
    )
    assert solicitacao_medicao_inicial_teste_salvar_logs.logs_salvos is True

    medicao_manha = solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
        periodo_escolar=periodo_escolar_manha
    )
    assert (
        medicao_manha.valores_medicao.filter(
            nome_campo="matriculados", categoria_medicao__nome="ALIMENTAÇÃO"
        ).count()
        == 30
    )
    assert (
        medicao_manha.valores_medicao.filter(
            nome_campo="dietas_autorizadas",
            categoria_medicao__nome="DIETA ESPECIAL - TIPO A",
        ).count()
        == 30
    )
    assert (
        medicao_manha.valores_medicao.filter(
            nome_campo="dietas_autorizadas",
            categoria_medicao__nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        ).count()
        == 30
    )

    medicao_tarde = solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
        periodo_escolar=periodo_escolar_tarde
    )
    assert (
        medicao_tarde.valores_medicao.filter(
            nome_campo="matriculados", categoria_medicao__nome="ALIMENTAÇÃO"
        ).count()
        == 30
    )

    medicao_noite = solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
        periodo_escolar=periodo_escolar_noite
    )
    assert (
        medicao_noite.valores_medicao.filter(
            nome_campo="matriculados", categoria_medicao__nome="ALIMENTAÇÃO"
        ).count()
        == 30
    )

    medicao_programas_projetos = (
        solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
            grupo__nome="Programas e Projetos"
        )
    )
    assert (
        medicao_programas_projetos.valores_medicao.filter(
            nome_campo="numero_de_alunos", categoria_medicao__nome="ALIMENTAÇÃO"
        ).count()
        == 30
    )

    medicao_etec = solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
        grupo__nome="ETEC"
    )
    assert (
        medicao_etec.valores_medicao.filter(
            nome_campo="numero_de_alunos", categoria_medicao__nome="ALIMENTAÇÃO"
        ).count()
        == 30
    )

    medicao_solicitacoes_alimentacao = (
        solicitacao_medicao_inicial_teste_salvar_logs.medicoes.get(
            grupo__nome="Solicitações de Alimentação"
        )
    )
    assert (
        medicao_solicitacoes_alimentacao.valores_medicao.filter(
            nome_campo="kit_lanche",
            categoria_medicao__nome="SOLICITAÇÕES DE ALIMENTAÇÃO",
        ).count()
        == 1
    )
    assert (
        medicao_solicitacoes_alimentacao.valores_medicao.get(
            nome_campo="kit_lanche",
            categoria_medicao__nome="SOLICITAÇÕES DE ALIMENTAÇÃO",
        ).valor
        == "200"
    )


def test_finaliza_medicao_inicial_salva_logs_cei(
    client_autenticado_da_escola_cei,
    solicitacao_medicao_inicial_teste_salvar_logs_cei,
):
    tipos_contagem = (
        solicitacao_medicao_inicial_teste_salvar_logs_cei.tipos_contagem_alimentacao.all()
    )
    tipos_contagem_uuids = tipos_contagem.values_list("uuid", flat=True)
    tipos_contagem_uuids = [str(uuid) for uuid in tipos_contagem_uuids]
    data_update = {
        "escola": str(solicitacao_medicao_inicial_teste_salvar_logs_cei.escola.uuid),
        "tipo_contagem_alimentacoes[]": tipos_contagem_uuids,
        "com_ocorrencias": False,
        "finaliza_medicao": True,
    }
    response = client_autenticado_da_escola_cei.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_teste_salvar_logs_cei.uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_200_OK

    solicitacao_medicao_inicial_teste_salvar_logs_cei.refresh_from_db()
    assert (
        solicitacao_medicao_inicial_teste_salvar_logs_cei.status
        == "MEDICAO_ENVIADA_PELA_UE"
    )
    assert solicitacao_medicao_inicial_teste_salvar_logs_cei.logs_salvos is True
    assert solicitacao_medicao_inicial_teste_salvar_logs_cei.medicoes.count() == 3

    medicao_integral = solicitacao_medicao_inicial_teste_salvar_logs_cei.medicoes.get(
        periodo_escolar__nome="INTEGRAL"
    )
    assert (
        medicao_integral.valores_medicao.filter(nome_campo="matriculados").count() == 31
    )
    assert (
        medicao_integral.valores_medicao.filter(nome_campo="dietas_autorizadas").count()
        == 62
    )

    medicao_parcial = solicitacao_medicao_inicial_teste_salvar_logs_cei.medicoes.get(
        periodo_escolar__nome="PARCIAL"
    )
    assert medicao_parcial.valores_medicao.count() == 93
    assert (
        medicao_parcial.valores_medicao.filter(nome_campo="dietas_autorizadas").count()
        == 62
    )
    assert (
        medicao_parcial.valores_medicao.filter(nome_campo="dietas_autorizadas")
        .values_list("faixa_etaria", flat=True)
        .distinct()
        .count()
        == 2
    )
    assert (
        medicao_parcial.valores_medicao.filter(nome_campo="matriculados")
        .values_list("faixa_etaria", flat=True)
        .distinct()
        .count()
        == 1
    )


def test_finaliza_medicao_inicial_salva_logs_ceu_gestao(
    client_autenticado_da_escola_ceu_gestao,
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
):
    tipos_contagem = (
        solicitacao_medicao_inicial_varios_valores_ceu_gestao.tipos_contagem_alimentacao.all()
    )
    tipos_contagem_uuids = tipos_contagem.values_list("uuid", flat=True)
    tipos_contagem_uuids = [str(uuid) for uuid in tipos_contagem_uuids]
    data_update = {
        "escola": str(
            solicitacao_medicao_inicial_varios_valores_ceu_gestao.escola.uuid
        ),
        "tipo_contagem_alimentacoes[]": tipos_contagem_uuids,
        "com_ocorrencias": False,
        "finaliza_medicao": True,
    }
    response = client_autenticado_da_escola_ceu_gestao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_varios_valores_ceu_gestao.uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == [
        {
            "erro": "Restam dias a serem lançados nas alimentações.",
            "periodo_escolar": "TARDE",
        }
    ]


def test_finaliza_medicao_inicial_salva_logs_emebs(
    client_autenticado_da_escola_emebs,
    solicitacao_medicao_inicial_varios_valores_emebs,
):
    tipos_contagem = (
        solicitacao_medicao_inicial_varios_valores_emebs.tipos_contagem_alimentacao.all()
    )
    tipos_contagem_uuids = tipos_contagem.values_list("uuid", flat=True)
    tipos_contagem_uuids = [str(uuid) for uuid in tipos_contagem_uuids]
    data_update = {
        "escola": str(solicitacao_medicao_inicial_varios_valores_emebs.escola.uuid),
        "tipo_contagem_alimentacoes[]": tipos_contagem_uuids,
        "com_ocorrencias": False,
        "finaliza_medicao": True,
    }
    response = client_autenticado_da_escola_emebs.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_medicao_inicial_varios_valores_emebs.uuid}/",
        content_type="application/json",
        data=json.dumps(data_update),
    )
    assert response.status_code == status.HTTP_200_OK


def test_salva_valores_medicao_inicial_cemei(
    client_autenticado_da_escola_cemei,
    escola_cemei,
    solicitacao_medicao_inicial_cemei,
    categoria_medicao,
):
    data = {
        "valores_medicao": [
            {
                "dia": "08",
                "valor": "218",
                "nome_campo": "matriculados",
                "categoria_medicao": categoria_medicao.id,
                "faixa_etaria": "0c914b27-c7cd-4682-a439-a4874745b005",
            },
            {
                "dia": "08",
                "valor": "200",
                "nome_campo": "frequencia",
                "categoria_medicao": categoria_medicao.id,
                "faixa_etaria": "0c914b27-c7cd-4682-a439-a4874745b005",
            },
        ]
    }
    medicao_integral = solicitacao_medicao_inicial_cemei.medicoes.get(
        periodo_escolar__nome="INTEGRAL"
    )
    response = client_autenticado_da_escola_cemei.patch(
        f"/medicao-inicial/medicao/{medicao_integral.uuid}/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_200_OK

    medicao_integral.refresh_from_db()
    assert medicao_integral.valores_medicao.count() == 3
    assert (
        medicao_integral.valores_medicao.filter(
            dia="08", nome_campo="matriculados", valor="218"
        ).exists()
        is True
    )
    assert (
        medicao_integral.valores_medicao.filter(
            dia="08", nome_campo="frequencia", valor="200"
        ).exists()
        is True
    )


def test_escolas_permissoes_lancamentos_especiais(
    client_autenticado_coordenador_codae, permissoes_lancamento_especial
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/permissao-lancamentos-especiais/escolas-permissoes-lancamentos-especiais/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


def test_permissoes_lancamentos_especiais_mes_ano_por_periodo(
    client_autenticado_da_escola, escola, permissoes_lancamento_especial
):
    response_manha = client_autenticado_da_escola.get(
        "/medicao-inicial/permissao-lancamentos-especiais/permissoes-lancamentos-especiais-mes-ano-por-periodo/"
        f"?escola_uuid={escola.uuid}&mes=08&ano=2023"
        "&nome_periodo_escolar=MANHA"
    )
    assert response_manha.status_code == status.HTTP_200_OK
    assert len(response_manha.data["results"]["permissoes_por_dia"]) == 3
    assert (
        len(response_manha.data["results"]["alimentacoes_lancamentos_especiais"]) == 4
    )
    assert response_manha.data["results"]["data_inicio_permissoes"] == "13/08/2023"

    response_tarde = client_autenticado_da_escola.get(
        "/medicao-inicial/permissao-lancamentos-especiais/permissoes-lancamentos-especiais-mes-ano-por-periodo/"
        f"?escola_uuid={escola.uuid}&mes=08&ano=2023"
        "&nome_periodo_escolar=TARDE"
    )
    assert response_tarde.status_code == status.HTTP_200_OK
    assert len(response_tarde.data["results"]["permissoes_por_dia"]) == 8
    assert (
        len(response_tarde.data["results"]["alimentacoes_lancamentos_especiais"]) == 3
    )
    assert response_tarde.data["results"]["data_inicio_permissoes"] == "02/08/2023"


def test_periodos_escola_cemei_com_alunos_emei(
    client_autenticado_da_escola_cemei, logs_alunos_matriculados_periodo_escola_cemei
):
    hoje = datetime.date.today()
    response = client_autenticado_da_escola_cemei.get(
        "/medicao-inicial/solicitacao-medicao-inicial/periodos-escola-cemei-com-alunos-emei/"
        f"?mes={hoje.month}&ano={hoje.year}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3
    dados = response.data["results"]
    assert dados[0] == "Infantil MANHA"
    assert dados[1] == "Infantil TARDE"
    assert dados[2] == "Infantil INTEGRAL"


def test_periodos_permissoes_lancamentos_especiais_mes_ano(
    client_autenticado_da_escola, escola, permissoes_lancamento_especial
):
    response = client_autenticado_da_escola.get(
        "/medicao-inicial/permissao-lancamentos-especiais/periodos-permissoes-lancamentos-especiais-mes-ano/"
        f"?escola_uuid={escola.uuid}&mes=08&ano=2023"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert set(
        [
            periodo_permissao
            for periodo_permissao in response.data["results"]
            if periodo_permissao["periodo"] == "TARDE"
        ][0]["alimentacoes"]
    ) == set(["Repetição 2ª Sobremesa", "2º Lanche 5h", "Repetição 2ª Refeição"])
    assert set(
        [
            periodo_permissao
            for periodo_permissao in response.data["results"]
            if periodo_permissao["periodo"] == "MANHA"
        ][0]["alimentacoes"]
    ) == set(
        [
            "2ª Sobremesa 1ª oferta",
            "2º Lanche 5h",
            "Lanche Extra",
            "2ª Refeição 1ª oferta",
        ]
    )


def test_url_endpoint_empenho(client_autenticado_coordenador_codae, edital, contrato):
    data = {
        "numero": "1234599",
        "contrato": contrato.uuid,
        "edital": edital.uuid,
        "tipo_empenho": "PRINCIPAL",
        "status": "ATIVO",
        "valor_total": 1050.99,
        "uuid": "c1203fab-b189-4cac-8930-6e2f315bbe2e",
    }

    response = client_autenticado_coordenador_codae.post(
        "/medicao-inicial/empenhos/",
        content_type="application/json",
        data=data,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Empenho.objects.count() == 1

    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/empenhos/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["contrato"] == "Contrato 78/SME/2024"
    assert response.json()["results"][0]["edital"] == "Edital de Pregão nº 78/SME/2024"
    assert response.json()["results"][0]["numero"] == "1234599"
    assert response.json()["results"][0]["tipo_empenho"] == "PRINCIPAL"
    assert response.json()["results"][0]["status"] == "ATIVO"
    assert response.json()["results"][0]["valor_total"] == "1050.99"


def test_url_endpoint_relatorio_adesao_sem_periodo_lancamento(
    client_autenticado_coordenador_codae,
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_url_endpoint_relatorio_adesao_com_periodo_lancamento(
    client_autenticado_coordenador_codae,
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]
    total_servido = sum(valores[:3])
    total_frequencia = sum(valores[:3])
    total_adesao = round(total_servido / total_frequencia, 4)

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_url_endpoint_relatorio_adesao_sem_mes_ano(
    client_autenticado_coordenador_codae,
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/relatorios/relatorio-adesao/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_relatorio_adesao_sem_periodo_lancamento_ate(
    client_autenticado_coordenador_codae,
):
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos"
    }


def test_url_endpoint_relatorio_adesao_com_periodo_lancamento_no_formato_incorreto(
    client_autenticado_coordenador_codae,
):
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01-{mes}-{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"
    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": f"Formato de data inválido para 'periodo_lancamento_de'. Use o formato dd/mm/yyyy"
    }


def test_url_endpoint_relatorio_adesao_com_periodo_lancamento_data_invertida(
    client_autenticado_coordenador_codae,
):
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"
    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_ate}&periodo_lancamento_ate={periodo_lancamento_de}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "'periodo_lancamento_de' deve ser anterior a 'periodo_lancamento_ate'"
    }


def test_url_endpoint_relatorio_adesao_com_periodo_lancamento_com_mes_diferente_do_parametro_ano_mes(
    client_autenticado_coordenador_codae,
):
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/03/{ano}"
    periodo_lancamento_ate = f"03/05/{ano}"
    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "O mês/ano de 'periodo_lancamento_ate' (05/2024) não coincide com 'mes_ano' (03_2024)."
    }


def test_url_endpoint_relatorio_adesao_exportar_xlsx(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-xlsx/?mes_ano={mes}_{ano}"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_relatorio_adesao_exportar_xlsx_com_periodo_lancamento(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-xlsx/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_relatorio_adesao_exportar_xlsx_sem_mes_ano(
    client_autenticado_coordenador_codae,
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/relatorios/relatorio-adesao/exportar-xlsx/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_relatorio_adesao_exportar_xlsx_sem_periodo_lancamento_ate(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-xlsx/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos"
    }


def test_url_endpoint_relatorio_adesao_exportar_pdf(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-pdf/?mes_ano={mes}_{ano}"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_relatorio_adesao_exportar_pdf_com_periodo_lancamento(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-pdf/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_relatorio_adesao_exportar_pdf_sem_mes_ano(
    client_autenticado_coordenador_codae,
):
    response = client_autenticado_coordenador_codae.get(
        "/medicao-inicial/relatorios/relatorio-adesao/exportar-pdf/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_relatorio_adesao_exportar_pdf_sem_periodo_lancamento_ate(
    client_autenticado_coordenador_codae,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"

    response = client_autenticado_coordenador_codae.get(
        f"/medicao-inicial/relatorios/relatorio-adesao/exportar-pdf/?mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos"
    }


def test_url_endpoint_parametrizacao_financeira(
    client_autenticado_codae_medicao,
    edital,
    escola_ceu_gestao,
    tipo_unidade_escolar,
    tipo_unidade_escolar_ceu_emef,
    tipo_unidade_escolar_emefm,
    tipo_unidade_escolar_cieja,
    tipo_unidade_escolar_ceu_gestao,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_sobremesa,
    tipo_alimentacao_almoco,
    tipo_alimentacao_lanche_emergencial,
    parametrizacao_financeira_emef,
):
    response = client_autenticado_codae_medicao.get(
        "/medicao-inicial/parametrizacao-financeira/", content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1

    data_create = {
        "edital": edital.uuid,
        "legenda": "Legenda teste",
        "lote": escola_ceu_gestao.lote.uuid,
        "tipos_unidades": [
            tipo_unidade_escolar.uuid,
            tipo_unidade_escolar_ceu_emef.uuid,
            tipo_unidade_escolar_emefm.uuid,
            tipo_unidade_escolar_cieja.uuid,
            tipo_unidade_escolar_ceu_gestao.uuid,
        ],
        "tabelas": [
            {
                "nome": "Preço das Alimentações",
                "valores": [
                    {
                        "grupo": "EMEF / CEUEMEF / EMEFM",
                        "tipo_alimentacao": tipo_alimentacao_refeicao.uuid,
                        "valor_colunas": {
                            "valor_unitario": 10,
                            "valor_unitario_reajuste": 2,
                        },
                    },
                    {
                        "grupo": "CIEJA / EJA",
                        "tipo_alimentacao": tipo_alimentacao_refeicao.uuid,
                        "valor_colunas": {
                            "valor_unitario": 8,
                            "valor_unitario_reajuste": 3,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche.uuid,
                        "valor_colunas": {
                            "valor_unitario": 5,
                            "valor_unitario_reajuste": 3,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche_4h.uuid,
                        "valor_colunas": {
                            "valor_unitario": 4,
                            "valor_unitario_reajuste": 2,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_sobremesa.uuid,
                        "valor_colunas": {
                            "valor_unitario": 6,
                            "valor_unitario_reajuste": 4,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_almoco.uuid,
                        "valor_colunas": {
                            "valor_unitario": 8,
                            "valor_unitario_reajuste": 5,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche_emergencial.uuid,
                        "valor_colunas": {
                            "valor_unitario": 10,
                            "valor_unitario_reajuste": 8,
                        },
                    },
                ],
            },
            {
                "nome": "Dietas Tipo A e Tipo A Enteral",
                "valores": [
                    {
                        "grupo": "Dieta Enteral",
                        "tipo_alimentacao": tipo_alimentacao_refeicao.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 2,
                            "valor_unitario": 10,
                            "valor_unitario_total": 10.2,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche_4h.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 20,
                            "valor_unitario": 11,
                            "valor_unitario_total": 13.2,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 3,
                            "valor_unitario": 12,
                            "valor_unitario_total": 12.36,
                        },
                    },
                ],
            },
            {
                "nome": "Dietas Tipo B",
                "valores": [
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche_4h.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 2,
                            "valor_unitario": 12,
                            "valor_unitario_total": 12.24,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 10,
                            "valor_unitario": 10,
                            "valor_unitario_total": 11,
                        },
                    },
                ],
            },
        ],
    }
    response = client_autenticado_codae_medicao.post(
        "/medicao-inicial/parametrizacao-financeira/",
        content_type="application/json",
        data=data_create,
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client_autenticado_codae_medicao.get(
        "/medicao-inicial/parametrizacao-financeira/", content_type="application/json"
    )
    assert len(response.data["results"]) == 2

    data_update = {
        "legenda": "Fonte: Relatório de Medição Inicial do Serviço de Alimentação e Nutrição Escolar realizada pela direção das unidades educacionais.",
        "tabelas": [
            {
                "nome": "Dietas Tipo B",
                "valores": [
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche_4h.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 6,
                            "valor_unitario": 8,
                            "valor_unitario_total": 8.48,
                        },
                    },
                    {
                        "grupo": None,
                        "tipo_alimentacao": tipo_alimentacao_lanche.uuid,
                        "valor_colunas": {
                            "percentual_acrescimo": 6,
                            "valor_unitario": 12,
                            "valor_unitario_total": 12.72,
                        },
                    },
                ],
            },
        ],
    }
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/parametrizacao-financeira/{parametrizacao_financeira_emef.uuid}/",
        content_type="application/json",
        data=data_update,
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_relatorio_consolidado_xlsx_sem_mes_refencia(
    client_autenticado_diretoria_regional,
    grupo_escolar,
    escola,
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/relatorio-consolidado/exportar-xlsx/"
        f"?grupo_escolar={grupo_escolar}&status=MEDICAO_APROVADA_PELA_CODAE&dre={escola.diretoria_regional.uuid}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == "É necessário informar o mês/ano de referência"


def test_url_endpoint_relatorio_consolidado_xlsx_com_filtros(
    client_autenticado_diretoria_regional,
    grupo_escolar,
    escola,
):
    response = client_autenticado_diretoria_regional.get(
        "/medicao-inicial/solicitacao-medicao-inicial/relatorio-consolidado/exportar-xlsx/"
        f"?mes=05&ano=2023&grupo_escolar={grupo_escolar}&status=MEDICAO_APROVADA_PELA_CODAE&dre={escola.diretoria_regional.uuid}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "detail": "Solicitação de geração de arquivo recebida com sucesso."
    }


def test_codae_solicita_correcao_sem_lancamento(
    client_autenticado_codae_medicao, solicitacao_sem_lancamento
):
    solicita_correcao = {
        "justificativa": "Houve alimentação ofertadada nesse período",
    }
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_sem_lancamento.uuid}/codae-solicita-correcao-sem-lancamentos/",
        content_type="application/json",
        data=json.dumps(solicita_correcao),
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert (
        resposta["justificativa_codae_correcao_sem_lancamentos"]
        == solicita_correcao["justificativa"]
    )
    assert resposta["status"] == "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"


def test_codae_solicita_correcao_sem_lancamento_usuario_sem_permissao(
    client_autenticado_da_escola, solicitacao_sem_lancamento
):
    solicita_correcao = {
        "justificativa": "Houve alimentação ofertadada nesse período",
    }
    response = client_autenticado_da_escola.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{solicitacao_sem_lancamento.uuid}/codae-solicita-correcao-sem-lancamentos/",
        content_type="application/json",
        data=json.dumps(solicita_correcao),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }


def test_codae_solicita_correcao_sem_lancamento_solicitacao_nao_existe(
    client_autenticado_codae_medicao, escola
):
    solicita_correcao = {
        "justificativa": "Houve alimentação ofertadada nesse período",
    }
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{escola.uuid}/codae-solicita-correcao-sem-lancamentos/",
        content_type="application/json",
        data=json.dumps(solicita_correcao),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "No SolicitacaoMedicaoInicial matches the given query."
    }


def test_codae_solicita_correcao_sem_lancamento_erro_transicao(
    client_autenticado_codae_medicao, medicao_sem_lancamento_com_correcao
):
    solicita_correcao = {
        "justificativa": "Houve alimentação ofertadada nesse período",
    }
    response = client_autenticado_codae_medicao.patch(
        f"/medicao-inicial/solicitacao-medicao-inicial/{medicao_sem_lancamento_com_correcao.uuid}/codae-solicita-correcao-sem-lancamentos/",
        content_type="application/json",
        data=json.dumps(solicita_correcao),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "['Solicitação Medição Inicial não pode voltar para ser preenchida novamente, pois possui lançamentos.']"
    }
