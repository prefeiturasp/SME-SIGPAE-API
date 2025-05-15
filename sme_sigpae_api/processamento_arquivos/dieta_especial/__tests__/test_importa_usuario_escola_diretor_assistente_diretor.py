import pytest

from sme_sigpae_api.perfil.models.perfil import Vinculo
from sme_sigpae_api.perfil.models.usuario import Usuario
from sme_sigpae_api.processamento_arquivos.dieta_especial.importa_usuarios_escola_diretor_assistente_diretor import (
    ProcessadorPlanilha,
    importa_usuarios_escola,
)
from sme_sigpae_api.processamento_arquivos.dieta_especial.schemas import (
    ArquivoCargaUsuariosDiretorSchema,
)

pytestmark = pytest.mark.django_db


def test_existe_conteudo_retorna_true(
    arquivo_carga_usuario_escola_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    tem_conteudo = processador.existe_conteudo()
    assert tem_conteudo is True


def test_extensao_do_arquivo_esta_correta_retorna_true(
    arquivo_carga_usuario_escola_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    assert processador.extensao_do_arquivo_esta_correta() is True


def test_monta_dicionario_de_dados(
    arquivo_carga_usuario_escola_com_informacoes,
    usuario,
    dados_planilha_valida,
    linha_planilha_valida,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    resultado = processador.monta_dicionario_de_dados(linha_planilha_valida)
    assert resultado == dados_planilha_valida


def test_consulta_escola(arquivo_carga_usuario_escola_com_informacoes, usuario, escola):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    escola_encontrada = processador.consulta_escola(escola.codigo_eol)
    assert escola_encontrada == escola


def test_consulta_escola_nao_encontrada(
    arquivo_carga_usuario_escola_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    with pytest.raises(Exception, match="Escola não encontrada para o código: 000000."):
        processador.consulta_escola("000000")


def test_checa_usuario_sem_conflito(
    arquivo_carga_usuario_escola_com_informacoes, usuario
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    usuario = processador.checa_usuario("1111111", "usuario@email", "Novo Usuário")
    assert usuario is None


def test_checa_usuario_com_conflito(
    arquivo_carga_usuario_escola_com_informacoes, usuario, usuario_diretor
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    with pytest.raises(Exception):
        processador.checa_usuario(
            usuario_diretor.registro_funcional,
            usuario_diretor.email,
            "Usuário Conflitante",
        )


def test_criar_usuario_diretor(
    arquivo_carga_usuario_escola_com_informacoes,
    usuario,
    escola,
    dados_planilha_valida,
    perfil_diretor,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    schema = ArquivoCargaUsuariosDiretorSchema(**dados_planilha_valida)
    assert Usuario.objects.count() == 1
    assert Vinculo.objects.count() == 0

    processador._ProcessadorPlanilha__criar_usuario_diretor(schema)

    assert Usuario.objects.count() == 2
    assert Vinculo.objects.count() == 1


def test_criar_usuario_assistente(
    arquivo_carga_usuario_escola_com_informacoes,
    usuario,
    escola,
    dados_planilha_valida,
    perfil_diretor,
):
    processador = ProcessadorPlanilha(
        usuario, arquivo_carga_usuario_escola_com_informacoes
    )
    schema = ArquivoCargaUsuariosDiretorSchema(**dados_planilha_valida)

    assert Usuario.objects.count() == 1
    assert Vinculo.objects.count() == 0

    processador._ProcessadorPlanilha__criar_usuario_assitente(schema)

    assert Usuario.objects.count() == 2
    assert Vinculo.objects.count() == 1


def test_processamento_completo(
    arquivo_carga_usuario_escola_com_informacoes, usuario, escola, perfil_diretor
):
    Usuario.objects.all().delete()
    Vinculo.objects.all().delete()

    importa_usuarios_escola(usuario, arquivo_carga_usuario_escola_com_informacoes)

    assert Usuario.objects.count() == 1
    assert Vinculo.objects.count() == 1


def test_extensao_do_arquivo_esta_correta_retorna_false(
    arquivo_extensao_incorreta, usuario
):
    processador = ProcessadorPlanilha(usuario, arquivo_extensao_incorreta)
    tem_extensao_correta = processador.extensao_do_arquivo_esta_correta()
    assert tem_extensao_correta is False


def test_processamento_erro_validacao_inicial(usuario, arquivo_extensao_incorreta):
    processador = ProcessadorPlanilha(usuario, arquivo_extensao_incorreta)
    assert len(processador.erros) == 0
    erro_validacao_inicial = processador.processamento()
    assert erro_validacao_inicial is None
    assert len(processador.erros) == 0
