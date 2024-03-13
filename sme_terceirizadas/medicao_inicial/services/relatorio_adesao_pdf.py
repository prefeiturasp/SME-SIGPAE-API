from datetime import datetime

from django.template.loader import render_to_string

from sme_terceirizadas.dados_comuns.utils import converte_numero_em_mes
from sme_terceirizadas.escola.models import DiretoriaRegional, Escola, Lote
from sme_terceirizadas.relatorios.utils import html_to_pdf_file


def _formata_filtros(query_params: dict):
    mes, ano = query_params.get("mes_ano").split("_")
    filtros = f"{converte_numero_em_mes(int(mes))} - {ano}"

    dre_uuid = query_params.get("diretoria_regional")
    if dre_uuid:
        dre = DiretoriaRegional.objects.filter(uuid=dre_uuid).first()
        filtros += f" | {dre.nome}"

    lotes_uuid = query_params.get("lotes")
    if lotes_uuid:
        lotes = Lote.objects.filter(uuid__in=lotes_uuid).values_list("nome", flat=True)
        filtros += f" | {', '.join(lotes)}"

    escola_codigo_eol = query_params.get("escola")
    if escola_codigo_eol:
        escola_codigo_eol, *_ = escola_codigo_eol.split("-")
        escola = Escola.objects.filter(codigo_eol=escola_codigo_eol.strip()).first()
        filtros += f" | {escola.nome}"

    return filtros


def gera_relatorio_adesao_pdf(resultados, query_params):
    # colunas = [
    #     "Tipo de Alimentação",
    #     "Total de Alimentações Servidas",
    #     "Número Total de Frequência",
    #     "% de Adesão",
    # ]

    filtros = _formata_filtros(query_params)
    data_relatorio = datetime.now().date().strftime("%d/%m/%Y")

    html_string = render_to_string(
        "relatorio_adesao.html",
        {
            "filtros": filtros,
            "data_relatorio": data_relatorio,
        },
    )

    return html_to_pdf_file(html_string, "relatorio_adesao.pdf", False)
