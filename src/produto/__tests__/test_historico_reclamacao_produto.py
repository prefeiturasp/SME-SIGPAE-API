import io
import zipfile
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker

from src.dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_UE,
)
from src.dados_comuns.models import (
    AnexoLogSolicitacoesUsuario,
    LogSolicitacoesUsuario,
)
from src.produto.api.permissions import PermissaoArquivosHistoricoReclamacao
from src.produto.models import AnexoReclamacaoDeProduto
from src.produto.services.historico_reclamacao_produto import (
    ServicoHistoricoReclamacaoProduto,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def reclamacao(user):
    terceirizada = baker.make("Terceirizada")
    homologacao = baker.make(
        "HomologacaoProduto",
        rastro_terceirizada=terceirizada,
        criado_por=user,
    )
    escola = baker.make("Escola")
    return baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=homologacao,
        escola=escola,
        reclamante_registro_funcional="1234567",
        reclamante_cargo="Nutricionista",
        reclamante_nome="Usuário de Teste",
        reclamacao="Produto em desacordo",
        criado_por=user,
    )


def criar_anexo_reclamacao(reclamacao, nome, conteudo=b"arquivo"):
    return AnexoReclamacaoDeProduto.objects.create(
        reclamacao_de_produto=reclamacao,
        nome=nome,
        arquivo=SimpleUploadedFile(nome, conteudo),
    )


def criar_log_reclamacao(reclamacao, user, status_evento):
    return baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=reclamacao.uuid,
        solicitacao_tipo=LogSolicitacoesUsuario.RECLAMACAO_PRODUTO,
        status_evento=status_evento,
        usuario=user,
    )


def criar_anexo_log(log, nome, conteudo=b"arquivo"):
    return AnexoLogSolicitacoesUsuario.objects.create(
        log=log,
        nome=nome,
        arquivo=SimpleUploadedFile(nome, conteudo),
    )


def criar_request_com_vinculo(instituicao, nome_perfil):
    request = MagicMock()
    request.user.vinculo_atual.instituicao = instituicao
    request.user.vinculo_atual.perfil.nome = nome_perfil
    return request


def test_obter_anexos_da_acao_inicial_legada(reclamacao):
    anexo = criar_anexo_reclamacao(reclamacao, "comprovante.pdf", b"%PDF-1.4")

    anexos = ServicoHistoricoReclamacaoProduto.obter_anexos_acao(
        reclamacao.uuid,
        reclamacao.uuid,
    )

    assert anexos == [anexo]


def test_obter_anexos_da_resposta_sem_misturar_acao_inicial(reclamacao, user):
    criar_anexo_reclamacao(reclamacao, "reclamacao.pdf", b"%PDF-1.4")
    log = criar_log_reclamacao(
        reclamacao,
        user,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
    )
    imagem = criar_anexo_log(log, "resposta.jpg", b"imagem-resposta")

    anexos = ServicoHistoricoReclamacaoProduto.obter_anexos_acao(
        reclamacao.uuid,
        log.uuid,
    )

    assert anexos == [imagem]


def test_acao_sem_arquivos_disponiveis_nao_expoe_anexos(reclamacao, user):
    log = criar_log_reclamacao(
        reclamacao,
        user,
        LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO,
    )
    criar_anexo_log(log, "arquivo.pdf", b"%PDF-1.4")

    anexos = ServicoHistoricoReclamacaoProduto.obter_anexos_acao(
        reclamacao.uuid,
        log.uuid,
    )

    assert anexos == []


def test_resumo_identifica_pdf_e_imagens(reclamacao):
    anexos = [
        criar_anexo_reclamacao(reclamacao, "documento.pdf", b"%PDF-1.4"),
        criar_anexo_reclamacao(reclamacao, "frente.jpg", b"imagem-frente"),
        criar_anexo_reclamacao(reclamacao, "verso.png", b"imagem-verso"),
    ]

    resumo = ServicoHistoricoReclamacaoProduto.obter_resumo_arquivos(anexos)

    assert resumo == {
        "possui_pdf": True,
        "quantidade_imagens": 2,
    }


def test_gerar_arquivo_pdf_unico_sem_compactacao(reclamacao):
    conteudo_pdf = b"%PDF-1.4 conteudo"
    criar_anexo_reclamacao(reclamacao, "documento.pdf", conteudo_pdf)

    nome, conteudo, tipo_mime = (
        ServicoHistoricoReclamacaoProduto.gerar_arquivo_pdfs(
            reclamacao.uuid,
            reclamacao.uuid,
        )
    )

    assert nome == "documento.pdf"
    assert conteudo == conteudo_pdf
    assert tipo_mime == "application/pdf"


def test_multiplos_pdfs_sao_agrupados_em_zip(reclamacao):
    criar_anexo_reclamacao(reclamacao, "documento-1.pdf", b"%PDF-1.4 primeiro")
    criar_anexo_reclamacao(reclamacao, "documento-2.pdf", b"%PDF-1.4 segundo")

    nome, conteudo, tipo_mime = (
        ServicoHistoricoReclamacaoProduto.gerar_arquivo_pdfs(
            reclamacao.uuid,
            reclamacao.uuid,
        )
    )

    assert nome == f"documentos_reclamacao_{reclamacao.uuid}.zip"
    assert tipo_mime == "application/zip"

    with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo_zip:
        assert set(arquivo_zip.namelist()) == {
            "documento-1.pdf",
            "documento-2.pdf",
        }
        assert arquivo_zip.read("documento-1.pdf") == b"%PDF-1.4 primeiro"
        assert arquivo_zip.read("documento-2.pdf") == b"%PDF-1.4 segundo"


def test_multiplas_imagens_sao_agrupadas_em_zip(reclamacao):
    criar_anexo_reclamacao(reclamacao, "frente.jpg", b"imagem-frente")
    criar_anexo_reclamacao(reclamacao, "verso.png", b"imagem-verso")

    nome, conteudo, tipo_mime = (
        ServicoHistoricoReclamacaoProduto.gerar_arquivo_imagens(
            reclamacao.uuid,
            reclamacao.uuid,
        )
    )

    assert nome == f"imagens_reclamacao_{reclamacao.uuid}.zip"
    assert tipo_mime == "application/zip"

    with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo_zip:
        assert set(arquivo_zip.namelist()) == {"frente.jpg", "verso.png"}
        assert arquivo_zip.read("frente.jpg") == b"imagem-frente"
        assert arquivo_zip.read("verso.png") == b"imagem-verso"


def test_log_de_outra_reclamacao_nao_pode_ser_consultado(reclamacao, user):
    outra_reclamacao = baker.make(
        "ReclamacaoDeProduto",
        homologacao_produto=reclamacao.homologacao_produto,
        escola=reclamacao.escola,
        criado_por=user,
    )
    log_outra_reclamacao = criar_log_reclamacao(
        outra_reclamacao,
        user,
        LogSolicitacoesUsuario.UE_RESPONDEU_RECLAMACAO,
    )

    with pytest.raises(LogSolicitacoesUsuario.DoesNotExist):
        ServicoHistoricoReclamacaoProduto.obter_anexos_acao(
            reclamacao.uuid,
            log_outra_reclamacao.uuid,
        )


def test_gestao_de_produto_pode_acessar_arquivos(reclamacao, codae):
    request = criar_request_com_vinculo(
        codae,
        ADMINISTRADOR_GESTAO_PRODUTO,
    )

    permitido = PermissaoArquivosHistoricoReclamacao().has_object_permission(
        request,
        MagicMock(),
        reclamacao,
    )

    assert permitido is True


def test_escola_nao_pode_acessar_reclamacao_de_outra_escola(reclamacao):
    outra_escola = baker.make("Escola")
    request = criar_request_com_vinculo(outra_escola, ADMINISTRADOR_UE)

    permitido = PermissaoArquivosHistoricoReclamacao().has_object_permission(
        request,
        MagicMock(),
        reclamacao,
    )

    assert permitido is False


def test_terceirizada_da_homologacao_pode_acessar_arquivos(reclamacao):
    terceirizada = reclamacao.homologacao_produto.rastro_terceirizada
    request = criar_request_com_vinculo(terceirizada, ADMINISTRADOR_EMPRESA)

    permitido = PermissaoArquivosHistoricoReclamacao().has_object_permission(
        request,
        MagicMock(),
        reclamacao,
    )

    assert permitido is True
