import base64
import io
import math
from datetime import date

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django_weasyprint.utils import django_url_fetcher
from pikepdf import Pdf
from pypdf import PdfReader, PdfWriter
from weasyprint import CSS, HTML

from ..dados_comuns.models import LogSolicitacoesUsuario


def formata_logs(logs):
    _tipos = LogSolicitacoesUsuario.TIPOS_SOLICITACOES
    tipos = {v: k for (k, v) in _tipos}
    if logs and logs.first().solicitacao_tipo != tipos["Homologação de Produto"]:
        return logs
    if logs.filter(
        status_evento__in=[
            LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            LogSolicitacoesUsuario.CODAE_NEGOU,
        ]
    ).exists():
        logs = logs.exclude(status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU)
    return logs.exclude(
        status_evento=LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO
    )


def get_width(fluxo, logs):
    logs_formatado = formata_logs(logs)
    fluxo_utilizado = fluxo if len(fluxo) > len(logs_formatado) else logs_formatado
    if not fluxo_utilizado:
        return "55%"
    if len(fluxo_utilizado) == 1:
        return "100%"
    return str(math.floor(99 / len(fluxo_utilizado))) + "%"


def get_diretorias_regionais(lotes):
    diretorias_regionais = []
    for lote in lotes:
        if lote.diretoria_regional not in diretorias_regionais:
            diretorias_regionais.append(lote.diretoria_regional)
    return diretorias_regionais


def merge_pdf_com_rodape_assinatura(arquivo_usuario, string_pdf_rodape):
    arquivo_final = io.BytesIO()
    pdf_rodape_assinatura = HTML(
        string=string_pdf_rodape, base_url=staticfiles_storage.location
    ).write_pdf()

    pdf_usuario = PdfReader(arquivo_usuario)
    pdf_rodape = PdfReader(io.BytesIO(pdf_rodape_assinatura))
    pdf_writer = PdfWriter()

    total_paginas = len(pdf_usuario.pages)

    for idx in range(total_paginas):
        page = pdf_usuario.pages[idx]

        if idx == total_paginas - 1:
            page.merge_page(pdf_rodape.pages[0])

        pdf_writer.add_page(page)

    pdf_writer.write(arquivo_final)
    arquivo_final.seek(0)

    encoded_string = base64.b64encode(arquivo_final.read())
    return "data:application/pdf;base64,%s" % (encoded_string.decode("utf-8"))


def html_to_pdf_response(html_string, pdf_filename, request=None):
    pdf_file = HTML(
        string=html_string,
        url_fetcher=django_url_fetcher,
        base_url=request.build_absolute_uri("/") if request else "file://abobrinha",
    ).write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'filename="{pdf_filename}"'
    return response


def html_to_pdf_file(html_string, pdf_filename, is_async=False):
    pdf_file = HTML(
        string=html_string, base_url=staticfiles_storage.location
    ).write_pdf()

    if is_async:
        return pdf_file
    else:
        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f'filename="{pdf_filename}"'
        return response


def html_to_pdf_watermark(html_string, pdf_filename, watermark, is_async=False):
    arquivo_final = io.BytesIO()
    pdf_file = HTML(
        string=html_string, base_url=staticfiles_storage.location
    ).write_pdf()

    watermark_instance = PdfReader(
        f"sme_sigpae_api/relatorios/static/images/{watermark}", strict=False
    )
    watermark_page = watermark_instance.pages[0]
    pdf_reader = PdfReader(io.BytesIO(pdf_file), strict=False)
    pdf_writer = PdfWriter()

    for page in pdf_reader.pages:
        page.merge_page(watermark_page)
        pdf_writer.add_page(page)

    pdf_writer.write(arquivo_final)
    arquivo_final.seek(0)
    if is_async:
        return arquivo_final.read()
    else:
        response = HttpResponse(arquivo_final, content_type="application/pdf")
        response["Content-Disposition"] = f'filename="{pdf_filename}"'
        return response


def html_to_pdf_multiple(lista_strings, pdf_filename, is_async=False):
    arquivo_final = io.BytesIO()
    arquivo = Pdf.new()
    for html_string in lista_strings:
        pdf_file = HTML(
            string=html_string, base_url=staticfiles_storage.location
        ).write_pdf()
        src = Pdf.open(io.BytesIO(pdf_file))
        arquivo.pages.extend(src.pages)

    arquivo.save(arquivo_final)
    arquivo_final.seek(0)

    if is_async:
        return arquivo_final.read()
    else:
        response = HttpResponse(arquivo_final, content_type="application/pdf")
        response["Content-Disposition"] = f'filename="{pdf_filename}"'
        return response


def html_to_pdf_email_anexo(html_string, pdf_filename=None):
    # O PDF gerado aqui pode ser anexado num email.
    # Utilizado para enviar email ao cancelar dietas ativas automaticamente.
    pdf_file = HTML(
        string=html_string, url_fetcher=django_url_fetcher, base_url="file://abobrinha"
    ).write_pdf()
    return pdf_file


def merge_pdf_com_string_template(
    arquivo_pdf,
    string_template,
    somente_ultima_pagina=False,
):
    pdf_usuario = PdfReader(arquivo_pdf, strict=False)

    css_string = (
        "html, body {font-family: 'Roboto', sans-serif; margin: 0; padding: 0}\n@page {size: A4 %s; margin: 0}"
        % obter_orientacao_pdf(pdf_usuario)
    )
    stylesheets = [CSS(string=css_string)]
    html_para_mergear = HTML(
        string=string_template,
        base_url=staticfiles_storage.location,
    ).write_pdf(stylesheets=stylesheets)

    pdf_para_mergear = PdfReader(io.BytesIO(html_para_mergear))

    pdf_writer = PdfWriter()
    total_paginas = len(pdf_usuario.pages)

    for idx_pagina in range(total_paginas):
        pagina = pdf_usuario.pages[idx_pagina]

        if somente_ultima_pagina:
            if idx_pagina == total_paginas - 1:
                pagina.merge_page(pdf_para_mergear.pages[0])

        else:
            pagina.merge_page(pdf_para_mergear.pages[0])

        pdf_writer.add_page(pagina)

    arquivo_final = io.BytesIO()
    pdf_writer.write(arquivo_final)
    arquivo_final.seek(0)

    return ContentFile(arquivo_final.read())


def obter_orientacao_pdf(arquivo_pdf: PdfReader):
    page = arquivo_pdf.pages[0]

    return (
        "portrait"
        if float(page.mediabox.height) > float(page.mediabox.width)
        else "landscape"
    )


def get_config_cabecario_relatorio_analise(  # noqa C901
    filtros, data_incial_analise_padrao, contatos_terceirizada
):
    tipos_cabecario = (
        "CABECARIO_POR_DATA",
        "CABECARIO_POR_NOME_TERCEIRIZADA",
        "CABECARIO_REDUZIDO",
        "CABECARIO_POR_NOME",
    )

    config = {
        "cabecario_tipo": None,
        "nome_busca": None,
        "nome_terceirizada": None,
        "email_terceirizada": None,
        "telefone_terceirizada": None,
        "data_analise_inicial": None,
        "data_analise_final": None,
    }

    if len(filtros) > 2 or len(filtros) == 0:
        config["cabecario_tipo"] = tipos_cabecario[2]

    if len(filtros) == 1:
        if "nome_produto" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[3]
            config["nome_busca"] = filtros.get("nome_produto")

        if "nome_fabricante" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[3]
            config["nome_busca"] = filtros.get("nome_fabricante")

        if "nome_marca" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[3]
            config["nome_busca"] = filtros.get("nome_marca")

        if "nome_terceirizada" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[1]
            config["nome_terceirizada"] = filtros.get("nome_terceirizada")
            config["email_terceirizada"] = contatos_terceirizada[0]["email"]
            config["telefone_terceirizada"] = contatos_terceirizada[0]["telefone"]

        if "data_analise_inicial" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[0]
            config["data_analise_inicial"] = filtros.get("data_analise_inicial")
            config["data_analise_final"] = date.today().strftime("%d/%m/%Y")

        if "data_analise_final" in filtros:
            config["cabecario_tipo"] = tipos_cabecario[0]
            config["data_analise_inicial"] = data_incial_analise_padrao
            config["data_analise_final"] = filtros.get("data_analise_final")

    elif "data_analise_inicial" in filtros and "data_analise_final" in filtros:
        config["cabecario_tipo"] = tipos_cabecario[0]
        config["data_analise_inicial"] = filtros.get("data_analise_inicial")
        config["data_analise_final"] = filtros.get("data_analise_final")

    else:
        config["cabecario_tipo"] = tipos_cabecario[2]

    return config


def conta_filtros(filtros):
    qtde_filtros = 0
    filtros.pop("status", [])
    for valor in filtros.values():
        if valor:
            qtde_filtros += 1
    return qtde_filtros


def get_ultima_justificativa_analise_sensorial(produto):
    justificativa = None
    ultimo_log = produto.ultima_homologacao.ultimo_log
    if ultimo_log.status_evento_explicacao == "CODAE pediu análise sensorial":
        justificativa = ultimo_log.justificativa
    return justificativa


def formata_motivos_inclusao(motivos_inclusao):
    motivos_formatados = []
    motivos = list(set(motivos_inclusao.values_list("motivo__nome", flat=True)))
    for motivo in motivos:
        datas = []
        for motivo_inclusao in motivos_inclusao:
            if motivo_inclusao.motivo.nome == motivo:
                datas.append(motivo_inclusao.data.strftime("%d/%m/%Y"))
        motivos_formatados.append(
            {
                "nome": motivo,
                "datas": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(
                    datas
                ),
                "descricao_evento": motivo_inclusao.descricao_evento,
            }
        )
    return motivos_formatados


def formata_logs_kit_lanche_unificado_cancelado_por_usuario_escola(
    solicitacao, uuid_log_temporario, logs
):
    logs_formatado = logs
    logs_escola_cancelou = solicitacao.logs.filter(
        status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU
    )
    log_outra_escola = logs_escola_cancelou.exclude(uuid=uuid_log_temporario)
    if log_outra_escola:
        logs_formatado = solicitacao.logs.exclude(uuid=log_outra_escola.first().uuid)
    log_dre_cancelou = solicitacao.logs.filter(
        status_evento=LogSolicitacoesUsuario.DRE_CANCELOU
    )
    if log_dre_cancelou:
        logs_formatado = solicitacao.logs.exclude(uuid=log_dre_cancelou.first().uuid)
    return logs_formatado


def formata_logs_kit_lanche_unificado_cancelado_por_usuario_dre(
    solicitacao, uuid_log_temporario, logs
):
    logs_formatado = logs
    logs_dre_cancelou = solicitacao.logs.filter(
        status_evento=LogSolicitacoesUsuario.DRE_CANCELOU
    )
    log_para_excluir = logs_dre_cancelou.exclude(uuid=uuid_log_temporario)
    if log_para_excluir:
        logs_formatado = solicitacao.logs.exclude(uuid=log_para_excluir.first().uuid)
    return logs_formatado


def formata_justificativas_usuario_dre_codae(solicitacao):
    justificativas_formatadas = []
    array_horarios_cancelados = []
    [
        array_horarios_cancelados.append(
            escola_quantidade.cancelado_em.replace(microsecond=0)
        )
        for escola_quantidade in solicitacao.escolas_quantidades.filter(cancelado=True)
    ]
    unique_array_horarios_cancelados = list(set(array_horarios_cancelados))
    unique_array_horarios_cancelados.sort(reverse=True)
    for date_time in unique_array_horarios_cancelados:
        unidades = []
        for escola_quantidade in solicitacao.escolas_quantidades.filter(
            cancelado=True,
            cancelado_em__year=date_time.year,
            cancelado_em__month=date_time.month,
            cancelado_em__day=date_time.day,
            cancelado_em__hour=date_time.hour,
            cancelado_em__minute=date_time.minute,
            cancelado_em__second__gt=date_time.second,
            cancelado_em__second__lt=date_time.second + 1,
        ):
            unidades.append(escola_quantidade.escola.nome)
            cancelado_em = escola_quantidade.cancelado_em
            justificativa = escola_quantidade.cancelado_justificativa
            tipo_usuario = escola_quantidade.cancelado_por.tipo_usuario
            nome_dre = escola_quantidade.escola.diretoria_regional.nome
            cancelado_por = escola_quantidade.cancelado_por.nome
        justificativas_formatadas.append(
            {
                "unidades": unidades,
                "cancelado_em": cancelado_em,
                "justificativa": justificativa,
                "tipo_usuario": tipo_usuario,
                "nome_dre": nome_dre,
                "cancelado_por": cancelado_por,
            }
        )
    return justificativas_formatadas


def deleta_log_temporario_se_necessario(
    log_temporario, solicitacao, uuid_log_temporario
):
    if log_temporario:
        solicitacao.logs.get(uuid=uuid_log_temporario).delete()


def todas_escolas_sol_kit_lanche_unificado_cancelado(solicitacao):
    return not solicitacao.escolas_quantidades.filter(cancelado=False).exists()


def extrair_texto_de_pdf(conteudo: bytes) -> str:
    """
    Extrai o texto de um PDF a partir de uma resposta HTTP.
    Remove quebras de linha desnecessárias e trata a codificação.
    """
    pdf_reader = PdfReader(io.BytesIO(conteudo))
    texto = ""
    for page_num in range(len(pdf_reader.pages)):
        texto_bruto = pdf_reader.get_page(page_num).extract_text()
        texto_codificado = texto_bruto.encode().decode("utf-8", errors="ignore")
        texto += texto_codificado.replace("\n\n", "").replace("\n", " ")
    return texto


class PDFMergeService:
    def __init__(self):
        self.writer = PdfWriter(strict=False)

    def append_pdf(self, file):
        self.writer.append(io.BytesIO(file))

    def merge_pdfs(self):
        output_final = io.BytesIO()
        self.writer.write(output_final)
        output_final.seek(0)

        self.writer.close()

        return output_final.getvalue()
