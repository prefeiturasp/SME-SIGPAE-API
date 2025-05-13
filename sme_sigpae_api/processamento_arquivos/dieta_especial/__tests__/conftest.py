from io import BytesIO
from pathlib import Path
import uuid
from openpyxl import Workbook
import pytest
from model_mommy import mommy
from django.core.files.uploadedfile import SimpleUploadedFile
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    ArquivoCargaAlimentosSubstitutos,
    ArquivoCargaDietaEspecial,
    ArquivoCargaUsuariosEscola,
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
)


@pytest.fixture
def arquivo_carga_dieta_especial():
    return mommy.make(ArquivoCargaDietaEspecial)


@pytest.fixture
def arquivo_carga_alimentos_e_substitutos():
    return mommy.make(ArquivoCargaAlimentosSubstitutos)


@pytest.fixture
def arquivo_carga_usuarios_escola():
    return mommy.make(ArquivoCargaUsuariosEscola)

@pytest.fixture
def aluno():
    return mommy.make("escola.Aluno", codigo_eol="1234567", nome="TESTE ALUNO DIETA")

@pytest.fixture
def escola():
    return mommy.make("escola.Escola", codigo_codae="12345678", lote= mommy.make("Lote"))

@pytest.fixture
def classificacao_dieta():
    return  mommy.make(ClassificacaoDieta, nome="Tipo A")

@pytest.fixture
def edital(escola):
    edital = mommy.make(
        "Edital",
        numero="Edital MAIO/2025",
        uuid="12288b47-9d27-4089-8c2e-48a6061d83ea",
    )
    contrato = mommy.make(
        "Contrato",
        terceirizada=mommy.make("Terceirizada"),
        edital=edital,
        make_m2m=True,
        uuid="44d51e10-8999-48bb-889a-1540c9e8c895",
    )
    contrato.lotes.set([escola.lote])
    return edital

@pytest.fixture
def protocolo_padrao_dieta_especial(edital):
    protocolo= mommy.make(
        "ProtocoloPadraoDietaEspecial",
        nome_protocolo="ALERGIA - OVO",
        uuid="5d7f80b8-7b62-441b-89da-4d5dd5c1e7e8",
    )
    protocolo.editais.add(edital)
    return protocolo


@pytest.fixture
def dieta_especial_ativa(aluno, escola, classificacao_dieta):
    # aluno = mommy.make("escola.Aluno", codigo_eol="1234567", nome="TESTE ALUNO DIETA")
    # escola = mommy.make("escola.Escola", codigo_codae="12345678")
    # classificacao = mommy.make(ClassificacaoDieta, nome="Tipo A")
    alergias_set = mommy.prepare(
        AlergiaIntolerancia, descricao="Aluno Alérgico", _quantity=1
    )
    solicitacao = mommy.make(
        SolicitacaoDietaEspecial,
        aluno=aluno,
        ativo=True,
        classificacao=classificacao_dieta,
        escola_destino=escola,
        nome_protocolo="Alérgico",
        alergias_intolerancias=alergias_set,
        eh_importado=True,
    )
    return solicitacao


@pytest.fixture
def usuario():
    return mommy.make("perfil.Usuario")


@pytest.fixture
def arquivo_carga_dieta_especial_com_arquivo(arquivo_carga_dieta_especial, aluno, escola, protocolo_padrao_dieta_especial, classificacao_dieta):
    wb = Workbook()
    ws = wb.active
    cabecalhos = [
        "dre",
        "tipo_gestao",
        "tipo_unidade",
        "codigo_escola",
        "nome_unidade",
        "codigo_eol_aluno",
        "nome_aluno",
        "data_nascimento",
        "data_ocorrencia",
        "codigo_diagnostico",
        "protocolo_dieta",
        "codigo_categoria_dieta"
    ]
    ws.append(cabecalhos)
    dados_exemplo = [
        "DRE XYZ",              # dre
        "TERCEIRIZADA",         # tipo_gestao
        "EMEF",                   # tipo_unidade
        escola.codigo_codae,           # codigo_escola
        "Escola Teste",         # nome_unidade
        aluno.codigo_eol,        # codigo_eol_aluno (obrigatório)
        aluno.nome,         # nome_aluno
        "01/01/2010",       # data_nascimento
        "15/05/2023",       # data_ocorrencia
        "DIAG001",          # codigo_diagnostico (obrigatório)
        protocolo_padrao_dieta_especial.nome_protocolo,      # protocolo_dieta (obrigatório)
        "A"           # codigo_categoria_dieta (obrigatório)
    ]
    ws.append(dados_exemplo)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    arquivo = SimpleUploadedFile(
        name=f"{uuid.uuid4()}.xlsx",
        content=buffer.read(), 
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    arquivo_carga_dieta_especial.conteudo = arquivo
    arquivo_carga_dieta_especial.save()
    return arquivo_carga_dieta_especial
