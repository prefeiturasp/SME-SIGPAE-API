import pytest
from openpyxl import load_workbook
from openpyxl.cell import Cell

from sme_sigpae_api.dieta_especial.models import Alimento
from sme_sigpae_api.processamento_arquivos.dieta_especial import (
    importa_alimentos as imp_alimentos,
)
from sme_sigpae_api.processamento_arquivos.dieta_especial.importa_alimentos import (
    ProcessadorPlanilha,
)

pytestmark = pytest.mark.django_db


def test_importa_dietas_especiais(arquivo_carga_alimentos_com_informacoes):
    importacao = imp_alimentos(arquivo_carga_alimentos_com_informacoes)
    assert importacao is None


def test_existe_conteudo_retorna_true(arquivo_carga_alimentos_com_informacoes):
    processador = ProcessadorPlanilha(arquivo_carga_alimentos_com_informacoes)
    tem_conteudo = processador.existe_conteudo()
    assert tem_conteudo is True


def test_existe_conteudo_retorna_false(arquivo_carga_alimentos_e_substitutos):
    processador = ProcessadorPlanilha(arquivo_carga_alimentos_e_substitutos)
    tem_conteudo = processador.existe_conteudo()
    assert tem_conteudo is False


def test_extensao_do_arquivo_esta_correta_retorna_true(
    arquivo_carga_alimentos_com_informacoes,
):
    processador = ProcessadorPlanilha(arquivo_carga_alimentos_com_informacoes)
    tem_extensao_correta = processador.extensao_do_arquivo_esta_correta()
    assert tem_extensao_correta is True


def test_extensao_do_arquivo_esta_correta_retorna_false(arquivo_extensao_incorreta):
    processador = ProcessadorPlanilha(arquivo_extensao_incorreta)
    tem_extensao_correta = processador.extensao_do_arquivo_esta_correta()
    assert tem_extensao_correta is False


def test_validacao_inicial(arquivo_carga_alimentos_com_informacoes):
    processador = ProcessadorPlanilha(arquivo_carga_alimentos_com_informacoes)
    validado = processador.validacao_inicial()
    assert validado is True


def test_monta_dicionario_de_dados(
    arquivo_carga_alimentos_com_informacoes,
    mock_cabecalho_e_informacoes_excel,
):
    cabecalhos, informacoes = mock_cabecalho_e_informacoes_excel
    linha = tuple(Cell(worksheet=None, value=valor) for valor in informacoes)
    dicionario = dict(zip(cabecalhos, informacoes))
    processador = ProcessadorPlanilha(arquivo_carga_alimentos_com_informacoes)
    dicionario_dados = processador.monta_dicionario_de_dados(linha)
    assert dicionario_dados == dicionario


# def test_processa_alimentos(arquivo_carga_alimentos_com_informacoes):
#     assert Alimento.objects.all().count() == 6
#     processador = ProcessadorPlanilha(arquivo_carga_alimentos_com_informacoes)
#     workbook = load_workbook(processador.path)
#     worksheet_alimentos = workbook.worksheets[0]
#     validado = processador.processa_alimentos(worksheet=worksheet_alimentos, tipo_listagem=Alimento.SO_ALIMENTOS)
#     assert validado is None
#     assert len(processador.erros) == 0
#     assert Alimento.objects.all().count() == 6
