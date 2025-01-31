import uuid
from sme_sigpae_api.produto.tasks import gera_pdf_relatorio_produtos_homologados_async, gera_xls_relatorio_produtos_homologados_async, gera_xls_relatorio_produtos_suspensos_async


def test_gera_xls_relatorio_produtos_homologados_async(client_autenticado_vinculo_terceirizada_homologacao):
    _, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    usuario = homologacao_produto.criado_por
    request_data = {
        "agrupado_por_nome_e_marca": False,
        "nome_edital":"edital",
        "page": 1,
        "titulo_produto": "Arroz",
    }

    resultado = gera_xls_relatorio_produtos_homologados_async.delay(
        user=usuario.username,
        nome_arquivo=f'relatorio_produtos_homologados.xlsx',
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
    
    
def test_gera_pdf_relatorio_produtos_homologados_async(client_autenticado_vinculo_terceirizada_homologacao):
    _, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    usuario = homologacao_produto.criado_por
    request_data = {
        "agrupado_por_nome_e_marca": False,
        "nome_edital":"edital",
        "page": 1,
        "titulo_produto": "Arroz",
    }

    resultado = gera_pdf_relatorio_produtos_homologados_async.delay(
        user=usuario.username,
        nome_arquivo=f'relatorio_produtos_homologados.xlsx',
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
    

def test_gera_xls_relatorio_produtos_suspensos_async(client_autenticado_vinculo_terceirizada_homologacao):
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