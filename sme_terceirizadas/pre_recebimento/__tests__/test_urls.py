import datetime
import json
import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from sme_terceirizadas.dados_comuns import constants
from sme_terceirizadas.dados_comuns.api.paginations import DefaultPagination
from sme_terceirizadas.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
    DocumentoDeRecebimentoWorkflow,
    FichaTecnicaDoProdutoWorkflow,
    LayoutDeEmbalagemWorkflow,
)
from sme_terceirizadas.pre_recebimento.api.serializers.serializers import (
    CronogramaSimplesSerializer,
    FichaTecnicaComAnaliseDetalharSerializer,
    FichaTecnicaDetalharSerializer,
    NomeEAbreviacaoUnidadeMedidaSerializer,
)
from sme_terceirizadas.pre_recebimento.api.services import (
    ServiceDashboardDocumentosDeRecebimento,
    ServiceDashboardFichaTecnica,
    ServiceDashboardLayoutEmbalagem,
)
from sme_terceirizadas.pre_recebimento.models import (
    AnaliseFichaTecnica,
    Cronograma,
    DocumentoDeRecebimento,
    FichaTecnicaDoProduto,
    Laboratorio,
    LayoutDeEmbalagem,
    SolicitacaoAlteracaoCronograma,
    TipoDeDocumentoDeRecebimento,
    TipoEmbalagemQld,
    UnidadeMedida,
)

fake = Faker("pt_BR")


def test_rascunho_cronograma_create_ok(
    client_autenticado_codae_dilog,
    contrato,
    empresa,
    unidade_medida_logistica,
    armazem,
    ficha_tecnica_perecivel_enviada_para_analise,
):
    qtd_total_empenho = fake.random_number() / 100
    custo_unitario_produto = fake.random_number() / 100

    payload = {
        "contrato": str(contrato.uuid),
        "empresa": str(empresa.uuid),
        "unidade_medida": str(unidade_medida_logistica.uuid),
        "armazem": str(armazem.uuid),
        "cadastro_finalizado": False,
        "etapas": [
            {
                "numero_empenho": "123456789",
                "qtd_total_empenho": qtd_total_empenho,
            },
            {
                "numero_empenho": "1891425",
                "qtd_total_empenho": qtd_total_empenho,
                "etapa": "Etapa 1",
            },
        ],
        "programacoes_de_recebimento": [
            {
                "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
        "ficha_tecnica": str(ficha_tecnica_perecivel_enviada_para_analise.uuid),
        "custo_unitario_produto": custo_unitario_produto,
    }

    response = client_autenticado_codae_dilog.post(
        "/cronogramas/", content_type="application/json", data=json.dumps(payload)
    )

    obj = Cronograma.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    assert obj.contrato == contrato
    assert obj.empresa == empresa
    assert obj.unidade_medida == unidade_medida_logistica
    assert obj.armazem == armazem
    assert obj.ficha_tecnica == ficha_tecnica_perecivel_enviada_para_analise
    assert obj.custo_unitario_produto == custo_unitario_produto
    assert obj.etapas.first().qtd_total_empenho == qtd_total_empenho


def test_url_lista_etapas_authorized_numeros(client_autenticado_codae_dilog):
    response = client_autenticado_codae_dilog.get("/cronogramas/opcoes-etapas/")
    assert response.status_code == status.HTTP_200_OK


def test_url_list_cronogramas(
    client_autenticado_codae_dilog, cronogramas_multiplos_status_com_log
):
    response = client_autenticado_codae_dilog.get("/cronogramas/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_list_cronogramas_fornecedor(client_autenticado_fornecedor):
    response = client_autenticado_fornecedor.get("/cronogramas/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_list_solicitacoes_alteracao_cronograma(
    client_autenticado_dilog_cronograma,
):
    response = client_autenticado_dilog_cronograma.get(
        "/solicitacao-de-alteracao-de-cronograma/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_list_solicitacoes_alteracao_cronograma_fornecedor(
    client_autenticado_fornecedor,
):
    response = client_autenticado_fornecedor.get(
        "/solicitacao-de-alteracao-de-cronograma/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_solicitacao_alteracao_fornecedor(
    client_autenticado_fornecedor, cronograma_assinado_perfil_dilog
):
    data = {
        "cronograma": str(cronograma_assinado_perfil_dilog.uuid),
        "etapas": [
            {
                "numero_empenho": "43532542",
                "etapa": "Etapa 4",
                "parte": "Parte 2",
                "data_programada": "2023-06-03",
                "quantidade": 123,
                "total_embalagens": 333,
            },
            {
                "etapa": "Etapa 1",
                "parte": "Parte 1",
                "data_programada": "2023-09-14",
                "quantidade": "0",
                "total_embalagens": 1,
            },
        ],
        "justificativa": "Teste",
    }
    response = client_autenticado_fornecedor.post(
        "/solicitacao-de-alteracao-de-cronograma/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    obj = SolicitacaoAlteracaoCronograma.objects.last()
    assert obj.status == "EM_ANALISE"


def test_url_solicitacao_alteracao_dilog(
    client_autenticado_dilog_cronograma, cronograma_assinado_perfil_dilog
):
    data = {
        "cronograma": str(cronograma_assinado_perfil_dilog.uuid),
        "qtd_total_programada": 124,
        "etapas": [
            {
                "numero_empenho": "43532542",
                "etapa": "Etapa 4",
                "parte": "Parte 2",
                "data_programada": "2023-06-03",
                "quantidade": 123,
                "total_embalagens": 333,
            },
            {
                "etapa": "Etapa 1",
                "parte": "Parte 1",
                "data_programada": "2023-09-14",
                "quantidade": 1,
                "total_embalagens": 1,
            },
        ],
        "justificativa": "Teste",
        "programacoes_de_recebimento": [
            {
                "data_programada": "14/09/2023 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
    }

    response = client_autenticado_dilog_cronograma.post(
        "/solicitacao-de-alteracao-de-cronograma/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_201_CREATED
    obj = SolicitacaoAlteracaoCronograma.objects.last()
    assert obj.status == "ALTERACAO_ENVIADA_FORNECEDOR"
    assert obj.qtd_total_programada == 124
    assert obj.programacoes_novas.count() > 0


def test_url_perfil_cronograma_ciente_alteracao_cronograma(
    client_autenticado_dilog_cronograma, solicitacao_cronograma_em_analise
):
    data = json.dumps(
        {
            "justificativa_cronograma": "teste justificativa",
            "etapas": [
                {"numero_empenho": "123456789"},
                {"numero_empenho": "1891425", "etapa": "Etapa 1"},
            ],
            "programacoes_de_recebimento": [
                {
                    "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                    "tipo_carga": "PALETIZADA",
                }
            ],
        }
    )
    response = client_autenticado_dilog_cronograma.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_em_analise.uuid}/cronograma-ciente/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_em_analise.uuid
    )
    assert obj.status == "CRONOGRAMA_CIENTE"


def test_url_cronograma_ciente_erro_solicitacao_cronograma_invalida(
    client_autenticado_dilog_cronograma,
):
    response = client_autenticado_dilog_cronograma.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{uuid.uuid4()}/cronograma-ciente/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_cronograma_ciente_erro_transicao_estado(
    client_autenticado_dilog_cronograma, solicitacao_cronograma_ciente
):
    data = json.dumps(
        {
            "justificativa_cronograma": "teste justificativa",
        }
    )
    response = client_autenticado_dilog_cronograma.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/cronograma-ciente/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_perfil_dinutre_aprova_alteracao_cronograma(
    client_autenticado_dinutre_diretoria, solicitacao_cronograma_ciente
):
    data = json.dumps({"aprovado": True})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-dinutre/",
        data,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_ciente.uuid
    )
    assert obj.status == "APROVADO_DINUTRE"


def test_url_perfil_dinutre_reprova_alteracao_cronograma(
    client_autenticado_dinutre_diretoria, solicitacao_cronograma_ciente
):
    data = json.dumps(
        {"justificativa_dinutre": "teste justificativa", "aprovado": False}
    )
    response = client_autenticado_dinutre_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-dinutre/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_ciente.uuid
    )
    assert obj.status == "REPROVADO_DINUTRE"


def test_url_analise_dinutre_erro_parametro_aprovado_invalida(
    client_autenticado_dinutre_diretoria, solicitacao_cronograma_ciente
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": ""})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-dinutre/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_analise_dinutre_erro_solicitacao_cronograma_invalido(
    client_autenticado_dinutre_diretoria,
):
    response = client_autenticado_dinutre_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{uuid.uuid4()}/analise-dinutre/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_analise_dinutre_erro_transicao_estado(
    client_autenticado_dinutre_diretoria, solicitacao_cronograma_aprovado_dinutre
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": True})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dinutre.uuid}/analise-dinutre/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_perfil_dilog_aprova_alteracao_cronograma(
    client_autenticado_dilog_diretoria, solicitacao_cronograma_aprovado_dinutre
):
    data = json.dumps({"aprovado": True})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dinutre.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_aprovado_dinutre.uuid
    )
    assert obj.status == "APROVADO_DILOG"


def test_url_perfil_dilog_reprova_alteracao_cronograma(
    client_autenticado_dilog_diretoria, solicitacao_cronograma_aprovado_dinutre
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": False})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dinutre.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_aprovado_dinutre.uuid
    )
    assert obj.status == "REPROVADO_DILOG"


def test_url_analise_dilog_erro_solicitacao_cronograma_invalido(
    client_autenticado_dilog_diretoria,
):
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{uuid.uuid4()}/analise-dilog/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_analise_dilog_erro_parametro_aprovado_invalida(
    client_autenticado_dilog_diretoria, solicitacao_cronograma_aprovado_dinutre
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": ""})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dinutre.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_analise_dilog_erro_transicao_estado(
    client_autenticado_dilog_diretoria, solicitacao_cronograma_ciente
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": True})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_fornecedor_assina_cronograma_authorized(
    client_autenticado_fornecedor, cronograma_recebido
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_fornecedor.patch(
        f"/cronogramas/{cronograma_recebido.uuid}/fornecedor-assina-cronograma/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = Cronograma.objects.get(uuid=cronograma_recebido.uuid)
    assert obj.status == "ASSINADO_FORNECEDOR"


def test_url_fornecedor_confirma_cronograma_erro_transicao_estado(
    client_autenticado_fornecedor, cronograma
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_fornecedor.patch(
        f"/cronogramas/{cronograma.uuid}/fornecedor-assina-cronograma/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_fornecedor_confirma_not_authorized(
    client_autenticado_fornecedor, cronograma_recebido
):
    data = json.dumps({"password": "senha-errada"})
    response = client_autenticado_fornecedor.patch(
        f"/cronogramas/{cronograma_recebido.uuid}/fornecedor-assina-cronograma/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_fornecedor_assina_cronograma_erro_cronograma_invalido(
    client_autenticado_fornecedor,
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_fornecedor.patch(
        f"/cronogramas/{uuid.uuid4()}/fornecedor-assina-cronograma/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_list_rascunhos_cronogramas(client_autenticado_codae_dilog):
    response = client_autenticado_codae_dilog.get("/cronogramas/rascunhos/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "results" in json


def test_url_endpoint_cronograma_editar(
    client_autenticado_codae_dilog, cronograma_rascunho, contrato, empresa
):
    data = {
        "empresa": str(empresa.uuid),
        "contrato": str(contrato.uuid),
        "password": constants.DJANGO_ADMIN_PASSWORD,
        "cadastro_finalizado": True,
        "etapas": [
            {"numero_empenho": "123456789"},
            {"numero_empenho": "1891425", "etapa": "Etapa 1"},
        ],
        "programacoes_de_recebimento": [
            {
                "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
    }
    response = client_autenticado_codae_dilog.put(
        f"/cronogramas/{cronograma_rascunho.uuid}/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_200_OK
    obj = Cronograma.objects.last()
    assert cronograma_rascunho.status == "RASCUNHO"
    assert obj.status == "ASSINADO_E_ENVIADO_AO_FORNECEDOR"


def test_url_endpoint_laboratorio(client_autenticado_qualidade):
    data = {
        "contatos": [
            {
                "nome": "TEREZA",
                "telefone": "8135431540",
                "email": "maxlab@max.com",
            }
        ],
        "nome": "Laboratorio de testes maiusculo",
        "cnpj": "10359359000154",
        "cep": "53600000",
        "logradouro": "OLIVEIR",
        "numero": "120",
        "complemento": "",
        "bairro": "CENTRO",
        "cidade": "IGARASSU",
        "estado": "PE",
        "credenciado": True,
    }
    response = client_autenticado_qualidade.post(
        "/laboratorios/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    obj = Laboratorio.objects.last()
    assert obj.nome == "LABORATORIO DE TESTES MAIUSCULO"


def test_url_laboratorios_authorized(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get("/laboratorios/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_laboratorio_editar(client_autenticado_qualidade, laboratorio):
    data = {
        "contatos": [
            {
                "nome": "TEREZA",
                "telefone": "8135431540",
                "email": "maxlab@max.com",
            }
        ],
        "nome": "Laboratorio de testes maiusculo",
        "cnpj": "10359359000154",
        "cep": "53600000",
        "logradouro": "OLIVEIR",
        "numero": "120",
        "complemento": "",
        "bairro": "CENTRO",
        "cidade": "IGARASSU",
        "estado": "PE",
        "credenciado": True,
    }
    response = client_autenticado_qualidade.put(
        f"/laboratorios/{laboratorio.uuid}/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_200_OK
    obj = Laboratorio.objects.last()
    assert obj.nome == "LABORATORIO DE TESTES MAIUSCULO"


def test_url_lista_laboratorios_authorized(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get("/laboratorios/lista-laboratorios/")
    assert response.status_code == status.HTTP_200_OK


def test_url_lista_nomes_laboratorios_authorized(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get(
        "/laboratorios/lista-nomes-laboratorios/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_embalagem_create(client_autenticado_qualidade):
    data = {"nome": "fardo", "abreviacao": "FD"}
    response = client_autenticado_qualidade.post(
        "/tipos-embalagens/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    obj = TipoEmbalagemQld.objects.last()
    assert obj.nome == "FARDO"


def test_url_embalagen_authorized(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get("/tipos-embalagens/")
    assert response.status_code == status.HTTP_200_OK


def test_url_lista_nomes_tipos_embalagens_authorized(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get(
        "/tipos-embalagens/lista-nomes-tipos-embalagens/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_lista_abreviacoes_tipos_embalagens_authorized(
    client_autenticado_qualidade,
):
    response = client_autenticado_qualidade.get(
        "/tipos-embalagens/lista-abreviacoes-tipos-embalagens/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_embalagem_update(
    client_autenticado_qualidade, tipo_emabalagem_qld
):
    data = {"nome": "saco", "abreviacao": "SC"}
    response = client_autenticado_qualidade.put(
        f"/tipos-embalagens/{tipo_emabalagem_qld.uuid}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_200_OK
    obj = TipoEmbalagemQld.objects.last()
    assert obj.nome == "SACO"


def test_url_perfil_cronograma_assina_cronograma_authorized(
    client_autenticado_dilog_cronograma, empresa, contrato, armazem
):
    data = {
        "empresa": str(empresa.uuid),
        "password": constants.DJANGO_ADMIN_PASSWORD,
        "contrato": str(contrato.uuid),
        "cadastro_finalizado": True,
        "etapas": [
            {"numero_empenho": "123456789"},
            {"numero_empenho": "1891425", "etapa": "Etapa 1"},
        ],
        "programacoes_de_recebimento": [
            {
                "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
    }
    response = client_autenticado_dilog_cronograma.post(
        "/cronogramas/", content_type="application/json", data=json.dumps(data)
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_url_perfil_cronograma_assina_cronograma_erro_senha(
    client_autenticado_dilog_cronograma, empresa, contrato
):
    data = {
        "empresa": str(empresa.uuid),
        "password": "senha_errada",
        "contrato": str(contrato.uuid),
        "cadastro_finalizado": True,
        "etapas": [
            {"numero_empenho": "123456789"},
            {"numero_empenho": "1891425", "etapa": "Etapa 1"},
        ],
        "programacoes_de_recebimento": [
            {
                "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
    }
    response = client_autenticado_dilog_cronograma.post(
        "/cronogramas/", data, content_type="application/json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_perfil_cronograma_assina_not_authorized(client_autenticado_dilog):
    response = client_autenticado_dilog.post("/cronogramas/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dinutre_assina_cronograma_authorized(
    client_autenticado_dinutre_diretoria, cronograma_assinado_fornecedor
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_fornecedor.uuid}/dinutre-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = Cronograma.objects.get(uuid=cronograma_assinado_fornecedor.uuid)
    assert obj.status == "ASSINADO_DINUTRE"


def test_url_dinutre_assina_cronograma_erro_senha(
    client_autenticado_dinutre_diretoria, cronograma_assinado_fornecedor
):
    data = json.dumps({"password": "senha_errada"})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_fornecedor.uuid}/dinutre-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_dinutre_assina_cronograma_erro_cronograma_invalido(
    client_autenticado_dinutre_diretoria,
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/cronogramas/{uuid.uuid4()}/dinutre-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_dinutre_assina_cronograma_erro_transicao_estado(
    client_autenticado_dinutre_diretoria, cronograma
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dinutre_diretoria.patch(
        f"/cronogramas/{cronograma.uuid}/dinutre-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_dinutre_assina_cronograma_not_authorized(
    client_autenticado_dilog, cronograma_recebido
):
    response = client_autenticado_dilog.patch(
        f"/cronogramas/{cronograma_recebido.uuid}/dinutre-assina/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dilog_assina_cronograma_authorized(
    client_autenticado_dilog_diretoria, cronograma_assinado_perfil_dinutre
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_perfil_dinutre.uuid}/codae-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = Cronograma.objects.get(uuid=cronograma_assinado_perfil_dinutre.uuid)
    assert obj.status == "ASSINADO_CODAE"


def test_url_dilog_assina_cronograma_erro_senha(
    client_autenticado_dilog_diretoria, cronograma_assinado_perfil_dinutre
):
    data = json.dumps({"password": "senha_errada"})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_perfil_dinutre.uuid}/codae-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_dilog_assina_cronograma_erro_cronograma_invalido(
    client_autenticado_dilog_diretoria,
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{uuid.uuid4()}/codae-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_dilog_assina_cronograma_erro_transicao_estado(
    client_autenticado_dilog_diretoria, cronograma
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{cronograma.uuid}/codae-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_dilog_assina_cronograma_not_authorized(
    client_autenticado_dilog, cronograma_recebido
):
    response = client_autenticado_dilog.patch(
        f"/cronogramas/{cronograma_recebido.uuid}/codae-assina/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_conogramas_detalhar_com_log(
    client_autenticado_dinutre_diretoria, cronogramas_multiplos_status_com_log
):
    cronograma_com_log = Cronograma.objects.first()
    response = client_autenticado_dinutre_diretoria.get(
        f"/cronogramas/{cronograma_com_log.uuid}/detalhar-com-log/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_conogramas_detalhar(
    client_autenticado_dilog_cronograma,
    cronograma,
    ficha_tecnica_perecivel_enviada_para_analise,
):
    cronograma.ficha_tecnica = ficha_tecnica_perecivel_enviada_para_analise
    cronograma.save()

    response = client_autenticado_dilog_cronograma.get(
        f"/cronogramas/{cronograma.uuid}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["ficha_tecnica"]["uuid"] == str(
        ficha_tecnica_perecivel_enviada_para_analise.uuid
    )


def test_url_dashboard_painel_usuario_dinutre(
    client_autenticado_dinutre_diretoria, cronogramas_multiplos_status_com_log
):
    response = client_autenticado_dinutre_diretoria.get("/cronogramas/dashboard/")
    assert response.status_code == status.HTTP_200_OK

    status_esperados = ["ASSINADO_FORNECEDOR", "ASSINADO_DINUTRE", "ASSINADO_CODAE"]
    status_recebidos = [result["status"] for result in response.json()["results"]]
    for status_esperado in status_esperados:
        assert status_esperado in status_recebidos

    resultados_recebidos = [result for result in response.json()["results"]]
    for resultado in resultados_recebidos:
        if resultado["status"] == "ASSINADO_FORNECEDOR":
            assert len(resultado["dados"]) == 3
        elif resultado["status"] == "ASSINADO_DINUTRE":
            assert len(resultado["dados"]) == 2
        elif resultado["status"] == "ASSINADO_CODAE":
            assert len(resultado["dados"]) == 1


def test_url_dashboard_painel_usuario_dinutre_com_paginacao(
    client_autenticado_dinutre_diretoria, cronogramas_multiplos_status_com_log
):
    response = client_autenticado_dinutre_diretoria.get(
        "/cronogramas/dashboard/?status=ASSINADO_FORNECEDOR&limit=2&offset=0"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["status"] == ["ASSINADO_FORNECEDOR"]
    assert response.json()["results"][0]["total"] == 3
    assert len(response.json()["results"][0]["dados"]) == 2


@pytest.mark.parametrize(
    "status_card",
    [
        CronogramaWorkflow.ASSINADO_FORNECEDOR,
        CronogramaWorkflow.ASSINADO_DINUTRE,
        CronogramaWorkflow.ASSINADO_CODAE,
    ],
)
def test_url_dashboard_cronograma_com_filtro(
    client_autenticado_dinutre_diretoria, cronograma_factory, status_card
):
    cronogramas = cronograma_factory.create_batch(size=10, status=status_card)

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_cronograma": cronogramas[0].numero,
    }
    response = client_autenticado_dinutre_diretoria.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": cronogramas[0].ficha_tecnica.produto.nome,
    }
    response = client_autenticado_dinutre_diretoria.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_fornecedor": cronogramas[0].empresa.razao_social,
    }
    response = client_autenticado_dinutre_diretoria.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1


def test_url_dashboard_painel_solicitacao_alteracao_dinutre(
    client_autenticado_dinutre_diretoria,
    cronogramas_multiplos_status_com_log_cronograma_ciente,
):
    response = client_autenticado_dinutre_diretoria.get(
        "/solicitacao-de-alteracao-de-cronograma/dashboard/"
    )
    QTD_STATUS_DASHBOARD_DINUTRE = 5
    SOLICITACOES_STATUS_CRONOGRAMA_CIENTE = 2
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == QTD_STATUS_DASHBOARD_DINUTRE
    assert response.json()["results"][0]["status"] == "CRONOGRAMA_CIENTE"
    assert (
        len(response.json()["results"][0]["dados"])
        == SOLICITACOES_STATUS_CRONOGRAMA_CIENTE
    )


def test_url_relatorio_cronograma_authorized(
    client_autenticado_dinutre_diretoria, cronograma
):
    response = client_autenticado_dinutre_diretoria.get(
        f"/cronogramas/{str(cronograma.uuid)}/gerar-pdf-cronograma/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_unidades_medida_listar(
    client_autenticado_dilog_cronograma, unidades_medida_logistica
):
    """Deve obter lista paginada de unidades de medida."""
    client = client_autenticado_dilog_cronograma

    response = client.get("/unidades-medida-logistica/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == len(unidades_medida_logistica)
    assert len(response.data["results"]) == DefaultPagination.page_size
    assert response.data["next"] is not None


def test_url_unidades_medida_listar_com_filtros(
    client_autenticado_dilog_cronograma, unidades_medida_reais_logistica
):
    """Deve obter lista paginada e filtrada de unidades de medida."""
    client = client_autenticado_dilog_cronograma

    url_com_filtro_nome = "/unidades-medida-logistica/?nome=lit"
    response = client.get(url_com_filtro_nome)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["nome"] == "LITRO"

    url_com_filtro_abreviacao = "/unidades-medida-logistica/?abreviacao=kg"
    response = client.get(url_com_filtro_abreviacao)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["nome"] == "KILOGRAMA"

    data_cadastro = (
        unidades_medida_reais_logistica[0].criado_em.date().strftime("%d/%m/%Y")
    )
    url_com_filtro_data_cadastro = (
        f"/unidades-medida-logistica/?data_cadastro={data_cadastro}"
    )
    response = client.get(url_com_filtro_data_cadastro)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 2

    url_com_filtro_sem_resultado = "/unidades-medida-logistica/?nome=lit&abreviacao=kg"
    response = client.get(url_com_filtro_sem_resultado)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0


def test_url_unidades_medida_detalhar(
    client_autenticado_dilog_cronograma, unidade_medida_logistica
):
    """Deve obter detalhes de uma unidade de medida."""
    client = client_autenticado_dilog_cronograma

    response = client.get(
        f"/unidades-medida-logistica/{unidade_medida_logistica.uuid}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["uuid"] == str(unidade_medida_logistica.uuid)
    assert response.data["nome"] == str(unidade_medida_logistica.nome)
    assert response.data["abreviacao"] == str(unidade_medida_logistica.abreviacao)
    assert response.data["criado_em"] == unidade_medida_logistica.criado_em.strftime(
        settings.REST_FRAMEWORK["DATETIME_FORMAT"]
    )


def test_url_unidades_medida_criar(client_autenticado_dilog_cronograma):
    """Deve criar com sucesso uma unidade de medida."""
    client = client_autenticado_dilog_cronograma
    payload = {"nome": "UNIDADE MEDIDA TESTE", "abreviacao": "umt"}

    response = client.post(
        "/unidades-medida-logistica/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["nome"] == payload["nome"]
    assert response.data["abreviacao"] == payload["abreviacao"]
    assert UnidadeMedida.objects.filter(uuid=response.data["uuid"]).exists()


def test_url_unidades_medida_criar_com_nome_invalido(
    client_autenticado_dilog_cronograma,
):
    """Deve falhar ao tentar criar uma unidade de medida com atributo nome inválido (caixa baixa)."""
    client = client_autenticado_dilog_cronograma
    payload = {"nome": "unidade medida teste", "abreviacao": "umt"}

    response = client.post(
        "/unidades-medida-logistica/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        str(response.data["nome"][0]) == "O campo deve conter apenas letras maiúsculas."
    )


def test_url_unidades_medida_criar_com_abreviacao_invalida(
    client_autenticado_dilog_cronograma,
):
    """Deve falhar ao tentar criar uma unidade de medida com atributo abreviacao inválida (caixa alta)."""
    client = client_autenticado_dilog_cronograma
    payload = {"nome": "UNIDADE MEDIDA TESTE", "abreviacao": "UMT"}

    response = client.post(
        "/unidades-medida-logistica/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        str(response.data["abreviacao"][0])
        == "O campo deve conter apenas letras minúsculas."
    )


def test_url_unidades_medida_criar_repetida(
    client_autenticado_dilog_cronograma, unidade_medida_logistica
):
    """Deve falhar ao tentar criar uma unidade de medida que já esteja cadastrada."""
    client = client_autenticado_dilog_cronograma
    payload = {"nome": "UNIDADE TESTE", "abreviacao": "ut"}

    response = client.post(
        "/unidades-medida-logistica/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["non_field_errors"][0].code == "unique"


def test_url_unidades_medida_atualizar(
    client_autenticado_dilog_cronograma, unidade_medida_logistica
):
    """Deve atualizar com sucesso uma unidade de medida."""
    client = client_autenticado_dilog_cronograma
    payload = {"nome": "UNIDADE MEDIDA TESTE ATUALIZADA", "abreviacao": "umta"}

    response = client.patch(
        f"/unidades-medida-logistica/{unidade_medida_logistica.uuid}/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    unidade_medida_logistica.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.data["nome"] == unidade_medida_logistica.nome == payload["nome"]
    assert (
        response.data["abreviacao"]
        == unidade_medida_logistica.abreviacao
        == payload["abreviacao"]
    )


def test_url_unidades_medida_action_listar_nomes_abreviacoes(
    client_autenticado_dilog_cronograma, unidades_medida_logistica
):
    """Deve obter lista com nomes e abreviações de todas as unidades de medida cadastradas."""
    client = client_autenticado_dilog_cronograma
    response = client.get("/unidades-medida-logistica/lista-nomes-abreviacoes/")

    unidades_medida = UnidadeMedida.objects.all().order_by("-criado_em")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == len(unidades_medida_logistica)
    assert (
        response.data["results"]
        == NomeEAbreviacaoUnidadeMedidaSerializer(unidades_medida, many=True).data
    )


def test_url_cronograma_action_listar_para_cadastro(
    client_autenticado_fornecedor, django_user_model, cronograma_factory
):
    """Deve obter lista com numeros, pregao e nome do produto dos cronogramas cadastrados do fornecedor."""
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    cronogramas_do_fornecedor = [
        cronograma_factory.create(empresa=empresa) for _ in range(10)
    ]
    outros_cronogramas = [cronograma_factory.create() for _ in range(5)]
    todos_cronogramas = cronogramas_do_fornecedor + outros_cronogramas
    response = client_autenticado_fornecedor.get(
        "/cronogramas/lista-cronogramas-cadastro/"
    )

    cronogramas = Cronograma.objects.filter(empresa=empresa).order_by("-criado_em")

    # Testa se o usuário fornecedor acessa apenas os seus cronogramas
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.data["results"]
        == CronogramaSimplesSerializer(cronogramas, many=True).data
    )
    assert len(response.data["results"]) == len(cronogramas_do_fornecedor)

    # Testa se a quantidade de cronogramas do response é diferente da quantidade total de cronogramas
    assert len(response.data["results"]) != len(todos_cronogramas)


def test_url_endpoint_layout_de_embalagem_create(
    client_autenticado_fornecedor, cronograma_assinado_perfil_dilog, arquivo_base64
):
    data = {
        "cronograma": str(cronograma_assinado_perfil_dilog.uuid),
        "observacoes": "Imagine uma observação aqui.",
        "tipos_de_embalagens": [
            {
                "tipo_embalagem": "PRIMARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Anexo2.jpg"},
                ],
            },
            {
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"}
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.post(
        "/layouts-de-embalagem/", content_type="application/json", data=json.dumps(data)
    )

    assert response.status_code == status.HTTP_201_CREATED
    obj = LayoutDeEmbalagem.objects.last()
    assert obj.status == LayoutDeEmbalagem.workflow_class.ENVIADO_PARA_ANALISE
    assert obj.tipos_de_embalagens.count() == 2


def test_url_endpoint_layout_de_embalagem_create_cronograma_nao_existe(
    client_autenticado_fornecedor,
):
    """Uuid do cronograma precisa existir na base, imagens_do_tipo_de_embalagem e arquivo são obrigatórios."""
    data = {
        "cronograma": str(uuid.uuid4()),
        "observacoes": "Imagine uma observação aqui.",
        "tipos_de_embalagens": [
            {
                "tipo_embalagem": "PRIMARIA",
            },
            {
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [{"arquivo": "", "nome": "Anexo1.jpg"}],
            },
        ],
    }

    response = client_autenticado_fornecedor.post(
        "/layouts-de-embalagem/", content_type="application/json", data=json.dumps(data)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cronograma não existe" in response.data["cronograma"]
    assert (
        "Este campo é obrigatório."
        in response.data["tipos_de_embalagens"][0]["imagens_do_tipo_de_embalagem"]
    )


def test_url_layout_de_embalagem_listagem(
    client_autenticado_qualidade, lista_layouts_de_embalagem
):
    """Deve obter lista paginada de layouts de embalagens."""
    client = client_autenticado_qualidade
    response = client.get("/layouts-de-embalagem/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == len(lista_layouts_de_embalagem)
    assert len(response.data["results"]) == DefaultPagination.page_size
    assert response.data["next"] is not None


def test_url_layout_de_embalagem_detalhar(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem
):
    layout_esperado = LayoutDeEmbalagem.objects.first()
    cronograma_esperado = layout_esperado.cronograma

    response = client_autenticado_codae_dilog.get(
        f"/layouts-de-embalagem/{layout_esperado.uuid}/"
    )
    dados_recebidos = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert dados_recebidos["uuid"] == str(layout_esperado.uuid)
    assert dados_recebidos["observacoes"] == str(layout_esperado.observacoes)
    assert dados_recebidos["criado_em"] == layout_esperado.criado_em.strftime(
        settings.REST_FRAMEWORK["DATETIME_FORMAT"]
    )
    assert dados_recebidos["status"] == layout_esperado.get_status_display()
    assert dados_recebidos["numero_cronograma"] == str(cronograma_esperado.numero)
    assert dados_recebidos["nome_produto"] == str(
        cronograma_esperado.ficha_tecnica.produto.nome
    )
    assert dados_recebidos["nome_empresa"] == str(
        cronograma_esperado.empresa.razao_social
    )


def test_url_dashboard_layout_embalagens_status_retornados(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem
):
    response = client_autenticado_codae_dilog.get("/layouts-de-embalagem/dashboard/")

    assert response.status_code == status.HTTP_200_OK

    user_id = client_autenticado_codae_dilog.session["_auth_user_id"]
    user = get_user_model().objects.get(id=user_id)
    status_esperados = ServiceDashboardLayoutEmbalagem.get_dashboard_status(user)
    status_recebidos = [result["status"] for result in response.json()["results"]]

    for status_recebido in status_recebidos:
        assert status_recebido in status_esperados


@pytest.mark.parametrize(
    "status_card",
    [
        LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        LayoutDeEmbalagemWorkflow.APROVADO,
        LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
    ],
)
def test_url_dashboard_layout_embalagens_quantidade_itens_por_card(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem, status_card
):
    response = client_autenticado_codae_dilog.get("/layouts-de-embalagem/dashboard/")

    assert response.status_code == status.HTTP_200_OK

    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 6


@pytest.mark.parametrize(
    "status_card",
    [
        LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        LayoutDeEmbalagemWorkflow.APROVADO,
        LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
    ],
)
def test_url_dashboard_layout_embalagens_com_filtro(
    client_autenticado_codae_dilog, layout_de_embalagem_factory, status_card
):
    layouts = layout_de_embalagem_factory.create_batch(size=10, status=status_card)

    filtros = {"numero_cronograma": layouts[0].cronograma.numero}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_produto": layouts[0].cronograma.ficha_tecnica.produto.nome}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_fornecedor": layouts[0].cronograma.empresa.razao_social}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1


@pytest.mark.parametrize(
    "status_card",
    [
        LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        LayoutDeEmbalagemWorkflow.APROVADO,
        LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
    ],
)
def test_url_dashboard_layout_embalagens_ver_mais(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem, status_card
):
    filtros = {"status": status_card, "offset": 0, "limit": 10}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]["dados"]) == 10

    total_cards_esperado = LayoutDeEmbalagem.objects.filter(status=status_card).count()
    assert response.json()["results"]["total"] == total_cards_esperado


@pytest.mark.parametrize(
    "status_card",
    [
        LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
        LayoutDeEmbalagemWorkflow.APROVADO,
        LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
    ],
)
def test_url_dashboard_layout_embalagens_ver_mais_com_filtros(
    client_autenticado_codae_dilog, layout_de_embalagem_factory, status_card
):
    layouts = layout_de_embalagem_factory.create_batch(size=10, status=status_card)

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_cronograma": layouts[0].cronograma.numero,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": layouts[0].cronograma.ficha_tecnica.produto.nome,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_fornecedor": layouts[0].cronograma.empresa.razao_social,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1


def test_url_layout_embalagens_analise_aprovando(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem_com_tipo_embalagem
):
    layout_analisado = lista_layouts_de_embalagem_com_tipo_embalagem[0]
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="TERCIARIA").uuid
                ),
                "tipo_embalagem": "TERCIARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )
    layout_analisado.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert layout_analisado.aprovado

    layout_analisado = lista_layouts_de_embalagem_com_tipo_embalagem[1]
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )
    layout_analisado.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert layout_analisado.aprovado


def test_url_layout_embalagens_analise_solicitando_correcao(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem_com_tipo_embalagem
):
    layout_analisado = lista_layouts_de_embalagem_com_tipo_embalagem[0]
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="TERCIARIA").uuid
                ),
                "tipo_embalagem": "TERCIARIA",
                "status": "REPROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )
    layout_analisado.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert not layout_analisado.aprovado

    layout_analisado = lista_layouts_de_embalagem_com_tipo_embalagem[1]
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "REPROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )
    layout_analisado.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert not layout_analisado.aprovado


def test_url_layout_embalagens_validacao_primeira_analise(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem_com_tipo_embalagem
):
    layout_analisado = lista_layouts_de_embalagem_com_tipo_embalagem[0]
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )

    msg_erro = (
        "Quantidade de Tipos de Embalagem recebida para primeira análise "
        + "é diferente da quantidade presente no Layout de Embalagem."
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert msg_erro in response.json()["tipos_de_embalagens"]


def test_url_layout_embalagens_analise_correcao(
    client_autenticado_codae_dilog, layout_de_embalagem_em_analise_com_correcao
):
    layout_analisado = layout_de_embalagem_em_analise_com_correcao
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="TERCIARIA").uuid
                ),
                "tipo_embalagem": "TERCIARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    assert not layout_analisado.eh_primeira_analise

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )
    layout_analisado.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert layout_analisado.aprovado


def test_url_layout_embalagens_validacao_analise_correcao(
    client_autenticado_codae_dilog, layout_de_embalagem_em_analise_com_correcao
):
    layout_analisado = layout_de_embalagem_em_analise_com_correcao
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="SECUNDARIA").uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "status": "REPROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    assert not layout_analisado.eh_primeira_analise

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )

    msg_erro = "O Tipo/UUID informado não pode ser analisado pois não está em análise."
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        msg_erro
        in response.json()["tipos_de_embalagens"][1]["Layout Embalagem SECUNDARIA"]
    )

    dados_analise = {
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    tipos_embalagem_analisados.get(tipo_embalagem="PRIMARIA").uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
        ],
    }

    response = client_autenticado_codae_dilog.patch(
        f"/layouts-de-embalagem/{layout_analisado.uuid}/codae-aprova-ou-solicita-correcao/",
        content_type="application/json",
        data=json.dumps(dados_analise),
    )

    msg_erro = (
        "Quantidade de Tipos de Embalagem recebida para análise da correção "
        + "é diferente da quantidade em análise."
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert msg_erro in response.json()["tipos_de_embalagens"]


def test_url_endpoint_layout_de_embalagem_fornecedor_corrige(
    client_autenticado_fornecedor, arquivo_base64, layout_de_embalagem_para_correcao
):
    layout_para_corrigir = layout_de_embalagem_para_correcao
    dados_correcao = {
        "observacoes": "Imagine uma nova observação aqui.",
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    layout_para_corrigir.tipos_de_embalagens.get(
                        status="REPROVADO"
                    ).uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Anexo2.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/layouts-de-embalagem/{layout_para_corrigir.uuid}/fornecedor-realiza-correcao/",
        content_type="application/json",
        data=json.dumps(dados_correcao),
    )

    layout_para_corrigir.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert layout_para_corrigir.status == LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE
    assert layout_para_corrigir.observacoes == "Imagine uma nova observação aqui."


def test_url_endpoint_layout_de_embalagem_fornecedor_corrige_not_ok(
    client_autenticado_fornecedor, arquivo_base64, layout_de_embalagem_para_correcao
):
    """Checa transição de estado, UUID valido de tipo de embalagem e se pode ser de fato corrigido."""
    layout_para_corrigir = layout_de_embalagem_para_correcao
    dados = {
        "observacoes": "Imagine uma nova observação aqui.",
        "tipos_de_embalagens": [
            {
                "uuid": str(uuid.uuid4()),
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                ],
            },
            {
                "uuid": str(
                    layout_para_corrigir.tipos_de_embalagens.get(status="APROVADO").uuid
                ),
                "tipo_embalagem": "TERCIARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/layouts-de-embalagem/{layout_para_corrigir.uuid}/fornecedor-realiza-correcao/",
        content_type="application/json",
        data=json.dumps(dados),
    )

    msg_erro1 = "UUID do tipo informado não existe."
    msg_erro2 = "O Tipo/UUID informado não pode ser corrigido pois não está reprovado."
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        msg_erro1
        in response.json()["tipos_de_embalagens"][0]["Layout Embalagem SECUNDARIA"][0]
    )
    assert (
        msg_erro2
        in response.json()["tipos_de_embalagens"][1]["Layout Embalagem TERCIARIA"][0]
    )

    dados = {
        "observacoes": "Imagine uma nova observação aqui.",
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    layout_para_corrigir.tipos_de_embalagens.get(
                        status="REPROVADO"
                    ).uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                ],
            },
        ],
    }

    layout_para_corrigir.status = LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE
    layout_para_corrigir.save()

    response = client_autenticado_fornecedor.patch(
        f"/layouts-de-embalagem/{layout_para_corrigir.uuid}/fornecedor-realiza-correcao/",
        content_type="application/json",
        data=json.dumps(dados),
    )

    msg_erro3 = (
        "Erro de transição de estado. O status deste layout não permite correção"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert msg_erro3 in response.json()[0]


def test_url_endpoint_layout_de_embalagem_fornecedor_atualiza(
    client_autenticado_fornecedor, arquivo_base64, layout_de_embalagem_aprovado
):
    layout_para_atualizar = layout_de_embalagem_aprovado
    dados_correcao = {
        "observacoes": "Imagine uma nova observação aqui.",
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    layout_para_atualizar.tipos_de_embalagens.get(
                        tipo_embalagem="PRIMARIA"
                    ).uuid
                ),
                "tipo_embalagem": "PRIMARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Anexo2.jpg"},
                ],
            },
            {
                "uuid": str(
                    layout_para_atualizar.tipos_de_embalagens.get(
                        tipo_embalagem="SECUNDARIA"
                    ).uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo3.jpg"},
                ],
            },
            {
                "tipo_embalagem": "TERCIARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo4.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/layouts-de-embalagem/{layout_para_atualizar.uuid}/",
        content_type="application/json",
        data=json.dumps(dados_correcao),
    )

    layout_para_atualizar.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert (
        layout_para_atualizar.status == LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE
    )
    assert layout_para_atualizar.observacoes == "Imagine uma nova observação aqui."


def test_url_endpoint_layout_de_embalagem_fornecedor_atualiza_not_ok(
    client_autenticado_fornecedor, arquivo_base64, layout_de_embalagem_para_correcao
):
    """Checa transição de estado."""
    layout_para_atualizar = layout_de_embalagem_para_correcao

    dados = {
        "observacoes": "Imagine uma nova observação aqui.",
        "tipos_de_embalagens": [
            {
                "uuid": str(
                    layout_para_atualizar.tipos_de_embalagens.get(
                        tipo_embalagem="SECUNDARIA"
                    ).uuid
                ),
                "tipo_embalagem": "SECUNDARIA",
                "imagens_do_tipo_de_embalagem": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/layouts-de-embalagem/{layout_para_atualizar.uuid}/",
        content_type="application/json",
        data=json.dumps(dados),
    )

    msg_erro3 = (
        "Erro de transição de estado. O status deste layout não permite correção"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert msg_erro3 in response.json()[0]


def test_url_endpoint_documentos_recebimento_create(
    client_autenticado_fornecedor, cronograma_factory, arquivo_base64
):
    cronograma_obj = cronograma_factory.create()
    data = {
        "cronograma": str(cronograma_obj.uuid),
        "numero_laudo": "123456789",
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Anexo2.jpg"},
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_RASTREABILIDADE,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Anexo1.jpg"}
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.post(
        "/documentos-de-recebimento/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_201_CREATED
    obj = DocumentoDeRecebimento.objects.last()
    assert obj.status == DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    assert obj.tipos_de_documentos.count() == 2

    # Teste de cadastro quando o cronograma informado não existe ou quando o arquivo não é enviado
    data["cronograma"] = fake.uuid4()
    data["tipos_de_documentos"][1].pop("arquivos_do_tipo_de_documento")

    response = client_autenticado_fornecedor.post(
        "/documentos-de-recebimento/",
        content_type="application/json",
        data=json.dumps(data),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cronograma não existe" in response.data["cronograma"]
    assert (
        "Este campo é obrigatório."
        in response.data["tipos_de_documentos"][1]["arquivos_do_tipo_de_documento"]
    )


def test_url_documentos_de_recebimento_listagem(
    client_autenticado_fornecedor, django_user_model, documento_de_recebimento_factory
):
    """Deve obter lista paginada e filtrada de documentos de recebimento."""
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    documentos = [
        documento_de_recebimento_factory.create(cronograma__empresa=empresa)
        for _ in range(11)
    ]
    response = client_autenticado_fornecedor.get("/documentos-de-recebimento/")

    assert response.status_code == status.HTTP_200_OK

    # Teste de paginação
    assert response.data["count"] == len(documentos)
    assert len(response.data["results"]) == DefaultPagination.page_size
    assert response.data["next"] is not None

    # Acessa a próxima página
    next_page = response.data["next"]
    next_response = client_autenticado_fornecedor.get(next_page)
    assert next_response.status_code == status.HTTP_200_OK

    # Tenta acessar uma página que não existe
    response_not_found = client_autenticado_fornecedor.get(
        "/documentos-de-recebimento/?page=1000"
    )
    assert response_not_found.status_code == status.HTTP_404_NOT_FOUND

    # Testa a resposta em caso de erro (por exemplo, sem autenticação)
    client_nao_autenticado = APIClient()
    response_error = client_nao_autenticado.get("/documentos-de-recebimento/")
    assert response_error.status_code == status.HTTP_401_UNAUTHORIZED

    # Teste de consulta com parâmetros
    data = datetime.date.today() - datetime.timedelta(days=1)
    response_filtro = client_autenticado_fornecedor.get(
        f"/documentos-de-recebimento/?data_cadastro={data}"
    )
    assert response_filtro.status_code == status.HTTP_200_OK
    assert response_filtro.data["count"] == 0


def test_url_documentos_de_recebimento_listagem_not_authorized(client_autenticado):
    """Teste de requisição quando usuário não tem permissão."""
    response = client_autenticado.get("/documentos-de-recebimento/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dashboard_documentos_de_recebimento_status_retornados(
    client_autenticado_codae_dilog, documento_de_recebimento_factory
):
    user_id = client_autenticado_codae_dilog.session["_auth_user_id"]
    user = get_user_model().objects.get(id=user_id)
    status_esperados = ServiceDashboardDocumentosDeRecebimento.get_dashboard_status(
        user
    )
    for status_esperado in status_esperados:
        documento_de_recebimento_factory(status=status_esperado)

    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/"
    )

    assert response.status_code == status.HTTP_200_OK

    status_recebidos = [result["status"] for result in response.json()["results"]]

    for status_recebido in status_recebidos:
        assert status_recebido in status_esperados


@pytest.mark.parametrize(
    "status_card",
    [
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
        DocumentoDeRecebimentoWorkflow.APROVADO,
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
    ],
)
def test_url_dashboard_documentos_de_recebimento_quantidade_itens_por_card(
    client_autenticado_codae_dilog, documento_de_recebimento_factory, status_card
):
    documento_de_recebimento_factory.create_batch(size=10, status=status_card)

    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/"
    )

    assert response.status_code == status.HTTP_200_OK

    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 6


@pytest.mark.parametrize(
    "status_card",
    [
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
        DocumentoDeRecebimentoWorkflow.APROVADO,
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
    ],
)
def test_url_dashboard_documentos_de_recebimento_com_filtro(
    client_autenticado_codae_dilog, documento_de_recebimento_factory, status_card
):
    documentos_de_recebimento = documento_de_recebimento_factory.create_batch(
        size=10, status=status_card
    )

    filtros = {"numero_cronograma": documentos_de_recebimento[0].cronograma.numero}
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {
        "nome_produto": documentos_de_recebimento[
            0
        ].cronograma.ficha_tecnica.produto.nome
    }
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {
        "nome_fornecedor": documentos_de_recebimento[0].cronograma.empresa.razao_social
    }
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1


@pytest.mark.parametrize(
    "status_card",
    [
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
        DocumentoDeRecebimentoWorkflow.APROVADO,
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
    ],
)
def test_url_dashboard_documentos_de_recebimento_ver_mais(
    client_autenticado_codae_dilog, documento_de_recebimento_factory, status_card
):
    documentos_de_recebimento = documento_de_recebimento_factory.create_batch(
        size=10, status=status_card
    )

    filtros = {"status": status_card, "offset": 0, "limit": 10}
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]["dados"]) == 10

    assert response.json()["results"]["total"] == len(documentos_de_recebimento)


@pytest.mark.parametrize(
    "status_card",
    [
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
        DocumentoDeRecebimentoWorkflow.APROVADO,
        DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
    ],
)
def test_url_dashboard_documentos_de_recebimento_ver_mais_com_filtros(
    client_autenticado_codae_dilog, documento_de_recebimento_factory, status_card
):
    documentos_de_recebimento = documento_de_recebimento_factory.create_batch(
        size=10, status=status_card
    )

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_cronograma": documentos_de_recebimento[0].cronograma.numero,
    }
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": documentos_de_recebimento[
            0
        ].cronograma.ficha_tecnica.produto.nome,
    }
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_fornecedor": documentos_de_recebimento[0].cronograma.empresa.razao_social,
    }
    response = client_autenticado_codae_dilog.get(
        "/documentos-de-recebimento/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1


def test_url_documentos_de_recebimento_detalhar(
    client_autenticado_fornecedor,
    documento_de_recebimento_factory,
    cronograma_factory,
    django_user_model,
    tipo_de_documento_de_recebimento_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    contrato = empresa.contratos.first()
    cronograma = cronograma_factory.create(empresa=empresa, contrato=contrato)
    documento_de_recebimento = documento_de_recebimento_factory.create(
        cronograma=cronograma
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento
    )

    response = client_autenticado_fornecedor.get(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/"
    )
    dados_documento_de_recebimento = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert dados_documento_de_recebimento["uuid"] == str(documento_de_recebimento.uuid)
    assert dados_documento_de_recebimento["numero_laudo"] == str(
        documento_de_recebimento.numero_laudo
    )
    assert dados_documento_de_recebimento[
        "criado_em"
    ] == documento_de_recebimento.criado_em.strftime("%d/%m/%Y")
    assert (
        dados_documento_de_recebimento["status"]
        == documento_de_recebimento.get_status_display()
    )
    assert dados_documento_de_recebimento["numero_cronograma"] == str(cronograma.numero)
    assert dados_documento_de_recebimento["nome_produto"] == str(
        cronograma.ficha_tecnica.produto.nome
    )
    assert dados_documento_de_recebimento["pregao_chamada_publica"] == str(
        cronograma.contrato.numero_pregao
    )
    assert dados_documento_de_recebimento["tipos_de_documentos"] is not None
    assert (
        dados_documento_de_recebimento["tipos_de_documentos"][0]["tipo_documento"]
        == "LAUDO"
    )


def test_url_documentos_de_recebimento_analisar_documento(
    documento_de_recebimento_factory,
    laboratorio_factory,
    unidade_medida_factory,
    client_autenticado_qualidade,
):
    """Testa o cenário de rascunho, aprovação e sol. de correção."""
    documento = documento_de_recebimento_factory.create(
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )
    laboratorio = laboratorio_factory.create(credenciado=True)
    unidade_medida = unidade_medida_factory()

    # Teste salvar rascunho (todos os campos não são obrigatórios)
    dados_atualizados = {
        "laboratorio": str(laboratorio.uuid),
        "quantidade_laudo": 10.5,
        "unidade_medida": str(unidade_medida.uuid),
        "data_fabricacao_lote": str(datetime.date.today()),
        "validade_produto": str(datetime.date.today()),
        "data_final_lote": str(datetime.date.today()),
        "saldo_laudo": 5.5,
    }

    response_rascunho = client_autenticado_qualidade.patch(
        f"/documentos-de-recebimento/{documento.uuid}/analise-documentos-rascunho/",
        content_type="application/json",
        data=json.dumps(dados_atualizados),
    )

    documento.refresh_from_db()
    assert response_rascunho.status_code == status.HTTP_200_OK
    assert (
        documento.status == DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )
    assert documento.laboratorio == laboratorio
    assert documento.quantidade_laudo == 10.5
    assert documento.unidade_medida == unidade_medida
    assert documento.data_fabricacao_lote == datetime.date.today()
    assert documento.validade_produto == datetime.date.today()
    assert documento.data_final_lote == datetime.date.today()
    assert documento.saldo_laudo == 5.5

    # Teste analise ação aprovar (Todos os campos são obrigatórios)
    dados_atualizados["quantidade_laudo"] = 20
    dados_atualizados["datas_fabricacao_e_prazos"] = [
        {
            "data_fabricacao": str(datetime.date.today()),
            "prazo_maximo_recebimento": "30",
        },
        {
            "data_fabricacao": str(datetime.date.today()),
            "prazo_maximo_recebimento": "60",
        },
        {
            "data_fabricacao": str(datetime.date.today()),
            "prazo_maximo_recebimento": "30",
        },
    ]

    response_aprovado = client_autenticado_qualidade.patch(
        f"/documentos-de-recebimento/{documento.uuid}/analise-documentos/",
        content_type="application/json",
        data=json.dumps(dados_atualizados),
    )

    documento.refresh_from_db()
    assert response_aprovado.status_code == status.HTTP_200_OK
    assert documento.status == DocumentoDeRecebimento.workflow_class.APROVADO
    assert documento.quantidade_laudo == 20
    assert documento.datas_fabricacao_e_prazos.count() == 3

    # Teste analise ação solicitar correção (Todos os campos são obrigatórios + correcao_solicitada)
    dados_atualizados[
        "correcao_solicitada"
    ] = "Documentos corrompidos, sem possibilidade de análise."
    documento.status = DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    documento.save()

    response_correcao = client_autenticado_qualidade.patch(
        f"/documentos-de-recebimento/{documento.uuid}/analise-documentos/",
        content_type="application/json",
        data=json.dumps(dados_atualizados),
    )

    documento.refresh_from_db()
    assert response_correcao.status_code == status.HTTP_200_OK
    assert (
        documento.status == DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_CORRECAO
    )
    assert (
        documento.correcao_solicitada
        == "Documentos corrompidos, sem possibilidade de análise."
    )


def test_url_documentos_de_recebimento_fornecedor_corrige(
    documento_de_recebimento_factory,
    client_autenticado_fornecedor,
    arquivo_base64,
    django_user_model,
    cronograma_factory,
    tipo_de_documento_de_recebimento_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    cronograma = cronograma_factory.create(
        empresa=empresa,
    )
    documento_de_recebimento = documento_de_recebimento_factory.create(
        cronograma=cronograma,
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_CORRECAO,
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento,
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS,
        descricao_documento="Outro que precisa ser corrigido.",
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento,
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_RASTREABILIDADE,
    )

    dados_correcao = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Laudo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Laudo2.jpg"},
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_DECLARACAO_LEI_1512010,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Declaracao1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Declaracao2.jpg"},
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS,
                "descricao_documento": "Outro após a correção.",
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Outros1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Outros2.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao),
    )

    documento_de_recebimento.refresh_from_db()
    tipos_de_documentos = documento_de_recebimento.tipos_de_documentos.all()
    laudo_atualizado = tipos_de_documentos.filter(
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
    ).first()
    outros_atualizado = tipos_de_documentos.filter(
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS
    ).first()
    declaracao_criado = tipos_de_documentos.filter(
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_DECLARACAO_LEI_1512010
    ).first()

    assert response.status_code == status.HTTP_200_OK
    assert (
        documento_de_recebimento.status
        == DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )
    assert not tipos_de_documentos.filter(
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_RASTREABILIDADE
    ).exists()
    assert tipos_de_documentos.count() == 3
    assert laudo_atualizado.arquivos.count() == 2
    assert outros_atualizado.arquivos.count() == 2
    assert outros_atualizado.descricao_documento == "Outro após a correção."
    assert declaracao_criado.arquivos.count() == 2


def test_url_documentos_de_recebimento_fornecedor_corrige_validacao(
    documento_de_recebimento_factory,
    client_autenticado_fornecedor,
    arquivo_base64,
    django_user_model,
    cronograma_factory,
    tipo_de_documento_de_recebimento_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    cronograma = cronograma_factory.create(
        empresa=empresa,
    )
    documento_de_recebimento = documento_de_recebimento_factory.create(
        cronograma=cronograma,
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_CORRECAO,
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento,
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS,
        descricao_documento="Outro que precisa ser corrigido.",
    )
    tipo_de_documento_de_recebimento_factory.create(
        documento_recebimento=documento_de_recebimento,
        tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_RASTREABILIDADE,
    )

    # testa validação de correção sem arquivo de Laudo
    dados_correcao_sem_laudo = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_DECLARACAO_LEI_1512010,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Declaracao1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Declaracao2.jpg"},
                ],
            }
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao_sem_laudo),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # testa validação sem arquivos de documentos
    dados_correcao_sem_documentos = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Laudo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Laudo2.jpg"},
                ],
            }
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao_sem_documentos),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # testa validação com payload incompleto
    dados_correcao_sem_arquivos = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {
                        "arquivo": arquivo_base64,
                    },
                    {
                        "arquivo": arquivo_base64,
                    },
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_DECLARACAO_LEI_1512010,
                "arquivos_do_tipo_de_documento": [
                    {
                        "arquivo": arquivo_base64,
                    },
                    {
                        "arquivo": arquivo_base64,
                    },
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao_sem_arquivos),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # testa validação com payload com documento do tipo Outros sem o campo descricao_documento
    dados_correcao_sem_arquivos = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Laudo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Laudo2.jpg"},
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_OUTROS,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Outro1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Outro2.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao_sem_arquivos),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_documentos_de_recebimento_fornecedor_corrige_erro_transicao_estado(
    documento_de_recebimento_factory,
    client_autenticado_fornecedor,
    arquivo_base64,
    django_user_model,
    cronograma_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    cronograma = cronograma_factory.create(
        empresa=empresa,
    )
    documento_de_recebimento = documento_de_recebimento_factory.create(
        cronograma=cronograma, status=DocumentoDeRecebimento.workflow_class.APROVADO
    )

    dados_correcao = {
        "tipos_de_documentos": [
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Laudo1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Laudo2.jpg"},
                ],
            },
            {
                "tipo_documento": TipoDeDocumentoDeRecebimento.TIPO_DOC_DECLARACAO_LEI_1512010,
                "arquivos_do_tipo_de_documento": [
                    {"arquivo": arquivo_base64, "nome": "Declaracao1.jpg"},
                    {"arquivo": arquivo_base64, "nome": "Declaracao2.jpg"},
                ],
            },
        ],
    }

    response = client_autenticado_fornecedor.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/corrigir-documentos/",
        content_type="application/json",
        data=json.dumps(dados_correcao),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_calendario_cronograma_list_ok(
    client_autenticado_dilog_cronograma,
    etapas_do_cronograma_factory,
    cronograma_factory,
):
    """Deve obter lista filtrada por mes e ano de etapas do cronograma."""
    mes = "5"
    ano = "2023"
    data_programada = datetime.date(int(ano), int(mes), 1)
    cronogramas = [
        cronograma_factory.create(status=CronogramaWorkflow.ASSINADO_CODAE),
        cronograma_factory.create(status=CronogramaWorkflow.ALTERACAO_CODAE),
        cronograma_factory.create(status=CronogramaWorkflow.SOLICITADO_ALTERACAO),
    ]
    etapas_cronogramas = [
        etapas_do_cronograma_factory.create(
            cronograma=cronograma, data_programada=data_programada
        )
        for cronograma in cronogramas
    ]

    response = client_autenticado_dilog_cronograma.get(
        "/calendario-cronogramas/",
        {"mes": mes, "ano": ano},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == len(etapas_cronogramas)


def test_calendario_cronograma_list_not_authorized(client_autenticado):
    """Deve retornar status HTTP 403 ao tentar obter listagem com usuário não autorizado."""
    response = client_autenticado.get("/calendario-cronogramas/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_rascunho_ficha_tecnica_list_metodo_nao_permitido(
    client_autenticado_fornecedor, ficha_tecnica_factory
):
    url = "/rascunho-ficha-tecnica/"
    response = client_autenticado_fornecedor.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_rascunho_ficha_tecnica_retrieve_metodo_nao_permitido(
    client_autenticado_fornecedor, ficha_tecnica_factory
):
    url = f"/rascunho-ficha-tecnica/{ficha_tecnica_factory().uuid}/"
    response = client_autenticado_fornecedor.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_rascunho_ficha_tecnica_create_update(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_rascunho,
    arquivo_pdf_base64,
):
    response_create = client_autenticado_fornecedor.post(
        "/rascunho-ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_rascunho),
    )

    ultima_ficha_criada = FichaTecnicaDoProduto.objects.last()

    assert response_create.status_code == status.HTTP_201_CREATED
    assert (
        response_create.json()["numero"] == f"FT{str(ultima_ficha_criada.pk).zfill(3)}"
    )

    payload_ficha_tecnica_rascunho["pregao_chamada_publica"] = "0987654321"
    payload_ficha_tecnica_rascunho["arquivo"] = arquivo_pdf_base64
    response_update = client_autenticado_fornecedor.put(
        f'/rascunho-ficha-tecnica/{response_create.json()["uuid"]}/',
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_rascunho),
    )
    ficha = FichaTecnicaDoProduto.objects.last()

    assert response_update.status_code == status.HTTP_200_OK
    assert ficha.pregao_chamada_publica == "0987654321"
    assert ficha.arquivo


def test_ficha_tecnica_create_ok(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_pereciveis),
    )

    ficha = FichaTecnicaDoProduto.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["numero"] == f"FT{str(ficha.pk).zfill(3)}"
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE


def test_ficha_tecnica_create_from_rascunho_ok(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_rascunho,
    payload_ficha_tecnica_pereciveis,
):
    response = client_autenticado_fornecedor.post(
        "/rascunho-ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_rascunho),
    )

    ficha_rascunho = FichaTecnicaDoProduto.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["numero"] == f"FT{str(ficha_rascunho.pk).zfill(3)}"
    assert ficha_rascunho.status == FichaTecnicaDoProdutoWorkflow.RASCUNHO

    response = client_autenticado_fornecedor.put(
        f"/ficha-tecnica/{ficha_rascunho.uuid}/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_pereciveis),
    )

    ficha_criada = FichaTecnicaDoProduto.objects.last()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["numero"] == f"FT{str(ficha_criada.pk).zfill(3)}"
    assert ficha_criada.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    assert ficha_rascunho.numero == ficha_criada.numero


def test_ficha_tecnica_validate_pereciveis(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    # testa validação dos atributos presentes somente em perecíveis
    payload = {**payload_ficha_tecnica_pereciveis}
    attrs_obrigatorios_pereciveis = {
        "numero_registro",
        "agroecologico",
        "organico",
        "prazo_validade_descongelamento",
        "temperatura_congelamento",
        "temperatura_veiculo",
        "condicoes_de_transporte",
        "variacao_percentual",
    }
    for attr in attrs_obrigatorios_pereciveis:
        payload.pop(attr)

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "Fichas Técnicas de Produtos PERECÍVEIS exigem que sejam forncecidos valores para os campos"
        + " numero_registro, agroecologico, organico, prazo_validade_descongelamento, temperatura_congelamento"
        + ", temperatura_veiculo, condicoes_de_transporte e variacao_percentual."
    ]

    # testa validação dos atributos dependentes organico e mecanismo_controle
    payload = {**payload_ficha_tecnica_pereciveis}
    payload.pop("mecanismo_controle")

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "É obrigatório fornecer um valor para atributo mecanismo_controle quando o produto for orgânico."
    ]

    # testa validação dos atributos dependentes alergenicos e ingredientes_alergenicos
    payload = {**payload_ficha_tecnica_pereciveis}
    payload.pop("ingredientes_alergenicos")

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "É obrigatório fornecer um valor para atributo ingredientes_alergenicos quando o produto for alergênico."
    ]

    # testa validação dos atributos dependentes lactose e lactose_detalhe
    payload = {**payload_ficha_tecnica_pereciveis}
    payload.pop("lactose_detalhe")

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "É obrigatório fornecer um valor para atributo lactose_detalhe quando o produto possuir lactose."
    ]


def test_ficha_tecnica_validate_nao_pereciveis(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_nao_pereciveis,
):
    payload = {**payload_ficha_tecnica_nao_pereciveis}
    payload.pop("produto_eh_liquido")

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam forncecidos valores para o campo produto_eh_liquido"
    ]

    # testa validação dos atributos volume_embalagem_primaria e unidade_medida_volume_primaria
    payload = {**payload_ficha_tecnica_nao_pereciveis}
    payload.pop("volume_embalagem_primaria")

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "É obrigatório fornecer um valor para os atributos volume_embalagem_primaria e unidade_medida_volume_primaria quando o produto for líquido."
    ]


def test_ficha_tecnica_validate_arquivo(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    payload_ficha_tecnica_pereciveis["arquivo"] = "string qualquer"

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_pereciveis),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["arquivo"] == ["Arquivo deve ser um PDF."]


def test_ficha_tecnica_validate_embalagens_de_acordo_com_anexo(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    payload_ficha_tecnica_pereciveis["embalagens_de_acordo_com_anexo"] = False

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_pereciveis),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["embalagens_de_acordo_com_anexo"] == [
        "Checkbox indicando que as embalagens estão de acordo com o Anexo I precisa ser marcado."
    ]


def test_ficha_tecnica_validate_rotulo_legivel(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    payload_ficha_tecnica_pereciveis["rotulo_legivel"] = False

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload_ficha_tecnica_pereciveis),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["rotulo_legivel"] == [
        "Checkbox indicando que o rótulo contém as informações solicitadas no Anexo I precisa ser marcado."
    ]


def test_ficha_tecnica_list_ok(
    client_autenticado_fornecedor, ficha_tecnica_factory, django_user_model
):
    """Deve obter lista paginada e filtrada de fichas técnicas."""
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    url = "/ficha-tecnica/"
    fichas_criadas = [ficha_tecnica_factory.create(empresa=empresa) for _ in range(25)]
    response = client_autenticado_fornecedor.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Teste de paginação
    assert response.data["count"] == len(fichas_criadas)
    assert len(response.data["results"]) == DefaultPagination.page_size
    assert response.data["next"] is not None

    # Acessa a próxima página
    next_page = response.data["next"]
    next_response = client_autenticado_fornecedor.get(next_page)
    assert next_response.status_code == status.HTTP_200_OK

    # Tenta acessar uma página que não existe
    response_not_found = client_autenticado_fornecedor.get("/ficha-tecnica/?page=1000")
    assert response_not_found.status_code == status.HTTP_404_NOT_FOUND

    # Testa a resposta em caso de erro (por exemplo, sem autenticação)
    client_nao_autenticado = APIClient()
    response_error = client_nao_autenticado.get("/ficha-tecnica/")
    assert response_error.status_code == status.HTTP_401_UNAUTHORIZED

    # Teste de consulta com parâmetros
    data = datetime.date.today() - datetime.timedelta(days=1)
    response_filtro = client_autenticado_fornecedor.get(
        f"/ficha-tecnica/?data_cadastro={data}"
    )
    assert response_filtro.status_code == status.HTTP_200_OK
    assert response_filtro.data["count"] == 0


def test_ficha_tecnica_list_not_authorized(client_autenticado):
    """Deve retornar status HTTP 403 ao tentar obter listagem com usuário não autorizado."""
    response = client_autenticado.get("/ficha-tecnica/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ficha_tecnica_retrieve_ok(
    client_autenticado_fornecedor, ficha_tecnica_factory, django_user_model
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    ficha_tecnica = ficha_tecnica_factory.create(empresa=empresa)
    url = f"/ficha-tecnica/{ficha_tecnica.uuid}/"
    response = client_autenticado_fornecedor.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == FichaTecnicaDetalharSerializer(ficha_tecnica).data


def test_url_dashboard_ficha_tecnica_status_retornados(
    client_autenticado_codae_dilog, ficha_tecnica_factory, django_user_model
):
    user_id = client_autenticado_codae_dilog.session["_auth_user_id"]
    user = django_user_model.objects.get(id=user_id)
    status_esperados = ServiceDashboardFichaTecnica.get_dashboard_status(user)
    for state in status_esperados:
        ficha_tecnica_factory(status=state)

    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/")

    assert response.status_code == status.HTTP_200_OK

    status_recebidos = [result["status"] for result in response.json()["results"]]

    for status_recebido in status_recebidos:
        assert status_recebido in status_esperados


@pytest.mark.parametrize(
    "status_card",
    [
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
    ],
)
def test_url_dashboard_ficha_tecnica_com_filtro(
    client_autenticado_codae_dilog, ficha_tecnica_factory, status_card
):
    fichas_tecnicas = ficha_tecnica_factory.create_batch(size=10, status=status_card)

    filtros = {"numero_ficha": fichas_tecnicas[0].numero}
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_produto": fichas_tecnicas[0].produto.nome}
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_empresa": fichas_tecnicas[0].empresa.nome_fantasia}
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1


@pytest.mark.parametrize(
    "status_card",
    [
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
    ],
)
def test_url_dashboard_ficha_tecnica_ver_mais(
    client_autenticado_codae_dilog, ficha_tecnica_factory, status_card
):
    fichas_tecnicas = ficha_tecnica_factory.create_batch(size=10, status=status_card)

    filtros = {"status": status_card, "offset": 0, "limit": 10}
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]["dados"]) == 10

    assert response.json()["results"]["total"] == len(fichas_tecnicas)


@pytest.mark.parametrize(
    "status_card",
    [
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
    ],
)
def test_url_dashboard_ficha_tecnica_ver_mais_com_filtros(
    client_autenticado_codae_dilog, ficha_tecnica_factory, status_card
):
    fichas_tecnicas = ficha_tecnica_factory.create_batch(size=10, status=status_card)

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_ficha": fichas_tecnicas[0].numero,
    }
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": fichas_tecnicas[0].produto.nome,
    }
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_empresa": fichas_tecnicas[0].empresa.nome_fantasia,
    }
    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/", filtros)

    assert len(response.json()["results"]["dados"]) == 1


@pytest.mark.parametrize(
    "status_card",
    [
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
    ],
)
def test_url_dashboard_ficha_tecnica_quantidade_itens_por_card(
    client_autenticado_codae_dilog, ficha_tecnica_factory, status_card
):
    ficha_tecnica_factory.create_batch(size=10, status=status_card)

    response = client_autenticado_codae_dilog.get("/ficha-tecnica/dashboard/")

    assert response.status_code == status.HTTP_200_OK

    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 6


def test_url_ficha_tecnica_lista_simples(
    client_autenticado_dilog_cronograma, ficha_tecnica_factory, cronograma_factory
):
    FICHAS_VINCULADAS = 5

    fichas = ficha_tecnica_factory.create_batch(
        size=35, status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    )

    for ficha in fichas[:FICHAS_VINCULADAS]:
        cronograma_factory(ficha_tecnica=ficha)

    response = client_autenticado_dilog_cronograma.get(
        "/ficha-tecnica/lista-simples-sem-cronograma/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(fichas) - FICHAS_VINCULADAS

    ficha = [
        ficha
        for ficha in response.json()["results"]
        if ficha["uuid"] == str(fichas[FICHAS_VINCULADAS].uuid)
    ].pop()
    assert (
        ficha["numero_e_produto"]
        == f"{fichas[FICHAS_VINCULADAS].numero} - {fichas[FICHAS_VINCULADAS].produto.nome}"
    )
    assert ficha["uuid_empresa"] is not None


def test_url_ficha_tecnica_dados_cronograma(
    client_autenticado_dilog_cronograma, ficha_tecnica_factory
):
    ficha = ficha_tecnica_factory()

    response = client_autenticado_dilog_cronograma.get(
        f"/ficha-tecnica/{ficha.uuid}/dados-cronograma/"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_ficha_tecnica_rascunho_analise_create(
    client_autenticado_codae_dilog,
    ficha_tecnica_perecivel_enviada_para_analise,
    payload_rascunho_analise_ficha_tecnica,
):
    response = client_autenticado_codae_dilog.post(
        f"/ficha-tecnica/{ficha_tecnica_perecivel_enviada_para_analise.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_rascunho_analise_ficha_tecnica),
    )
    analises = AnaliseFichaTecnica.objects.all()

    assert response.status_code == status.HTTP_201_CREATED
    assert analises.count() == 1
    assert (
        analises.first().ficha_tecnica == ficha_tecnica_perecivel_enviada_para_analise
    )


def test_url_ficha_tecnica_detalhar_com_analise_ok(
    client_autenticado_codae_dilog,
    ficha_tecnica_perecivel_enviada_para_analise,
    analise_ficha_tecnica_factory,
):
    ficha_tecnica = ficha_tecnica_perecivel_enviada_para_analise
    analise_ficha_tecnica_factory.create(ficha_tecnica=ficha_tecnica)
    url = f"/ficha-tecnica/{ficha_tecnica.uuid}/detalhar-com-analise/"

    response = client_autenticado_codae_dilog.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == FichaTecnicaComAnaliseDetalharSerializer(ficha_tecnica).data
    assert response.data["analise"] is not None


def test_url_ficha_tecnica_rascunho_analise_update(
    client_autenticado_codae_dilog,
    analise_ficha_tecnica,
    payload_rascunho_analise_ficha_tecnica,
):
    payload_atualizacao = {**payload_rascunho_analise_ficha_tecnica}
    payload_atualizacao["detalhes_produto_conferido"] = False
    payload_atualizacao["detalhes_produto_correcoes"] = "Uma correção qualquer..."

    response = client_autenticado_codae_dilog.put(
        f"/ficha-tecnica/{analise_ficha_tecnica.ficha_tecnica.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_atualizacao),
    )
    analise = AnaliseFichaTecnica.objects.last()

    assert response.status_code == status.HTTP_200_OK
    assert AnaliseFichaTecnica.objects.count() == 1
    assert analise.detalhes_produto_conferido == False
    assert analise.detalhes_produto_correcoes == "Uma correção qualquer..."


def test_url_ficha_tecnica_rascunho_analise_update_criado_por(
    client_autenticado_codae_dilog,
    analise_ficha_tecnica,
    payload_rascunho_analise_ficha_tecnica,
):
    criado_por_antigo = analise_ficha_tecnica.criado_por
    response = client_autenticado_codae_dilog.put(
        f"/ficha-tecnica/{analise_ficha_tecnica.ficha_tecnica.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_rascunho_analise_ficha_tecnica),
    )
    analise_atualizada = AnaliseFichaTecnica.objects.last()

    assert response.status_code == status.HTTP_200_OK
    assert AnaliseFichaTecnica.objects.count() == 1
    assert analise_atualizada.criado_por != criado_por_antigo
