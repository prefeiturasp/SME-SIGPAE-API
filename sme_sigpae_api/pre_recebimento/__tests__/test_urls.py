import datetime
import json
import uuid
import copy

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.api.paginations import DefaultPagination
from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
    DocumentoDeRecebimentoWorkflow,
    FichaTecnicaDoProdutoWorkflow,
    LayoutDeEmbalagemWorkflow,
)
from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    SolicitacaoAlteracaoCronograma,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.services import (
    ServiceDashboardDocumentosDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
    TipoDeDocumentoDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaComAnaliseDetalharSerializer,
    FichaTecnicaDetalharSerializer,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.services import (
    ServiceDashboardFichaTecnica,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.api.services import (
    ServiceDashboardLayoutEmbalagem,
)
from sme_sigpae_api.pre_recebimento.layout_embalagem.models import LayoutDeEmbalagem
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)
from sme_sigpae_api.terceirizada.models import Terceirizada

fake = Faker("pt_BR")


def test_rascunho_cronograma_create_ok(
    client_autenticado_dilog_cronograma,
    contrato,
    empresa,
    unidade_medida_logistica,
    armazem,
    ficha_tecnica_perecivel_enviada_para_analise,
    tipo_emabalagem_qld,
):
    qtd_total_empenho = fake.random_number() / 100
    custo_unitario_produto = fake.random_number() / 100
    observacoes = "aaaa"

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
                "etapa": 1,
            },
        ],
        "programacoes_de_recebimento": [
            {
                "data_programada": "22/08/2022 - Etapa 1 - Parte 1",
                "tipo_carga": "PALETIZADA",
            }
        ],
        "ficha_tecnica": str(ficha_tecnica_perecivel_enviada_para_analise.uuid),
        "tipo_embalagem_secundaria": str(tipo_emabalagem_qld.uuid),
        "custo_unitario_produto": custo_unitario_produto,
        "observacoes": observacoes,
    }

    response = client_autenticado_dilog_cronograma.post(
        "/cronogramas/", content_type="application/json", data=json.dumps(payload)
    )

    obj = Cronograma.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    assert obj.contrato == contrato
    assert obj.empresa == empresa
    assert obj.unidade_medida == unidade_medida_logistica
    assert obj.armazem == armazem
    assert obj.ficha_tecnica == ficha_tecnica_perecivel_enviada_para_analise
    assert obj.tipo_embalagem_secundaria == tipo_emabalagem_qld
    assert obj.custo_unitario_produto == custo_unitario_produto
    assert obj.etapas.first().qtd_total_empenho == qtd_total_empenho
    assert obj.observacoes == observacoes


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


def test_url_list_cronogramas_relatorio(
    client_autenticado_codae_dilog, cronograma_factory
):
    cronograma_factory.create_batch(size=11)
    response = client_autenticado_codae_dilog.get(f"/cronogramas/listagem-relatorio/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_list_cronogramas_relatorio_filtros(
    client_autenticado_codae_dilog, empresa_factory, cronograma_factory
):
    empresa1 = empresa_factory.create(tipo_servico=Terceirizada.FORNECEDOR)
    empresa2 = empresa_factory.create(tipo_servico=Terceirizada.FORNECEDOR)
    cronograma_factory.create_batch(size=2, empresa=empresa1)
    cronograma_factory.create_batch(size=2, empresa=empresa2)
    response1 = client_autenticado_codae_dilog.get(
        f"/cronogramas/listagem-relatorio/?empresa={empresa1.uuid}"
    )
    response2 = client_autenticado_codae_dilog.get(
        f"/cronogramas/listagem-relatorio/?empresa={empresa1.uuid}&empresa={empresa2.uuid}"
    )
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK
    json1 = response1.json()
    json2 = response2.json()
    assert json1["count"] == 2
    assert json2["count"] == 4


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
                "etapa": 4,
                "parte": 2,
                "data_programada": "2023-06-03",
                "quantidade": 123,
                "total_embalagens": 333,
            },
            {
                "etapa": 1,
                "parte": 1,
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
                "etapa": 4,
                "parte": 2,
                "data_programada": "2023-06-03",
                "quantidade": 123,
                "total_embalagens": 333,
            },
            {
                "etapa": 1,
                "parte": 1,
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
                {"numero_empenho": "1891425", "etapa": 1},
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


def test_url_perfil_dilog_abastecimento_cronograma(
    client_autenticado_dilog_abastecimento, solicitacao_cronograma_ciente
):
    data = json.dumps({"aprovado": True})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-abastecimento/",
        data,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_ciente.uuid
    )
    assert obj.status == "APROVADO_DILOG_ABASTECIMENTO"


def test_url_perfil_dilog_abastecimento_reprova_alteracao_cronograma(
    client_autenticado_dilog_abastecimento, solicitacao_cronograma_ciente
):
    data = json.dumps(
        {"justificativa_abastecimento": "teste justificativa", "aprovado": False}
    )
    response = client_autenticado_dilog_abastecimento.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-abastecimento/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_ciente.uuid
    )
    assert obj.status == "REPROVADO_DILOG_ABASTECIMENTO"


def test_url_analise_dilog_abastecimento_erro_parametro_aprovado_invalida(
    client_autenticado_dilog_abastecimento, solicitacao_cronograma_ciente
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": ""})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_ciente.uuid}/analise-abastecimento/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_analise_dilog_abastecimento_erro_solicitacao_cronograma_invalido(
    client_autenticado_dilog_abastecimento,
):
    response = client_autenticado_dilog_abastecimento.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{uuid.uuid4()}/analise-abastecimento/",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_analise_dilog_abastecimento_erro_transicao_estado(
    client_autenticado_dilog_abastecimento,
    solicitacao_cronograma_aprovado_dilog_abastecimento,
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": True})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dilog_abastecimento.uuid}/analise-abastecimento/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_perfil_dilog_aprova_alteracao_cronograma(
    client_autenticado_dilog_diretoria,
    solicitacao_cronograma_aprovado_dilog_abastecimento,
):
    data = json.dumps({"aprovado": True})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dilog_abastecimento.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_aprovado_dilog_abastecimento.uuid
    )
    assert obj.status == "APROVADO_DILOG"


def test_url_perfil_dilog_reprova_alteracao_cronograma(
    client_autenticado_dilog_diretoria,
    solicitacao_cronograma_aprovado_dilog_abastecimento,
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": False})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dilog_abastecimento.uuid}/analise-dilog/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = SolicitacaoAlteracaoCronograma.objects.get(
        uuid=solicitacao_cronograma_aprovado_dilog_abastecimento.uuid
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
    client_autenticado_dilog_diretoria,
    solicitacao_cronograma_aprovado_dilog_abastecimento,
):
    data = json.dumps({"justificativa_dilog": "teste justificativa", "aprovado": ""})
    response = client_autenticado_dilog_diretoria.patch(
        f"/solicitacao-de-alteracao-de-cronograma/{solicitacao_cronograma_aprovado_dilog_abastecimento.uuid}/analise-dilog/",
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
    client_autenticado_fornecedor,
    cronograma_factory,
):
    cronograma = cronograma_factory(
        status=CronogramaWorkflow.ASSINADO_E_ENVIADO_AO_FORNECEDOR
    )

    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_fornecedor.patch(
        f"/cronogramas/{cronograma.uuid}/fornecedor-assina-cronograma/",
        data,
        content_type="application/json",
    )
    obj = Cronograma.objects.get(uuid=cronograma.uuid)

    assert response.status_code == status.HTTP_200_OK
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
            {"numero_empenho": "1891425", "etapa": 1},
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


def test_url_cronograma_gerar_relatorio_xlsx_async(client_autenticado_dilog_cronograma):
    response = client_autenticado_dilog_cronograma.get(
        "/cronogramas/gerar-relatorio-xlsx-async/"
    )

    obj_central_download = CentralDeDownload.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert obj_central_download is not None
    assert obj_central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    assert obj_central_download.arquivo is not None
    assert obj_central_download.arquivo.size > 0


def test_url_cronograma_gerar_relatorio_pdf_async(client_autenticado_dilog_cronograma):
    response = client_autenticado_dilog_cronograma.get(
        "/cronogramas/gerar-relatorio-pdf-async/"
    )

    obj_central_download = CentralDeDownload.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert obj_central_download is not None
    assert obj_central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    assert obj_central_download.arquivo is not None
    assert obj_central_download.arquivo.size > 0


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
            {"numero_empenho": "1891425", "etapa": 1},
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
        "password": constants.DJANGO_ADMIN_TREINAMENTO_PASSWORD,
        "contrato": str(contrato.uuid),
        "cadastro_finalizado": True,
        "etapas": [
            {"numero_empenho": "123456789"},
            {"numero_empenho": "1891425", "etapa": 1},
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


def test_url_dilog_abastecimento_assina_cronograma_authorized(
    client_autenticado_dilog_abastecimento,
    cronograma_factory,
):
    cronograma = cronograma_factory(status=CronogramaWorkflow.ASSINADO_FORNECEDOR)

    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/cronogramas/{cronograma.uuid}/abastecimento-assina/",
        data,
        content_type="application/json",
    )
    obj = Cronograma.objects.get(uuid=cronograma.uuid)

    assert response.status_code == status.HTTP_200_OK
    assert obj.status == "ASSINADO_DILOG_ABASTECIMENTO"


def test_url_dilog_abastecimento_assina_cronograma_erro_senha(
    client_autenticado_dilog_abastecimento, cronograma_assinado_fornecedor
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_TREINAMENTO_PASSWORD})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/cronogramas/{cronograma_assinado_fornecedor.uuid}/abastecimento-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_dilog_abastecimento_assina_cronograma_erro_cronograma_invalido(
    client_autenticado_dilog_abastecimento,
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/cronogramas/{uuid.uuid4()}/abastecimento-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_url_dilog_abastecimento_assina_cronograma_erro_transicao_estado(
    client_autenticado_dilog_abastecimento, cronograma
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_abastecimento.patch(
        f"/cronogramas/{cronograma.uuid}/abastecimento-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_dilog_abastecimento_assina_cronograma_not_authorized(
    client_autenticado_dilog, cronograma_recebido
):
    response = client_autenticado_dilog.patch(
        f"/cronogramas/{cronograma_recebido.uuid}/abastecimento-assina/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_dilog_assina_cronograma_authorized(
    client_autenticado_dilog_diretoria, cronograma_assinado_perfil_dilog_abastecimento
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_PASSWORD})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_perfil_dilog_abastecimento.uuid}/codae-assina/",
        data,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    obj = Cronograma.objects.get(
        uuid=cronograma_assinado_perfil_dilog_abastecimento.uuid
    )
    assert obj.status == "ASSINADO_CODAE"


def test_url_dilog_assina_cronograma_erro_senha(
    client_autenticado_dilog_diretoria, cronograma_assinado_perfil_dilog_abastecimento
):
    data = json.dumps({"password": constants.DJANGO_ADMIN_TREINAMENTO_PASSWORD})
    response = client_autenticado_dilog_diretoria.patch(
        f"/cronogramas/{cronograma_assinado_perfil_dilog_abastecimento.uuid}/codae-assina/",
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
    client_autenticado_dilog_abastecimento, cronogramas_multiplos_status_com_log
):
    cronograma_com_log = Cronograma.objects.first()
    response = client_autenticado_dilog_abastecimento.get(
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


def test_url_dashboard_painel_usuario_dilog_abastecimento(
    client_autenticado_dilog_abastecimento, cronogramas_multiplos_status_com_log
):
    response = client_autenticado_dilog_abastecimento.get("/cronogramas/dashboard/")
    assert response.status_code == status.HTTP_200_OK

    status_esperados = [
        "ASSINADO_FORNECEDOR",
        "ASSINADO_DILOG_ABASTECIMENTO",
        "ASSINADO_CODAE",
    ]
    status_recebidos = [result["status"] for result in response.json()["results"]]
    for status_esperado in status_esperados:
        assert status_esperado in status_recebidos

    resultados_recebidos = [result for result in response.json()["results"]]
    for resultado in resultados_recebidos:
        if resultado["status"] == "ASSINADO_FORNECEDOR":
            assert len(resultado["dados"]) == 3
        elif resultado["status"] == "ASSINADO_DILOG_ABASTECIMENTO":
            assert len(resultado["dados"]) == 2
        elif resultado["status"] == "ASSINADO_CODAE":
            assert len(resultado["dados"]) == 1


def test_url_dashboard_painel_usuario_dilog_abastecimento_com_paginacao(
    client_autenticado_dilog_abastecimento, cronogramas_multiplos_status_com_log
):
    response = client_autenticado_dilog_abastecimento.get(
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
        CronogramaWorkflow.ASSINADO_DILOG_ABASTECIMENTO,
        CronogramaWorkflow.ASSINADO_CODAE,
    ],
)
def test_url_dashboard_cronograma_com_filtro(
    client_autenticado_dilog_abastecimento, cronograma_factory, status_card
):
    cronogramas = cronograma_factory.create_batch(size=10, status=status_card)

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_cronograma": cronogramas[0].numero,
    }
    response = client_autenticado_dilog_abastecimento.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": cronogramas[0].ficha_tecnica.produto.nome,
    }
    response = client_autenticado_dilog_abastecimento.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_fornecedor": cronogramas[0].empresa.razao_social,
    }
    response = client_autenticado_dilog_abastecimento.get(
        "/cronogramas/dashboard-com-filtro/", filtros
    )

    assert len(response.json()["results"][0]["dados"]) == 1


def test_url_dashboard_painel_solicitacao_alteracao_dilog_abastecimento(
    client_autenticado_dilog_abastecimento,
    cronogramas_multiplos_status_com_log_cronograma_ciente,
):
    response = client_autenticado_dilog_abastecimento.get(
        "/solicitacao-de-alteracao-de-cronograma/dashboard/"
    )

    QTD_STATUS_DASHBOARD_DILOG_ABASTECIMENTO = 5
    SOLICITACOES_STATUS_CRONOGRAMA_CIENTE = 2
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == QTD_STATUS_DASHBOARD_DILOG_ABASTECIMENTO
    assert response.json()["results"][0]["status"] == "CRONOGRAMA_CIENTE"
    assert (
        len(response.json()["results"][0]["dados"])
        == SOLICITACOES_STATUS_CRONOGRAMA_CIENTE
    )


def test_url_relatorio_cronograma_authorized(
    client_autenticado_dilog_abastecimento, cronograma
):
    response = client_autenticado_dilog_abastecimento.get(
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
        == UnidadeMedidaSimplesSerializer(unidades_medida, many=True).data
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


def test_url_cronograma_lista_cronogramas_ficha_recebimento(
    client_autenticado_qualidade,
    cronograma_factory,
):
    cronogramas_assinados_codae = cronograma_factory.create_batch(
        size=5, status=CronogramaWorkflow.ASSINADO_CODAE
    )
    cronograma_factory(status=CronogramaWorkflow.ASSINADO_DILOG_ABASTECIMENTO)

    response = client_autenticado_qualidade.get(
        "/cronogramas/lista-cronogramas-ficha-recebimento/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(cronogramas_assinados_codae)


def test_url_cronograma_dados_cronograma_ficha_recebimento(
    client_autenticado_qualidade,
    cronograma_factory,
    etapas_do_cronograma_factory,
    documento_de_recebimento_factory,
    data_de_fabricao_e_prazo_factory,
):
    cronograma = cronograma_factory(status=CronogramaWorkflow.ASSINADO_CODAE)
    etapas = etapas_do_cronograma_factory.create_batch(size=3, cronograma=cronograma)
    docs_recebimento = documento_de_recebimento_factory.create_batch(
        size=3, cronograma=cronograma, status=DocumentoDeRecebimentoWorkflow.APROVADO
    )
    documento_de_recebimento_factory(
        cronograma=cronograma,
        status=DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
    )
    datas_e_prazos = []
    for doc_recebimento in docs_recebimento:
        datas_e_prazos.extend(
            data_de_fabricao_e_prazo_factory.create_batch(
                size=3, documento_recebimento=doc_recebimento
            )
        )

    response = client_autenticado_qualidade.get(
        f"/cronogramas/{cronograma.uuid}/dados-cronograma-ficha-recebimento/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]["etapas"]) == len(etapas)
    assert len(response.json()["results"]["documentos_de_recebimento"]) == len(
        docs_recebimento
    )


def test_url_layout_de_embalagem_create(
    client_autenticado_fornecedor,
    payload_layout_embalagem,
):
    response = client_autenticado_fornecedor.post(
        "/layouts-de-embalagem/",
        content_type="application/json",
        data=json.dumps(payload_layout_embalagem),
    )

    assert response.status_code == status.HTTP_201_CREATED
    obj = LayoutDeEmbalagem.objects.last()
    assert obj.status == LayoutDeEmbalagem.workflow_class.ENVIADO_PARA_ANALISE
    assert obj.tipos_de_embalagens.count() == 2


def test_url_layout_de_embalagem_validate_ficha_tecnica(
    client_autenticado_fornecedor, ficha_tecnica_factory
):
    ficha = ficha_tecnica_factory(status=FichaTecnicaDoProdutoWorkflow.RASCUNHO)

    payload = {
        "ficha_tecnica": str(ficha.uuid),
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
        "/layouts-de-embalagem/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Não é possível vincular com Ficha Técnica em rascunho."
        in response.data["ficha_tecnica"]
    )
    assert (
        "Este campo é obrigatório."
        in response.data["tipos_de_embalagens"][0]["imagens_do_tipo_de_embalagem"]
    )


def test_url_layout_de_embalagem_listagem(
    client_autenticado_fornecedor, lista_layouts_de_embalagem
):
    """Deve obter lista paginada de layouts de embalagens."""
    client = client_autenticado_fornecedor
    response = client.get("/layouts-de-embalagem/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == len(lista_layouts_de_embalagem)
    assert len(response.data["results"]) == DefaultPagination.page_size
    assert response.data["next"] is not None


def test_url_layout_de_embalagem_detalhar(
    client_autenticado_codae_dilog, lista_layouts_de_embalagem
):
    layout = LayoutDeEmbalagem.objects.first()

    response = client_autenticado_codae_dilog.get(
        f"/layouts-de-embalagem/{layout.uuid}/"
    )
    dados = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert dados["uuid"] == str(layout.uuid)
    assert dados["observacoes"] == str(layout.observacoes)
    assert dados["status"] == layout.get_status_display()
    assert dados["numero_ficha_tecnica"] == str(layout.ficha_tecnica.numero)
    assert dados["nome_produto"] == str(layout.ficha_tecnica.produto.nome)
    assert (
        dados["nome_empresa"]
        == f"{layout.ficha_tecnica.empresa.nome_fantasia} / {layout.ficha_tecnica.empresa.razao_social}"
    )
    assert dados["pregao_chamada_publica"] == str(
        layout.ficha_tecnica.pregao_chamada_publica
    )


def test_url_dashboard_layout_embalagem_status_retornados(
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
def test_url_dashboard_layout_embalagem_quantidade_itens_por_card(
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
def test_url_dashboard_layout_embalagem_com_filtro(
    client_autenticado_codae_dilog, layout_de_embalagem_factory, status_card
):
    layouts = layout_de_embalagem_factory.create_batch(size=10, status=status_card)

    filtros = {"numero_ficha_tecnica": layouts[0].ficha_tecnica.numero}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_produto": layouts[0].ficha_tecnica.produto.nome}
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )
    dados_card = list(
        filter(lambda e: e["status"] == status_card, response.json()["results"])
    ).pop()["dados"]

    assert len(dados_card) == 1

    filtros = {"nome_fornecedor": layouts[0].ficha_tecnica.empresa.razao_social}
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
def test_url_dashboard_layout_embalagem_ver_mais(
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
def test_url_dashboard_layout_embalagem_ver_mais_com_filtros(
    client_autenticado_codae_dilog, layout_de_embalagem_factory, status_card
):
    layouts = layout_de_embalagem_factory.create_batch(size=10, status=status_card)

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "numero_ficha_tecnica": layouts[0].ficha_tecnica.numero,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_produto": layouts[0].ficha_tecnica.produto.nome,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1

    filtros = {
        "status": status_card,
        "offset": 0,
        "limit": 10,
        "nome_fornecedor": layouts[0].ficha_tecnica.empresa.razao_social,
    }
    response = client_autenticado_codae_dilog.get(
        "/layouts-de-embalagem/dashboard/", filtros
    )

    assert len(response.json()["results"]["dados"]) == 1


def test_url_layout_embalagem_analise_aprovando(
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


def test_url_layout_embalagem_analise_solicitando_correcao(
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


def test_url_layout_embalagem_validacao_primeira_analise(
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
        + "é menor que quantidade presente no Layout de Embalagem."
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert msg_erro in response.json()["tipos_de_embalagens"]


def test_url_layout_embalagem_analise_correcao(
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


def test_url_layout_embalagem_solicitacao_correcao_apos_aprovado(
    client_autenticado_codae_dilog, layout_de_embalagem_aprovado
):
    # Pede correção da embalagem terciaria que não foi enviada originalmente.
    layout_analisado = layout_de_embalagem_aprovado
    dados_analise = {
        "tipos_de_embalagens": [
            {
                "tipo_embalagem": "TERCIARIA",
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
    assert response.status_code == status.HTTP_200_OK


def test_url_layout_embalagem_validacao_analise_correcao(
    client_autenticado_codae_dilog, layout_de_embalagem_em_analise_com_correcao
):
    layout_analisado = layout_de_embalagem_em_analise_com_correcao
    tipos_embalagem_analisados = layout_analisado.tipos_de_embalagens.all()

    dados_analise = {
        "tipos_de_embalagens": [
            {
                "tipo_embalagem": "PRIMARIA",
                "status": "APROVADO",
                "complemento_do_status": "Teste complemento",
            },
            {
                "tipo_embalagem": "SECUNDARIA",
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
    msg_erro = "UUID obrigatório para o tipo de embalagem informado."
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        msg_erro
        in response.json()["tipos_de_embalagens"][0]["Layout Embalagem PRIMARIA"]
    )


def test_url_layout_de_embalagem_fornecedor_corrige(
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


def test_url_layout_de_embalagem_fornecedor_corrige_not_ok(
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


def test_url_layout_de_embalagem_fornecedor_atualiza(
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


def test_url_layout_de_embalagem_fornecedor_atualiza_not_ok(
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
        "numero_lote_laudo": "001",
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
    assert documento.numero_lote_laudo == "001"
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
    dados_atualizados["correcao_solicitada"] = (
        "Documentos corrompidos, sem possibilidade de análise."
    )
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
    client_autenticado_fornecedor,
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


@pytest.mark.django_db
def test_ficha_tecnica_create_envasador_null(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    payload = copy.deepcopy(payload_ficha_tecnica_pereciveis)
    payload["envasador_distribuidor"] = None

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_201_CREATED

    ficha = FichaTecnicaDoProduto.objects.last()
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    assert ficha.envasador_distribuidor is None

def test_ficha_tecnica_validate_pereciveis(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_pereciveis,
):
    # testa validação dos atributos presentes somente em perecíveis
    payload = {**payload_ficha_tecnica_pereciveis}
    attrs_obrigatorios_pereciveis = {
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
        + " agroecologico, organico, prazo_validade_descongelamento, temperatura_congelamento"
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
        "É obrigatório fornecer um valor para o atributo mecanismo_controle quando o produto for orgânico."
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
        "É obrigatório fornecer um valor para o atributo ingredientes_alergenicos quando o produto for alergênico."
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
        "É obrigatório fornecer um valor para o atributo lactose_detalhe quando o produto possuir lactose."
    ]


def test_ficha_tecnica_validate_nao_pereciveis(
    client_autenticado_fornecedor,
    payload_ficha_tecnica_nao_pereciveis,
):
    payload = {**payload_ficha_tecnica_nao_pereciveis}
    attrs_obrigatorios_nao_pereciveis = {
        "produto_eh_liquido",
        "agroecologico",
        "organico",
    }
    for attr in attrs_obrigatorios_nao_pereciveis:
        payload.pop(attr)

    response = client_autenticado_fornecedor.post(
        "/ficha-tecnica/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam forncecidos valores para os campos agroecologico, organico, e produto_eh_liquido"
    ]

    # teste de validação dos atributos volume_embalagem_primaria e unidade_medida_volume_primaria
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
        FichaTecnicaDoProdutoWorkflow.APROVADA,
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
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
        FichaTecnicaDoProdutoWorkflow.APROVADA,
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
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
        FichaTecnicaDoProdutoWorkflow.APROVADA,
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
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
        FichaTecnicaDoProdutoWorkflow.APROVADA,
        FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
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


def test_url_ficha_tecnica_lista_simples_sem_cronograma(
    client_autenticado_dilog_cronograma, ficha_tecnica_factory, cronograma_factory
):
    FICHAS_VINCULADAS = 5

    fichas = ficha_tecnica_factory.create_batch(
        size=10, status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    )

    for ficha in fichas[:FICHAS_VINCULADAS]:
        cronograma_factory(ficha_tecnica=ficha)

    response = client_autenticado_dilog_cronograma.get(
        "/ficha-tecnica/lista-simples-sem-cronograma/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(fichas) - FICHAS_VINCULADAS


def test_url_ficha_tecnica_lista_simples_sem_layout_embalagem(
    client_autenticado_fornecedor,
    ficha_tecnica_factory,
    empresa,
    layout_de_embalagem_factory,
):
    FICHAS_VINCULADAS = 5

    fichas = ficha_tecnica_factory.create_batch(
        size=10,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
        empresa=empresa,
    )

    for ficha in fichas[:FICHAS_VINCULADAS]:
        layout_de_embalagem_factory(ficha_tecnica=ficha)

    response = client_autenticado_fornecedor.get(
        "/ficha-tecnica/lista-simples-sem-layout-embalagem/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(fichas) - FICHAS_VINCULADAS


def test_url_ficha_tecnica_lista_simples_sem_questoes_conferencia(
    client_autenticado_qualidade,
    ficha_tecnica_factory,
    empresa,
    questoes_por_produto_factory,
):
    FICHAS_VINCULADAS = 5

    fichas = ficha_tecnica_factory.create_batch(
        size=10,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
        empresa=empresa,
    )

    for ficha in fichas[:FICHAS_VINCULADAS]:
        questoes_por_produto_factory(ficha_tecnica=ficha)

    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/lista-simples-sem-questoes-conferencia/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(fichas) - FICHAS_VINCULADAS


def test_url_ficha_tecnica_lista_simples(
    client_autenticado_fornecedor, ficha_tecnica_factory, empresa
):
    fichas = ficha_tecnica_factory.create_batch(
        size=10,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
        empresa=empresa,
    )

    response = client_autenticado_fornecedor.get("/ficha-tecnica/lista-simples/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == len(fichas)


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
    payload_analise_ficha_tecnica,
):
    response = client_autenticado_codae_dilog.post(
        f"/ficha-tecnica/{ficha_tecnica_perecivel_enviada_para_analise.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_analise_ficha_tecnica),
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
    assert (
        response.data
        == FichaTecnicaComAnaliseDetalharSerializer(
            ficha_tecnica,
            context={"request": response.wsgi_request},
        ).data
    )
    assert response.data["analise"] is not None


def test_url_ficha_tecnica_rascunho_analise_update(
    client_autenticado_codae_dilog,
    analise_ficha_tecnica,
    payload_analise_ficha_tecnica,
):
    payload_atualizacao = {**payload_analise_ficha_tecnica}
    payload_atualizacao["fabricante_envasador_conferido"] = False
    payload_atualizacao["fabricante_envasador_correcoes"] = "Correção fabricante"
    payload_atualizacao["detalhes_produto_conferido"] = False
    payload_atualizacao["detalhes_produto_correcoes"] = "Uma correção qualquer..."
    payload_atualizacao["responsavel_tecnico_conferido"] = False
    payload_atualizacao["responsavel_tecnico_correcoes"] = "Correção responsável"
    payload_atualizacao["modo_preparo_conferido"] = False
    payload_atualizacao["modo_preparo_correcoes"] = "Correção modo de preparo"

    response = client_autenticado_codae_dilog.put(
        f"/ficha-tecnica/{analise_ficha_tecnica.ficha_tecnica.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_atualizacao),
    )
    analise = AnaliseFichaTecnica.objects.last()

    assert response.status_code == status.HTTP_200_OK
    assert AnaliseFichaTecnica.objects.count() == 1
    assert analise.fabricante_envasador_conferido is False
    assert analise.fabricante_envasador_correcoes == "Correção fabricante"
    assert analise.detalhes_produto_conferido is False
    assert analise.detalhes_produto_correcoes == "Uma correção qualquer..."
    assert analise.responsavel_tecnico_conferido is False
    assert analise.responsavel_tecnico_correcoes == "Correção responsável"
    assert analise.modo_preparo_conferido is False
    assert analise.modo_preparo_correcoes == "Correção modo de preparo"


def test_url_ficha_tecnica_rascunho_analise_update_criado_por(
    client_autenticado_codae_dilog,
    analise_ficha_tecnica,
    payload_analise_ficha_tecnica,
):
    criado_por_antigo = analise_ficha_tecnica.criado_por
    response = client_autenticado_codae_dilog.put(
        f"/ficha-tecnica/{analise_ficha_tecnica.ficha_tecnica.uuid}/rascunho-analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_analise_ficha_tecnica),
    )
    analise_atualizada = AnaliseFichaTecnica.objects.last()

    assert response.status_code == status.HTTP_200_OK
    assert AnaliseFichaTecnica.objects.count() == 1
    assert analise_atualizada.criado_por != criado_por_antigo


def test_url_ficha_tecnica_analise_gpcodae_aprovacao(
    client_autenticado_codae_dilog,
    ficha_tecnica_perecivel_enviada_para_analise,
    payload_analise_ficha_tecnica,
):
    response = client_autenticado_codae_dilog.post(
        f"/ficha-tecnica/{ficha_tecnica_perecivel_enviada_para_analise.uuid}/analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_analise_ficha_tecnica),
    )
    analise = AnaliseFichaTecnica.objects.first()

    assert response.status_code == status.HTTP_201_CREATED
    assert analise.ficha_tecnica.status == FichaTecnicaDoProdutoWorkflow.APROVADA


def test_url_ficha_tecnica_analise_gpcodae_aprovacao_analise_rascunho(
    client_autenticado_codae_dilog,
    analise_ficha_tecnica,
    payload_analise_ficha_tecnica,
):
    analise = analise_ficha_tecnica
    response = client_autenticado_codae_dilog.put(
        f"/ficha-tecnica/{analise_ficha_tecnica.ficha_tecnica.uuid}/analise-gpcodae/",
        content_type="application/json",
        data=json.dumps(payload_analise_ficha_tecnica),
    )
    analise.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert analise.ficha_tecnica.status == FichaTecnicaDoProdutoWorkflow.APROVADA


def test_url_ficha_tecnica_analise_gpcodae_validate(
    client_autenticado_codae_dilog,
    ficha_tecnica_perecivel_enviada_para_analise,
    payload_analise_ficha_tecnica,
):
    # Test missing correcoes when conferido is False
    campos_para_testar = [
        "fabricante_envasador",
        "detalhes_produto",
        "responsavel_tecnico",
        "modo_preparo",
    ]

    for campo in campos_para_testar:
        payload_invalido = {**payload_analise_ficha_tecnica}
        payload_invalido[f"{campo}_conferido"] = False

        response = client_autenticado_codae_dilog.post(
            f"/ficha-tecnica/{ficha_tecnica_perecivel_enviada_para_analise.uuid}/analise-gpcodae/",
            content_type="application/json",
            data=json.dumps(payload_invalido),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not AnaliseFichaTecnica.objects.exists()

    # Test correcoes not empty when conferido is True
    for campo in campos_para_testar:
        payload_invalido = {**payload_analise_ficha_tecnica}
        payload_invalido[f"{campo}_correcoes"] = f"Correção para {campo}"

        response = client_autenticado_codae_dilog.post(
            f"/ficha-tecnica/{ficha_tecnica_perecivel_enviada_para_analise.uuid}/analise-gpcodae/",
            content_type="application/json",
            data=json.dumps(payload_invalido),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not AnaliseFichaTecnica.objects.exists()


def test_url_ficha_tecnica_correcao_fornecedor(
    client_autenticado_fornecedor,
    django_user_model,
    analise_ficha_tecnica_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    analise = analise_ficha_tecnica_factory.create(
        ficha_tecnica__empresa=empresa,
        ficha_tecnica__status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        armazenamento_conferido=False,
        armazenamento_correcoes=fake.pystr(max_chars=150),
    )
    ficha = analise.ficha_tecnica
    payload_correcao = {
        "password": constants.DJANGO_ADMIN_PASSWORD,
        "embalagem_primaria": fake.pystr(max_chars=150),
        "embalagem_secundaria": fake.pystr(max_chars=150),
    }

    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/correcao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_correcao),
    )

    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    assert ficha.analises.last().armazenamento_conferido is None
    assert analise.armazenamento_correcoes != ""


def test_url_ficha_tecnica_correcao_fornecedor_validate_status(
    client_autenticado_fornecedor,
    django_user_model,
    analise_ficha_tecnica_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    analise = analise_ficha_tecnica_factory.create(
        ficha_tecnica__empresa=empresa,
        ficha_tecnica__status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha = analise.ficha_tecnica

    payload_correcao = {"password": constants.DJANGO_ADMIN_PASSWORD}

    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/correcao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_correcao),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "status": [f"Não é possível corrigir uma Ficha no status {ficha.status}"]
    }


def test_url_ficha_tecnica_correcao_fornecedor_validate_campos_pereciveis(
    client_autenticado_fornecedor,
    django_user_model,
    analise_ficha_tecnica_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    analise = analise_ficha_tecnica_factory.create(
        ficha_tecnica__empresa=empresa,
        ficha_tecnica__categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        ficha_tecnica__status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        conservacao_conferido=False,
    )
    ficha = analise.ficha_tecnica
    payload_correcao = {
        "password": constants.DJANGO_ADMIN_PASSWORD,
        "condicoes_de_conservacao": fake.pystr(max_chars=150),
    }

    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/correcao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_correcao),
    )

    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "prazo_validade_descongelamento": ["Este campo é obrigatório."]
    }
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO


def test_url_ficha_tecnica_correcao_fornecedor_validate_campos_nao_pereciveis(
    client_autenticado_fornecedor,
    django_user_model,
    analise_ficha_tecnica_factory,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    analise = analise_ficha_tecnica_factory.create(
        ficha_tecnica__empresa=empresa,
        ficha_tecnica__categoria=FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        ficha_tecnica__status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        conservacao_conferido=False,
    )
    ficha = analise.ficha_tecnica

    # Testa campo obrigatório
    payload_correcao = {
        "password": constants.DJANGO_ADMIN_PASSWORD,
    }
    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/correcao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_correcao),
    )
    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "condicoes_de_conservacao": ["Este campo é obrigatório."]
    }
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO

    # Testa campo não permitido
    payload_correcao = {
        "password": constants.DJANGO_ADMIN_PASSWORD,
        "condicoes_de_conservacao": fake.pystr(max_chars=150),
        "produto_eh_liquido": False,
    }
    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/correcao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_correcao),
    )
    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "produto_eh_liquido": ["Este campo não é permitido nesta correção."]
    }
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO


def test_url_ficha_tecnica_atualizacao_fornecedor(
    client_autenticado_fornecedor,
    django_user_model,
    analise_ficha_tecnica_factory,
    payload_atualizacao_ficha_tecnica,
):
    user_id = client_autenticado_fornecedor.session["_auth_user_id"]
    empresa = django_user_model.objects.get(pk=user_id).vinculo_atual.instituicao
    analise = analise_ficha_tecnica_factory.create(
        ficha_tecnica__empresa=empresa,
        ficha_tecnica__status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha = analise.ficha_tecnica

    payload_atualizacao_ficha_tecnica["password"] = constants.DJANGO_ADMIN_PASSWORD

    response = client_autenticado_fornecedor.patch(
        f"/ficha-tecnica/{ficha.uuid}/atualizacao-fornecedor/",
        content_type="application/json",
        data=json.dumps(payload_atualizacao_ficha_tecnica),
    )

    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert ficha.status == FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
