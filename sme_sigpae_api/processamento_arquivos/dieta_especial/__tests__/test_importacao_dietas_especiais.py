import pandas as pd
import pytest
from openpyxl.cell import Cell

from sme_sigpae_api.dados_comuns.constants import StatusProcessamentoArquivo
from sme_sigpae_api.dieta_especial.models import (
    ArquivoCargaDietaEspecial,
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
)
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.processamento_arquivos.dieta_especial import (
    importa_dietas_especiais as imp_dietas,
)

from ..importa_dietas_especiais import ProcessadorPlanilha
from ..schemas import ArquivoCargaDietaEspecialSchema

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


def test_importa_dietas_especiais(
    arquivo_carga_dieta_especial_com_informacoes, usuario
):
    importacao = imp_dietas(usuario, arquivo_carga_dieta_especial_com_informacoes)
    assert importacao is None


def test_existe_conteudo_retorna_true(
    arquivo_carga_dieta_especial_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    tem_conteudo = processador.existe_conteudo()
    assert tem_conteudo is True


def test_existe_conteudo_retorna_false(arquivo_carga_dieta_especial, usuario):
    processador = ProcessadorPlanilha(usuario, arquivo_carga_dieta_especial)
    tem_conteudo = processador.existe_conteudo()
    assert tem_conteudo is False


def test_extensao_do_arquivo_esta_correta_retorna_true(
    arquivo_carga_dieta_especial_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    tem_extensao_correta = processador.extensao_do_arquivo_esta_correta()
    assert tem_extensao_correta is True


def test_extensao_do_arquivo_esta_correta_retorna_false(
    arquivo_extensao_incorreta, usuario
):
    processador = ProcessadorPlanilha(usuario, arquivo_extensao_incorreta)
    tem_extensao_correta = processador.extensao_do_arquivo_esta_correta()
    assert tem_extensao_correta is False


def test_validacao_inicial(arquivo_carga_dieta_especial_com_informacoes, usuario):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    validado = processador.validacao_inicial()
    assert validado is True


def test_monta_dicionario_de_dados(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    mock_cabecalho_e_informacoes_excel,
):
    cabecalhos, informacoes = mock_cabecalho_e_informacoes_excel
    linha = tuple(Cell(worksheet=None, value=valor) for valor in informacoes)
    dicionario = dict(zip(cabecalhos, informacoes))
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    dicionario_dados = processador.monta_dicionario_de_dados(linha)
    assert dicionario_dados == dicionario


def test_consulta_aluno(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    aluno,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    aluno_excel = processador.consulta_aluno(solicitacao_dieta_schema)
    assert aluno_excel == aluno


def test_consulta_aluno_nao_existe(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
):
    solicitacao_dieta_schema.codigo_eol_aluno = 0
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    with pytest.raises(
        Exception,
        match=f"Erro: Aluno com código eol {solicitacao_dieta_schema.codigo_eol_aluno} não encontrado.",
    ):
        processador.consulta_aluno(solicitacao_dieta_schema)


def test_consulta_aluno_nome_incorreto(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    aluno,
):
    solicitacao_dieta_schema.nome_aluno = "ALUNO"
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    erro = f"Erro: Nome divergente para o código eol {aluno.codigo_eol}: Nome aluno planilha: {solicitacao_dieta_schema.nome_aluno.upper()} != Nome aluno sistema: {aluno.nome}"
    with pytest.raises(Exception, match=erro):
        processador.consulta_aluno(solicitacao_dieta_schema)


def test_consulta_escola(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    escola,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    escola_excel = processador.consulta_escola(solicitacao_dieta_schema)
    assert escola_excel == escola


def test_consulta_escola_nao_existe(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
):
    solicitacao_dieta_schema.codigo_escola = 0
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    with pytest.raises(
        Exception,
        match=f"Erro: escola com código codae {solicitacao_dieta_schema.codigo_escola} não encontrada.",
    ):
        processador.consulta_escola(solicitacao_dieta_schema)


def test_consulta_protocolo_padrao(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    escola,
    protocolo_padrao_dieta_especial,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    protocolo_padrao = processador.consulta_protocolo_padrao(
        solicitacao_dieta_schema, escola
    )
    assert protocolo_padrao == protocolo_padrao_dieta_especial


def test_consulta_protocolo_padrao_sem_escola(
    arquivo_carga_dieta_especial_com_informacoes, usuario, solicitacao_dieta_schema
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    with pytest.raises(
        Exception,
        match=f"Erro: Escola inválida. Não foi possível encontrar os editais e protocolos.",
    ):
        processador.consulta_protocolo_padrao(solicitacao_dieta_schema, None)


def test_consulta_protocolo_padrao_sem_protocolo(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    escola,
):
    solicitacao_dieta_schema.protocolo_dieta = 0
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    with pytest.raises(Exception):
        processador.consulta_protocolo_padrao(solicitacao_dieta_schema, escola)


def test_consulta_classificacao(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    classificacao_dieta,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    classificacao_dieta_excel = processador.consulta_classificacao(
        solicitacao_dieta_schema
    )
    assert classificacao_dieta_excel == classificacao_dieta


def test_consulta_classificacao_nao_existe(
    arquivo_carga_dieta_especial_com_informacoes, usuario, solicitacao_dieta_schema
):
    solicitacao_dieta_schema.codigo_categoria_dieta = 0
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    with pytest.raises(
        Exception,
        match=f"Erro: A categoria da dieta {solicitacao_dieta_schema.codigo_categoria_dieta} não encontrado.",
    ):
        processador.consulta_classificacao(solicitacao_dieta_schema)


def test_monta_diagnosticos(
    arquivo_carga_dieta_especial_com_informacoes, usuario, solicitacao_dieta_schema
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    diagnostico = processador.monta_diagnosticos(
        solicitacao_dieta_schema.codigo_diagnostico
    )
    assert len(diagnostico) == 4


def test_checa_existencia_solicitacao_eh_importado_true(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    aluno,
    solicitacao_dieta_especial,
):
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=True, eh_importado=True
        ).count()
        == 1
    )
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    solicitacao = processador.checa_existencia_solicitacao(
        solicitacao_dieta_schema, aluno
    )
    assert solicitacao is None
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=True, eh_importado=True
        ).count()
        == 1
    )


def test_checa_existencia_solicitacao_eh_importado_false(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    aluno,
    solicitacao_dieta_especial,
):
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=True, eh_importado=True
        ).count()
        == 1
    )
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=True, eh_importado=False
        ).count()
        == 0
    )

    solicitacao_dieta_especial.eh_importado = False
    solicitacao_dieta_especial.save()

    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    solicitacao = processador.checa_existencia_solicitacao(
        solicitacao_dieta_schema, aluno
    )
    assert solicitacao is None
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=False, eh_importado=False
        ).count()
        == 1
    )
    assert (
        SolicitacaoDietaEspecial.objects.filter(
            aluno=aluno, ativo=True, eh_importado=False
        ).count()
        == 0
    )


def test_cria_solicitacao(
    arquivo_carga_dieta_especial_com_informacoes,
    usuario,
    solicitacao_dieta_schema,
    aluno,
    classificacao_dieta,
    escola,
    protocolo_padrao_dieta_especial,
    alergia_intolerancia,
    perfil,
    substituicao_alimento,
):
    assert SolicitacaoDietaEspecial.objects.all().count() == 0
    assert SubstituicaoAlimento.objects.all().count() == 0
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    solicitacao = processador.cria_solicitacao(
        solicitacao_dieta_schema,
        aluno,
        classificacao_dieta,
        alergia_intolerancia,
        escola,
        protocolo_padrao_dieta_especial,
    )
    assert solicitacao is None
    assert SolicitacaoDietaEspecial.objects.all().count() == 1
    assert SubstituicaoAlimento.objects.all().count() == 1


def test_finaliza_processamento(
    usuario, arquivo_carga_dieta_especial_com_informacoes, perfil
):
    assert (
        ArquivoCargaDietaEspecial.objects.last().status
        == StatusProcessamentoArquivo.PENDENTE.value
    )
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    processador.processamento()
    processador.finaliza_processamento()
    assert (
        ArquivoCargaDietaEspecial.objects.last().status
        == StatusProcessamentoArquivo.SUCESSO.value
    )


def test_finaliza_processamento_com_erro(
    usuario, arquivo_carga_dieta_especial_com_informacoes
):
    assert (
        ArquivoCargaDietaEspecial.objects.last().status
        == StatusProcessamentoArquivo.PENDENTE.value
    )
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_dieta_especial_com_informacoes
    )
    processador.processamento()
    processador.finaliza_processamento()
    assert (
        ArquivoCargaDietaEspecial.objects.last().status
        == StatusProcessamentoArquivo.PROCESSADO_COM_ERRO.value
    )

    resultado = ArquivoCargaDietaEspecial.objects.last().resultado
    df = pd.read_excel(resultado)
    messagem_erro = "Linha 2 - Perfil matching query does not exist."
    assert messagem_erro in df["Erros encontrados no processamento da planilha"].values


def test_processamento_erro_validacao_inicial(usuario, arquivo_extensao_incorreta):
    processador = ProcessadorPlanilha(usuario, arquivo_extensao_incorreta)
    assert len(processador.erros) == 0
    erro_validacao_inicial = processador.processamento()
    assert erro_validacao_inicial is None
    assert len(processador.erros) == 0


def test_processamento_erro_colunas(usuario, arquivo_colunas_incorreta):
    processador = ProcessadorPlanilha(usuario, arquivo_colunas_incorreta)
    assert len(processador.erros) == 0
    erro_colunas = processador.processamento()
    assert erro_colunas is None
    assert len(processador.erros) == 1
    assert (
        processador.erros[0]
        == "Erro: O número de colunas diferente das estrutura definida."
    )
