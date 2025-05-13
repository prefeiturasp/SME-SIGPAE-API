import pytest

from sme_sigpae_api.dieta_especial.models import ClassificacaoDieta
from sme_sigpae_api.escola.models import Escola

from ..importa_dietas_especiais import ProcessadorPlanilha
from ..schemas import ArquivoCargaDietaEspecialSchema
from sme_sigpae_api.processamento_arquivos.dieta_especial import importa_dietas_especiais as imp_dietas


pytestmark = pytest.mark.django_db


def test_eh_exatamente_mesma_solicitacao(
    dieta_especial_ativa, arquivo_carga_dieta_especial, usuario
):
    dicionario_dados = {
        "dre": "BT",
        "tipo_gestao": "Terceirizada",
        "tipo_unidade": "DIRETA",
        "codigo_escola": "12345678",
        "nome_unidade": "Uma Unidade",
        "codigo_eol_aluno": "1234567",
        "nome_aluno": "Anderson Marques",
        "data_nascimento": "11/01/1989",
        "data_ocorrencia": "11/01/1989",
        "codigo_diagnostico": "Aluno Alérgico",
        "protocolo_dieta": "Alérgico",
        "codigo_categoria_dieta": "A",
    }
    solicitacao_dieta_schema = ArquivoCargaDietaEspecialSchema(**dicionario_dados)
    processador = ProcessadorPlanilha(usuario, arquivo_carga_dieta_especial)
    with pytest.raises(Exception):
        processador.eh_exatamente_mesma_solicitacao(
            solicitacao=dieta_especial_ativa,
            solicitacao_dieta_schema=solicitacao_dieta_schema,
        )
    with pytest.raises(Exception):
        processador.consulta_relacao_lote_terceirizada(solicitacao=dieta_especial_ativa)
    monta_diagnosticos = processador.monta_diagnosticos(
        "Aluno Alérgico;Aluno Diabético"
    )
    assert len(monta_diagnosticos) == 2
    assert [diagnotisco.descricao for diagnotisco in monta_diagnosticos] == [
        "ALUNO ALÉRGICO",
        "ALUNO DIABÉTICO",
    ]
    assert processador.consulta_classificacao(
        solicitacao_dieta_schema
    ) == ClassificacaoDieta.objects.get(nome="Tipo A")
    dicionario_dados_categoria_incorreta = dicionario_dados
    dicionario_dados_categoria_incorreta["codigo_categoria_dieta"] = "B"
    solicitacao_dieta_schema_categoria_incorreta = ArquivoCargaDietaEspecialSchema(
        **dicionario_dados_categoria_incorreta
    )
    with pytest.raises(Exception):
        processador.consulta_classificacao(solicitacao_dieta_schema_categoria_incorreta)
    assert processador.consulta_escola(solicitacao_dieta_schema) == Escola.objects.get(
        codigo_codae="12345678"
    )
    dicionario_dados_escola_incorreta = dicionario_dados
    dicionario_dados_escola_incorreta["codigo_escola"] = "12345679"
    solicitacao_dieta_schema_escola_incorreta = ArquivoCargaDietaEspecialSchema(
        **dicionario_dados_escola_incorreta
    )
    with pytest.raises(Exception):
        processador.consulta_escola(solicitacao_dieta_schema_escola_incorreta)


def test_importa_dietas_especiais(arquivo_carga_dieta_especial_com_arquivo, usuario):
    importacao = imp_dietas(usuario,arquivo_carga_dieta_especial_com_arquivo)
    assert importacao is None
    
