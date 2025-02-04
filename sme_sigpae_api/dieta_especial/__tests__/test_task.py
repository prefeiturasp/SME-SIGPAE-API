from datetime import date
import uuid
import pytest
from sme_sigpae_api.dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from sme_sigpae_api.dados_comuns.fluxo_status import DietaEspecialWorkflow
from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.dieta_especial.models import LogQuantidadeDietasAutorizadas, LogQuantidadeDietasAutorizadasCEI, PlanilhaDietasAtivas, SolicitacaoDietaEspecial
from sme_sigpae_api.dieta_especial.tasks import gera_logs_dietas_especiais_diariamente, gera_pdf_relatorio_dieta_especial_async, gera_pdf_relatorio_dietas_especiais_terceirizadas_async, get_escolas_task, processa_dietas_especiais_task
from model_mommy import mommy
from django.core.files.uploadedfile import SimpleUploadedFile

from sme_sigpae_api.escola.models import Escola


pytestmark = pytest.mark.django_db

def test_processa_dietas_especiais_task(usuario_com_pk, solicitacoes_processa_dieta_especial):
    solicitacoes = SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=date.today(),
        ativo=False,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )
    assert solicitacoes.count() == 3
    assert solicitacoes.filter(tipo_solicitacao=TIPO_SOLICITACAO_DIETA.get("ALTERACAO_UE")).count() == 2
    
    processa_dietas_especiais_task()
    
    solicitacoes = SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=date.today(),
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
        ],
    )
    assert solicitacoes.filter(ativo=True).count() == 2
    assert solicitacoes.filter(ativo=False).count() == 2
    
def test_cancela_dietas_ativas_automaticamente_task():
    pass

def test_get_escolas_task():
    pass

def test_gera_pdf_relatorio_dieta_especial_async(usuario_com_pk, escola_cei, alergias_intolerancias, solicitacoes_processa_dieta_especial):
    request_data = {
        "dre": escola_cei.diretoria_regional.uuid, 
        "escola": [escola_cei.uuid],  
        "diagnostico": [ai.pk for ai in alergias_intolerancias],  
        "data_inicial": "2024-01-01",  
        "data_final": "2024-01-31"  
    }
    ids_dietas = [dieta.pk for dieta in SolicitacaoDietaEspecial.objects.all()]
    
    resultado = gera_pdf_relatorio_dieta_especial_async(
        user=usuario_com_pk.username,
        nome_arquivo="relatorio_dieta_especial.pdf",
        data=request_data,
        ids_dietas=ids_dietas,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True
    
    
def test_gera_pdf_relatorio_dieta_especial(usuario_com_pk, escola_cei, alergias_intolerancias, solicitacoes_processa_dieta_especial):
    request_data = {
        "dre": escola_cei.diretoria_regional.uuid,
        "escola": [escola_cei.uuid],  
        "diagnostico": [ai.pk for ai in alergias_intolerancias],  
        "data_inicial": "2024-01-01", 
        "data_final": "2024-01-31"  
    }
    ids_dietas = [dieta.pk for dieta in SolicitacaoDietaEspecial.objects.all()]
    nome_arquivo="relatorio_dieta_especial.pdf"
    
    gera_pdf_relatorio_dieta_especial_async(
        user=usuario_com_pk.username,
        nome_arquivo=nome_arquivo,
        data=request_data,
        ids_dietas=ids_dietas,
    )
    central_download = CentralDeDownload.objects.get(identificador=nome_arquivo)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO

def test_gera_logs_dietas_especiais_diariamente(solicitacoes_processa_dieta_especial, escola_cemei, escola_emebs, escola_cei, escola_dre_guaianases):
    assert Escola.objects.filter(tipo_gestao__nome="TERC TOTAL").count() == 4
    gera_logs_dietas_especiais_diariamente()
    assert LogQuantidadeDietasAutorizadas.objects.all().count() == 0
    assert LogQuantidadeDietasAutorizadasCEI.objects.all().count() == 0
    
    
def test_gera_pdf_relatorio_dietas_especiais_terceirizadas_async(usuario_com_pk, escola_cei, alergias_intolerancias, solicitacoes_processa_dieta_especial):
    request_data = {
        "status_selecionado":  "CANCELADAS"
    }
    ids_dietas = [dieta.pk for dieta in SolicitacaoDietaEspecial.objects.all()]
    resultado = gera_pdf_relatorio_dietas_especiais_terceirizadas_async.delay(
        user=usuario_com_pk.username,
        data=request_data,
        nome_arquivo="relatorio_dietas_especiais.pdf",
        ids_dietas=ids_dietas,
        filtros="texto a ser enviado",
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True
    
def test_gera_pdf_relatorio_dietas_especiais_terceirizadas(usuario_com_pk, escola_cei, alergias_intolerancias, solicitacoes_processa_dieta_especial):
    request_data = {
        "status_selecionado":  "CANCELADAS"
    }
    ids_dietas = [dieta.pk for dieta in SolicitacaoDietaEspecial.objects.all()]
    nome_arquivo="relatorio_dietas_especiais.pdf"
    gera_pdf_relatorio_dietas_especiais_terceirizadas_async(
        user=usuario_com_pk.username,
        data=request_data,
        nome_arquivo=nome_arquivo,
        ids_dietas=ids_dietas,
        filtros="texto a ser enviado",
    )
    central_download = CentralDeDownload.objects.get(identificador=nome_arquivo)
    assert central_download.arquivo is not None
    assert central_download.status == CentralDeDownload.STATUS_ERRO
    assert central_download.msg_erro == "'NoneType' object has no attribute 'codigo_eol'"
    # TODO: Tem erro aqui