import io
import uuid

import pytest

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.models import CentralDeDownload
from sme_sigpae_api.produto.models import HomologacaoProduto, Produto
from sme_sigpae_api.produto.tasks import (
    gera_pdf_relatorio_produtos_homologados_async,
    gera_xls_relatorio_produtos_homologados_async,
    gera_xls_relatorio_produtos_suspensos_async,
)

pytestmark = pytest.mark.django_db


def test_gera_xls_relatorio_produtos_homologados_async(
    client_autenticado_vinculo_terceirizada_homologacao,
):
    _, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    usuario = homologacao_produto.criado_por
    request_data = {
        "agrupado_por_nome_e_marca": False,
        "nome_edital": "edital",
        "page": 1,
        "titulo_produto": "Arroz",
    }

    resultado = gera_xls_relatorio_produtos_homologados_async.delay(
        user=usuario.username,
        nome_arquivo=f"relatorio_produtos_homologados.xlsx",
        data=request_data,
        perfil_nome=usuario.vinculo_atual.perfil.nome,
        tipo_usuario=usuario.tipo_usuario,
        object_id=usuario.vinculo_atual.object_id,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True


def test_gera_pdf_relatorio_produtos_homologados_async(
    client_autenticado_vinculo_terceirizada_homologacao,
):
    _, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    usuario = homologacao_produto.criado_por
    request_data = {
        "agrupado_por_nome_e_marca": False,
        "nome_edital": "edital",
        "page": 1,
        "titulo_produto": "Arroz",
    }

    resultado = gera_pdf_relatorio_produtos_homologados_async.delay(
        user=usuario.username,
        nome_arquivo=f"relatorio_produtos_homologados.xlsx",
        data=request_data,
        perfil_nome=usuario.vinculo_atual.perfil.nome,
        tipo_usuario=usuario.tipo_usuario,
        object_id=usuario.vinculo_atual.object_id,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True


def test_gera_xls_relatorio_produtos_suspensos_async(
    client_autenticado_vinculo_terceirizada_homologacao,
):
    _, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    usuario = homologacao_produto.criado_por
    resultado = gera_xls_relatorio_produtos_suspensos_async.delay(
        produtos_uuids=["97224852-7e35-4e73-ab0a-237cd9e34a6f"],
        nome_arquivo="relatorio_produtos_suspensos.pdf",
        nome_edital="edital",
        user=usuario.username,
        data_final="2025-01-10",
        filtros=[],
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True


def test_gera_xls_relatorio_produtos_homologados(hom_produto_com_editais):
    user = hom_produto_com_editais.criado_por
    nome_arquivo = "relatorio.xlsx"
    data = {
        "agrupado_por_nome_e_marca": True,
        "nome_edital": "Edital de Pregão nº 41/sme/2017",
    }
    perfil_nome = constants.ADMINISTRADOR_EMPRESA
    tipo_usuario = "Admin"
    object_id = 1

    gera_xls_relatorio_produtos_homologados_async(
        user, nome_arquivo, data, perfil_nome, tipo_usuario, object_id
    )

    central_download = CentralDeDownload.objects.filter(
        identificador=nome_arquivo
    ).first()
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    assert central_download.identificador == nome_arquivo
    assert central_download.arquivo is not None
    assert central_download.msg_erro == ""
    assert central_download.visto is False
    assert central_download.usuario == user


def test_gera_pdf_relatorio_produtos_homologados(hom_produto_com_editais):
    user = hom_produto_com_editais.criado_por
    nome_arquivo = "relatorio.xlsx"
    data = {
        "agrupado_por_nome_e_marca": True,
        "nome_edital": "Edital de Pregão nº 41/sme/2017",
    }
    perfil_nome = constants.ADMINISTRADOR_EMPRESA
    tipo_usuario = "Admin"
    object_id = 1

    gera_pdf_relatorio_produtos_homologados_async(
        user, nome_arquivo, data, perfil_nome, tipo_usuario, object_id
    )

    central_download = CentralDeDownload.objects.filter(
        identificador=nome_arquivo
    ).first()
    assert central_download.status == CentralDeDownload.STATUS_CONCLUIDO
    assert central_download.identificador == nome_arquivo
    assert central_download.arquivo is not None
    assert central_download.msg_erro == ""
    assert central_download.visto is False
    assert central_download.usuario == user
