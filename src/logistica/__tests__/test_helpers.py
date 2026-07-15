import pytest

from src.logistica.api.helpers import (
    remove_acentos_de_strings,
    retorna_dados_normalizados_excel_entregas_distribuidor,
    retorna_dados_normalizados_excel_visao_dilog,
    retorna_dados_normalizados_excel_visao_distribuidor,
    retorna_motivo_insucesso,
    retorna_ocorrencias_alimento,
    retorna_status_das_requisicoes,
    retorna_status_guia_remessa,
    retorna_status_para_usuario,
    valida_rf_ou_cpf,
)
from src.logistica.models import SolicitacaoRemessa

pytestmark = pytest.mark.django_db


def test_remove_acentos_de_strings():
    string = remove_acentos_de_strings("educação")
    assert string == "educacao"


def test_retorna_statis_das_resquisicoes():
    status0 = retorna_status_das_requisicoes([])
    status1 = retorna_status_das_requisicoes([" "])
    status2 = retorna_status_das_requisicoes(["Todos"])
    status3 = retorna_status_das_requisicoes(
        ["Aguardando envio", "Enviada", "Cancelada", "Confirmada", "Em análise"]
    )
    todos_status = [
        "AGUARDANDO_ENVIO",
        "DILOG_ENVIA",
        "CANCELADA",
        "DISTRIBUIDOR_CONFIRMA",
        "DISTRIBUIDOR_SOLICITA_ALTERACAO",
    ]
    assert status0 == todos_status
    assert status1 == todos_status
    assert status2 == todos_status
    assert status3 == todos_status


def test_retorna_status_para_usuario():
    status0 = retorna_status_para_usuario("Papa enviou a requisição")
    status1 = retorna_status_para_usuario("Dilog Enviou a requisição")
    status2 = retorna_status_para_usuario("Distribuidor confirmou requisição")
    status3 = retorna_status_para_usuario("Distribuidor pede alteração da requisição")
    status4 = retorna_status_para_usuario("Cancelada")
    assert status0 == "Aguardando envio"
    assert status1 == "Enviada"
    assert status2 == "Confirmada"
    assert status3 == "Em análise"
    assert status4 == "Cancelada"


def test_retorna_dados_normalizados_excel_visao_distribuidor(solicitacao):
    queryset = SolicitacaoRemessa.objects.filter(uuid=f"{str(solicitacao.uuid)}")
    requisicoes = retorna_dados_normalizados_excel_visao_distribuidor(queryset)
    esperado = {
        "numero_solicitacao": "559890",
        "guias__data_entrega": None,
        "guias__alimentos__nome_alimento": None,
        "guias__nome_unidade": None,
        "guias__escola__codigo_eol": None,
        "guias__endereco_unidade": None,
        "guias__numero_unidade": None,
        "guias__bairro_unidade": None,
        "guias__cep_unidade": None,
        "guias__telefone_unidade": None,
        "guias__numero_guia": None,
        "guias__alimentos__embalagens__tipo_embalagem": None,
        "guias__alimentos__embalagens__qtd_volume": None,
        "guias__alimentos__embalagens__descricao_embalagem": None,
        "guias__alimentos__embalagens__capacidade_embalagem": None,
        "guias__alimentos__embalagens__unidade_medida": None,
        "guias__alimentos__codigo_suprimento": None,
        "guias__escola__subprefeitura__agrupamento": None,
        "status_requisicao": "Aguardando envio",
    }
    assert requisicoes.last() == esperado


def test_retorna_dados_normalizados_excel_visao_dilog(solicitacao):
    queryset = SolicitacaoRemessa.objects.filter(id__in=[str(solicitacao.id)])
    requisicoes = retorna_dados_normalizados_excel_visao_dilog(queryset)
    esperado = {
        "distribuidor__nome_fantasia": "Alimentos SA",
        "numero_solicitacao": "559890",
        "quantidade_total_guias": 2,
        "guias__numero_guia": None,
        "guias__status": None,
        "guias__data_entrega": None,
        "guias__codigo_unidade": None,
        "guias__nome_unidade": None,
        "guias__endereco_unidade": None,
        "guias__numero_unidade": None,
        "guias__bairro_unidade": None,
        "guias__cep_unidade": None,
        "guias__cidade_unidade": None,
        "guias__estado_unidade": None,
        "guias__contato_unidade": None,
        "guias__telefone_unidade": None,
        "guias__alimentos__nome_alimento": None,
        "guias__alimentos__codigo_suprimento": None,
        "guias__alimentos__codigo_papa": None,
        "guias__alimentos__embalagens__tipo_embalagem": None,
        "guias__alimentos__embalagens__descricao_embalagem": None,
        "guias__alimentos__embalagens__capacidade_embalagem": None,
        "guias__alimentos__embalagens__unidade_medida": None,
        "guias__alimentos__embalagens__qtd_volume": None,
        "status_requisicao": "Aguardando envio",
        "codigo_eol_unidade": "",
    }
    assert requisicoes.last() == esperado


def test_retorna_dados_normalizados_excel_entregas_distribuidor(solicitacao):
    queryset = SolicitacaoRemessa.objects.filter(uuid=f"{str(solicitacao.uuid)}")
    requisicoes = retorna_dados_normalizados_excel_entregas_distribuidor(queryset)
    esperado = {
        "numero_solicitacao": "559890",
        "quantidade_total_guias": 2,
        "guias__numero_guia": None,
        "guias__data_entrega": None,
        "guias__codigo_unidade": None,
        "guias__escola__codigo_eol": None,
        "guias__nome_unidade": None,
        "guias__endereco_unidade": None,
        "guias__numero_unidade": None,
        "guias__bairro_unidade": None,
        "guias__cep_unidade": None,
        "guias__cidade_unidade": None,
        "guias__estado_unidade": None,
        "guias__contato_unidade": None,
        "guias__telefone_unidade": None,
        "guias__alimentos__nome_alimento": None,
        "guias__alimentos__codigo_suprimento": None,
        "guias__alimentos__codigo_papa": None,
        "guias__alimentos__embalagens__tipo_embalagem": None,
        "guias__alimentos__embalagens__descricao_embalagem": None,
        "guias__alimentos__embalagens__capacidade_embalagem": None,
        "guias__alimentos__embalagens__unidade_medida": None,
        "guias__alimentos__embalagens__qtd_volume": None,
        "guias__status": None,
        "guias__alimentos__embalagens__qtd_a_receber": None,
        "guias__insucessos__placa_veiculo": None,
        "guias__insucessos__nome_motorista": None,
        "guias__insucessos__criado_em": None,
        "guias__insucessos__hora_tentativa": None,
        "guias__insucessos__motivo": None,
        "guias__insucessos__justificativa": None,
        "guias__insucessos__criado_por__cpf": None,
        "guias__insucessos__criado_por__nome": None,
        "distribuidor__nome_fantasia": "Alimentos SA",
        "guias__escola__subprefeitura__agrupamento": None,
        "status_requisicao": "Aguardando envio",
    }
    assert requisicoes.last() == esperado


def test_retorna_ocorrencias_alimento():
    ocorrencias = retorna_ocorrencias_alimento(["AUSENCIA_PRODUTO"])
    assert ocorrencias == "Ausência do produto"


def test_retorna_status_guia_remessa():
    status = retorna_status_guia_remessa("CANCELADA")
    assert status == "Cancelada"


def test_valida_rf_ou_cpf(distribuidor):
    doc = valida_rf_ou_cpf(distribuidor)
    assert doc == "12345678910"


def test_retorna_motivo_insucesso():
    motivo = retorna_motivo_insucesso("OUTROS")
    assert motivo == "Outros"
