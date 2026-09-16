from datetime import datetime

from django.template.loader import render_to_string

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.dados_comuns.utils import converte_numero_em_mes
from src.escola.models import DiretoriaRegional, Escola, Lote
from src.relatorios.utils import html_to_pdf_file


def _obtem_nomes_lotes(query_params: dict) -> list[str]:
    lotes_uuid = query_params.get("lotes")
    if not lotes_uuid:
        return []
    return list(Lote.objects.filter(uuid__in=lotes_uuid).values_list("nome", flat=True))


def _obtem_dre(query_params: dict):
    dre_uuid = query_params.get("diretoria_regional")
    if not dre_uuid:
        return None
    return DiretoriaRegional.objects.filter(uuid=dre_uuid).first()


def _formata_segmento_dre_lote(dre, lote_nomes: list[str]) -> str:
    if lote_nomes and dre:
        return f" | {', '.join(lote_nomes)} - DRE {dre.nome}"
    if lote_nomes:
        return f" | {', '.join(lote_nomes)}"
    if dre:
        return f" | DRE {dre.nome}"
    return ""


def _formata_segmento_escola(query_params: dict, nome_escola: str = None) -> str:
    if nome_escola:
        return f" | {nome_escola}"
    escola_codigo_eol = query_params.get("escola")
    if not escola_codigo_eol:
        return ""
    escola_codigo_eol, *_ = escola_codigo_eol.split("-")
    escola = Escola.objects.filter(codigo_eol=escola_codigo_eol.strip()).first()
    if not escola:
        return ""
    return f" | {escola.nome}"


def _formata_segmento_periodo_lancamento(query_params: dict) -> str:
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")
    if not periodo_lancamento_de or not periodo_lancamento_ate:
        return ""
    return (
        f" | PERÍODO DE LANÇAMENTO: DE {periodo_lancamento_de} "
        f"ATÉ {periodo_lancamento_ate}"
    )


def _formata_filtros(query_params: dict, nome_escola: str = None):
    mes, ano = query_params.get("mes_ano").split("_")
    filtros = f"{converte_numero_em_mes(int(mes))} {ano}"

    filtros += _formata_segmento_dre_lote(
        _obtem_dre(query_params), _obtem_nomes_lotes(query_params)
    )
    filtros += _formata_segmento_escola(query_params, nome_escola)
    filtros += _formata_segmento_periodo_lancamento(query_params)

    return filtros


def _eh_relatorio_por_escola(resultados):
    return (
        isinstance(resultados, list) and bool(resultados) and "escola" in resultados[0]
    )


def gera_relatorio_adesao_pdf(resultados, query_params):
    colunas = [
        "Tipo de Alimentação",
        "Total de Alimentações Servidas",
        "Número Total de Frequência",
        "% de Adesão",
    ]

    data_relatorio = datetime.now().date().strftime(FORMATO_DATA_BRASILEIRO)

    if _eh_relatorio_por_escola(resultados):
        escolas = []
        for resultado in resultados:
            escolas.append(
                {
                    "filtros": _formata_filtros(
                        query_params, nome_escola=resultado["escola"]["nome"]
                    ),
                    "resultados": resultado["resultados"],
                }
            )
        html_string = render_to_string(
            "relatorio_adesao_por_escola.html",
            {
                "escolas": escolas,
                "data_relatorio": data_relatorio,
                "colunas": colunas,
            },
        )
    else:
        filtros = _formata_filtros(query_params)
        html_string = render_to_string(
            "relatorio_adesao.html",
            {
                "filtros": filtros,
                "data_relatorio": data_relatorio,
                "colunas": colunas,
                "resultados": resultados,
            },
        )

    return html_to_pdf_file(html_string, "relatorio_adesao.pdf", True)
