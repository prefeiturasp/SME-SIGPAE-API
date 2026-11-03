import logging
from io import BytesIO
from pathlib import Path
from shutil import copy2, copytree
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.staticfiles import finders
from django.core.files.storage import FileSystemStorage
from freezegun import freeze_time
from model_bakery import baker
from pypdf import PdfReader, PdfWriter
from sass_processor.processor import SassProcessor

from src.dados_comuns.models import CentralDeDownload
from src.dieta_especial.tasks import gerar_pdf_protocolo_padrao_async

pytestmark = pytest.mark.django_db

CAMINHO_TASK = "src.dieta_especial.tasks.relatorio_protocolo_padrao_pdf"
NOME_ARQUIVO = "relatorio_protocolo_padrao.pdf"


@pytest.fixture(autouse=True)
def armazenamento_download_temporario(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "media")


@pytest.fixture
def estaticos_pdf_temporarios(settings, tmp_path, monkeypatch):
    estaticos = tmp_path / "static"
    imagens = estaticos / "images"
    imagens.mkdir(parents=True)
    settings.STATIC_ROOT = str(estaticos)
    settings.STATIC_URL = str(estaticos) + "/"
    monkeypatch.setattr(
        SassProcessor,
        "source_storage",
        FileSystemStorage(
            location=str(estaticos), base_url=settings.STATIC_URL
        ),
    )
    copy2(
        finders.find("images/LOGO_FUNDO_CLARO.png"),
        imagens / "LOGO_FUNDO_CLARO.png",
    )
    fontes = Path(finders.find("fonts/Roboto/Roboto-Regular.ttf")).parent
    copytree(fontes, estaticos / "fonts" / "Roboto")


@pytest.fixture
def dependencias_pdf_protocolo():
    destino = BytesIO()
    documento = PdfWriter()
    documento.add_blank_page(width=595, height=842)
    documento.write(destino)
    with (
        patch(
            f"{CAMINHO_TASK}.preparar_dados_protocolo_padrao",
            return_value={"nome_protocolo": "PROTOCOLO DE TESTE"},
        ) as preparar,
        patch(
            f"{CAMINHO_TASK}.render_to_string",
            return_value="<html><body>PROTOCOLO DE TESTE</body></html>",
        ) as renderizar,
        patch(
            f"{CAMINHO_TASK}.html_to_pdf_file",
            return_value=destino.getvalue(),
        ) as converter,
    ):
        yield {
            "preparar": preparar,
            "renderizar": renderizar,
            "converter": converter,
        }


def ler_paginas_pdf(usuario):
    download = CentralDeDownload.objects.get(usuario=usuario)
    assert download.status == CentralDeDownload.STATUS_CONCLUIDO, (
        download.msg_erro
    )
    assert download.identificador == NOME_ARQUIVO
    with download.arquivo.open("rb") as arquivo:
        documento = PdfReader(arquivo)
        return [
            " ".join(pagina.extract_text().split())
            for pagina in documento.pages
        ]


def test_task_pdf_protocolo_padrao_salva_na_central_do_solicitante(
    usuario_admin,
    protocolo_padrao_dieta_especial,
    dependencias_pdf_protocolo,
    caplog,
):
    caplog.set_level(logging.INFO, logger=CAMINHO_TASK)
    protocolo = protocolo_padrao_dieta_especial

    gerar_pdf_protocolo_padrao_async.run(
        user=usuario_admin.username,
        nome_arquivo=NOME_ARQUIVO,
        params={"protocolo_uuid": str(protocolo.uuid)},
    )

    download = CentralDeDownload.objects.get(usuario=usuario_admin)
    assert download.status == CentralDeDownload.STATUS_CONCLUIDO
    assert download.identificador == NOME_ARQUIVO
    assert download.msg_erro == ""
    assert download.arquivo.name.endswith(NOME_ARQUIVO)
    with download.arquivo.open("rb") as arquivo:
        assert arquivo.read() == (
            dependencias_pdf_protocolo["converter"].return_value
        )
    dependencias_pdf_protocolo["preparar"].assert_called_once_with(protocolo)
    dependencias_pdf_protocolo["renderizar"].assert_called_once_with(
        "protocolo_padrao_dieta_especial.html",
        dependencias_pdf_protocolo["preparar"].return_value,
    )
    dependencias_pdf_protocolo["converter"].assert_called_once_with(
        dependencias_pdf_protocolo["renderizar"].return_value,
        NOME_ARQUIVO,
        is_async=True,
    )
    assert "Iniciando a geração do arquivo" in caplog.text
    assert "Encerrada a geração do arquivo" in caplog.text


@pytest.mark.parametrize("etapa", ["preparar", "renderizar", "converter"])
def test_task_pdf_protocolo_padrao_registra_falha_na_geracao(
    usuario_admin,
    protocolo_padrao_dieta_especial,
    dependencias_pdf_protocolo,
    caplog,
    etapa,
):
    caplog.set_level(logging.INFO, logger=CAMINHO_TASK)
    mensagem = f"Falha na etapa {etapa}"
    dependencias_pdf_protocolo[etapa].side_effect = ValueError(mensagem)

    gerar_pdf_protocolo_padrao_async.run(
        user=usuario_admin.username,
        nome_arquivo=NOME_ARQUIVO,
        params={
            "protocolo_uuid": str(protocolo_padrao_dieta_especial.uuid)
        },
    )

    download = CentralDeDownload.objects.get(usuario=usuario_admin)
    assert download.status == CentralDeDownload.STATUS_ERRO
    assert download.msg_erro == mensagem
    assert not download.arquivo
    assert any(
        registro.levelno == logging.ERROR and registro.exc_info
        for registro in caplog.records
    )
    assert "Encerrada a geração do arquivo" in caplog.text


def test_task_pdf_protocolo_padrao_registra_falha_ao_salvar_arquivo(
    usuario_admin,
    protocolo_padrao_dieta_especial,
    dependencias_pdf_protocolo,
):
    with patch(
        f"{CAMINHO_TASK}.atualiza_central_download",
        side_effect=OSError("Falha ao salvar o PDF"),
    ):
        gerar_pdf_protocolo_padrao_async.run(
            user=usuario_admin.username,
            nome_arquivo=NOME_ARQUIVO,
            params={
                "protocolo_uuid": str(protocolo_padrao_dieta_especial.uuid)
            },
        )

    download = CentralDeDownload.objects.get(usuario=usuario_admin)
    assert download.status == CentralDeDownload.STATUS_ERRO
    assert download.msg_erro == "Falha ao salvar o PDF"
    assert not download.arquivo


@pytest.mark.parametrize("situacao", ["inexistente", "inativo"])
def test_task_pdf_protocolo_padrao_recusa_protocolo_indisponivel(
    usuario_admin,
    protocolo_padrao_dieta_especial,
    dependencias_pdf_protocolo,
    situacao,
):
    protocolo = protocolo_padrao_dieta_especial
    identificador = str(uuid4())
    if situacao == "inativo":
        protocolo.ativo = False
        protocolo.save(update_fields=["ativo"])
        identificador = str(protocolo.uuid)

    gerar_pdf_protocolo_padrao_async.run(
        user=usuario_admin.username,
        nome_arquivo=NOME_ARQUIVO,
        params={"protocolo_uuid": identificador},
    )

    download = CentralDeDownload.objects.get(usuario=usuario_admin)
    assert download.status == CentralDeDownload.STATUS_ERRO
    assert download.msg_erro
    assert not download.arquivo
    dependencias_pdf_protocolo["preparar"].assert_not_called()
    dependencias_pdf_protocolo["converter"].assert_not_called()


@freeze_time("2026-10-22 16:21:00")
def test_pdf_protocolo_padrao_contem_dados_editais_e_rodape(
    usuario_admin,
    protocolo_padrao_para_pdf,
    estaticos_pdf_temporarios,
):
    outro_protocolo = baker.make(
        "ProtocoloPadraoDietaEspecial",
        nome_protocolo="PROTOCOLO NÃO SELECIONADO",
    )
    gerar_pdf_protocolo_padrao_async.run(
        user=usuario_admin.username,
        nome_arquivo=NOME_ARQUIVO,
        params={"protocolo_uuid": str(protocolo_padrao_para_pdf.uuid)},
    )

    paginas = ler_paginas_pdf(usuario_admin)
    conteudo = " ".join(paginas)
    for texto in (
        "SISTEMA GESTÃO DO PROGRAMA DE ALIMENTAÇÃO ESCOLAR",
        "PROTOCOLO PADRÃO DE DIETA ESPECIAL",
        "ALERGIA A CAMARÃO",
        "Primeira orientação do protocolo.",
        "Segunda linha da orientação.",
        "Orientação em destaque.",
        "Alimento/Ingrediente",
        "Isenção/Substituição",
        "ABACATE",
        "UVA",
        "Substituir",
        "Isento",
        "SUBSTITUTO ALIMENTAR A",
        "SUBSTITUTO ALIMENTAR B",
        "PRODUTO SUBSTITUTO CADASTRADO",
        "01/2026",
        "02/2026",
        "07/05/2026",
        "Documento gerado em 22/10/2026 às 16:21",
    ):
        assert texto in conteudo
    assert outro_protocolo.nome_protocolo not in conteudo
    assert "99/2026" not in conteudo
    assert "1/1" in paginas[0]


@pytest.mark.parametrize("cenario", ["substituicoes", "orientacoes"])
def test_pdf_protocolo_padrao_pagina_sem_perder_conteudo(
    usuario_admin,
    protocolo_padrao_para_pdf,
    estaticos_pdf_temporarios,
    cenario,
):
    protocolo = protocolo_padrao_para_pdf
    quantidade = 40
    if cenario == "orientacoes":
        quantidade = 20
        trechos = []
        for numero in range(1, 61):
            trechos.append(
                f"<p>Trecho {numero:02d} das orientações gerais. "
                "Conteúdo fictício para conferir a continuidade do texto "
                "entre páginas, mantendo todas as informações "
                "do protocolo disponíveis para leitura.</p>"
            )
        trechos.append("<p>FIM DAS ORIENTACOES.</p>")
        protocolo.orientacoes_gerais = "".join(trechos)
        protocolo.save(update_fields=["orientacoes_gerais"])

    for numero in range(1, quantidade + 1):
        alimento = baker.make(
            "dieta_especial.Alimento", nome=f"ALIMENTO LOCAL {numero:02d}"
        )
        substituto = baker.make(
            "dieta_especial.Alimento", nome=f"INGREDIENTE LOCAL {numero:02d}"
        )
        substituicao = baker.make(
            "SubstituicaoAlimentoProtocoloPadrao",
            protocolo_padrao=protocolo,
            alimento=alimento,
            tipo="S",
        )
        baker.make(
            "AlimentoSubstituto",
            substituicao_alimento_protocolo_padrao=substituicao,
            alimento=substituto,
        )

    gerar_pdf_protocolo_padrao_async.run(
        user=usuario_admin.username,
        nome_arquivo=NOME_ARQUIVO,
        params={"protocolo_uuid": str(protocolo.uuid)},
    )

    paginas = ler_paginas_pdf(usuario_admin)
    assert len(paginas) > 1
    conteudo = " ".join(paginas)
    for numero in range(1, quantidade + 1):
        assert f"ALIMENTO LOCAL {numero:02d}" in conteudo
        assert f"INGREDIENTE LOCAL {numero:02d}" in conteudo
    if cenario == "orientacoes":
        for numero in range(1, 61):
            assert f"Trecho {numero:02d} das orientações gerais." in conteudo
        assert "FIM DAS ORIENTACOES." in conteudo
        assert conteudo.index("FIM DAS ORIENTACOES.") < conteudo.index(
            "ALIMENTO LOCAL 01"
        )
    for numero, pagina in enumerate(paginas, start=1):
        assert "PROTOCOLO PADRÃO DE DIETA ESPECIAL" in pagina
        assert "Documento gerado em" in pagina
        assert f"{numero}/{len(paginas)}" in pagina
    paginas_com_tabela = [
        pagina for pagina in paginas if "ALIMENTO LOCAL" in pagina
    ]
    if cenario == "substituicoes":
        assert len(paginas_com_tabela) > 1
    for pagina in paginas_com_tabela:
        assert "Isenção/Substituição" in pagina
        assert "Alimento/Ingrediente" in pagina
