import pytest
from model_bakery import baker

from src.dados_comuns.models import LogSolicitacoesUsuario
from src.produto.models import DadosHistoricosProduto, HomologacaoProduto
from src.produto.services.dados_historicos_produto import (
    ServicoDadosHistoricosProduto,
)

pytestmark = pytest.mark.django_db


def criar_log(homologacao, usuario):
    return baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=homologacao.uuid,
        solicitacao_tipo=LogSolicitacoesUsuario.HOMOLOGACAO_PRODUTO,
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        usuario=usuario,
    )


def test_registrar_dados_historicos_do_produto(homologacao_produto, user):
    log = criar_log(homologacao_produto, user)

    dados_historicos = ServicoDadosHistoricosProduto.registrar(
        log,
        homologacao_produto,
    )

    produto = homologacao_produto.produto
    assert dados_historicos.log == log
    assert str(dados_historicos.produto_uuid) == str(produto.uuid)
    assert dados_historicos.empresa == (
        homologacao_produto.rastro_terceirizada.nome_fantasia
    )
    assert dados_historicos.criado_em_produto == produto.criado_em
    assert dados_historicos.nome_produto == produto.nome
    assert dados_historicos.marca == produto.marca.nome
    assert dados_historicos.fabricante == produto.fabricante.nome
    assert (
        dados_historicos.eh_para_alunos_com_dieta
        == produto.eh_para_alunos_com_dieta
    )
    assert dados_historicos.componentes == produto.componentes
    assert dados_historicos.perfil_responsavel == user.vinculo_atual.perfil.nome
    assert dados_historicos.nome_instituicao == user.vinculo_atual.instituicao.nome


def test_registrar_dados_historicos_e_idempotente(homologacao_produto, user):
    log = criar_log(homologacao_produto, user)

    primeiro_registro = ServicoDadosHistoricosProduto.registrar(
        log,
        homologacao_produto,
    )
    segundo_registro = ServicoDadosHistoricosProduto.registrar(
        log,
        homologacao_produto,
    )

    assert primeiro_registro.pk == segundo_registro.pk
    assert DadosHistoricosProduto.objects.filter(log=log).count() == 1


def test_dados_historicos_nao_sao_alterados_com_o_produto(
    homologacao_produto,
    user,
):
    produto = homologacao_produto.produto
    log_original = criar_log(homologacao_produto, user)
    dados_originais = ServicoDadosHistoricosProduto.registrar(
        log_original,
        homologacao_produto,
    )

    nome_original = produto.nome
    componentes_originais = produto.componentes
    produto.nome = "Produto atualizado"
    produto.componentes = "Componentes atualizados"
    produto.save()

    dados_originais.refresh_from_db()
    novo_log = criar_log(homologacao_produto, user)
    novos_dados = ServicoDadosHistoricosProduto.registrar(
        novo_log,
        homologacao_produto,
    )

    assert dados_originais.nome_produto == nome_original
    assert dados_originais.componentes == componentes_originais
    assert novos_dados.nome_produto == "Produto atualizado"
    assert novos_dados.componentes == "Componentes atualizados"


def test_registrar_dados_historicos_sem_dados_opcionais(
    homologacao_produto,
    usuario,
):
    produto = homologacao_produto.produto
    produto.marca = None
    produto.fabricante = None
    produto.save()
    homologacao_produto.rastro_terceirizada = None
    homologacao_produto.save()
    log = criar_log(homologacao_produto, usuario)

    dados_historicos = ServicoDadosHistoricosProduto.registrar(
        log,
        homologacao_produto,
    )

    assert dados_historicos.empresa == ""
    assert dados_historicos.marca == ""
    assert dados_historicos.fabricante == ""
    assert dados_historicos.perfil_responsavel == ""
    assert dados_historicos.nome_instituicao == ""


def test_copiar_dados_historicos(homologacao_produto, user):
    log_original = criar_log(homologacao_produto, user)
    dados_originais = ServicoDadosHistoricosProduto.registrar(
        log_original,
        homologacao_produto,
    )
    log_copia = criar_log(homologacao_produto, user)

    dados_copia = ServicoDadosHistoricosProduto.copiar(
        log_original,
        log_copia,
    )

    assert dados_copia is not None
    assert dados_copia.pk != dados_originais.pk
    assert dados_copia.log == log_copia
    assert str(dados_copia.produto_uuid) == str(dados_originais.produto_uuid)
    assert dados_copia.empresa == dados_originais.empresa
    assert dados_copia.criado_em_produto == dados_originais.criado_em_produto
    assert dados_copia.nome_produto == dados_originais.nome_produto
    assert dados_copia.marca == dados_originais.marca
    assert dados_copia.fabricante == dados_originais.fabricante
    assert (
        dados_copia.eh_para_alunos_com_dieta
        == dados_originais.eh_para_alunos_com_dieta
    )
    assert dados_copia.componentes == dados_originais.componentes
    assert dados_copia.perfil_responsavel == dados_originais.perfil_responsavel
    assert dados_copia.nome_instituicao == dados_originais.nome_instituicao


def test_copiar_log_sem_dados_historicos(homologacao_produto, user):
    log_original = criar_log(homologacao_produto, user)
    log_copia = criar_log(homologacao_produto, user)

    dados_copia = ServicoDadosHistoricosProduto.copiar(
        log_original,
        log_copia,
    )

    assert dados_copia is None
    assert not DadosHistoricosProduto.objects.filter(log=log_copia).exists()


def test_log_de_homologacao_cria_dados_historicos(homologacao_produto, user):
    log = homologacao_produto.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        usuario=user,
    )

    assert str(log.dados_produto.produto_uuid) == str(
        homologacao_produto.produto.uuid
    )
    assert log.dados_produto.nome_produto == homologacao_produto.produto.nome


def test_log_de_reclamacao_cria_dados_historicos(reclamacao, user):
    log = reclamacao.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
        user=user,
    )

    assert log.solicitacao_tipo == LogSolicitacoesUsuario.RECLAMACAO_PRODUTO
    assert str(log.dados_produto.produto_uuid) == str(
        reclamacao.homologacao_produto.produto.uuid
    )
    assert log.dados_produto.nome_produto == (
        reclamacao.homologacao_produto.produto.nome
    )


def test_copia_de_homologacao_preserva_dados_historicos(
    homologacao_produto,
    terceirizada,
    user,
):
    log_original = homologacao_produto.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        usuario=user,
    )

    homologacao_copia = homologacao_produto.cria_copia(terceirizada)
    log_copia = homologacao_copia.logs.get(
        status_evento=LogSolicitacoesUsuario.INICIO_FLUXO
    )

    assert str(log_copia.dados_produto.produto_uuid) == str(
        log_original.dados_produto.produto_uuid
    )
    assert log_copia.dados_produto.nome_produto == (
        log_original.dados_produto.nome_produto
    )
    assert log_copia.dados_produto.componentes == (
        log_original.dados_produto.componentes
    )
    assert log_copia.dados_produto.pk != log_original.dados_produto.pk


def test_copia_de_log_da_reclamacao_preserva_dados_historicos(
    reclamacao,
    user,
):
    log_original = reclamacao.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
        user=user,
    )
    reclamacao_copia = baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=reclamacao.homologacao_produto,
        escola=reclamacao.escola,
        criado_por=user,
    )

    log_copia = HomologacaoProduto._criar_log_copia(
        log_original,
        reclamacao_copia,
    )

    assert str(log_copia.dados_produto.produto_uuid) == str(
        log_original.dados_produto.produto_uuid
    )
    assert log_copia.dados_produto.nome_produto == (
        log_original.dados_produto.nome_produto
    )
    assert log_copia.dados_produto.componentes == (
        log_original.dados_produto.componentes
    )
    assert log_copia.dados_produto.pk != log_original.dados_produto.pk
