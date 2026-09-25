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


def _nome_dre_lote(query_params: dict) -> str:
    dre = _obtem_dre(query_params)
    sigla = ""
    if dre:
        sigla = dre.iniciais or dre.nome
    lote_nomes = _obtem_nomes_lotes(query_params)
    if lote_nomes and sigla:
        return f"{', '.join(lote_nomes)} - DRE {sigla}"
    if lote_nomes:
        return ", ".join(lote_nomes)
    return sigla


def _formata_filtros_por_data(query_params: dict, tipo_unidade: str) -> str:
    mes, ano = query_params.get("mes_ano").split("_")
    partes = [f"{converte_numero_em_mes(int(mes))} {ano}"]
    lote_dre = _nome_dre_lote(query_params)
    if lote_dre:
        partes.append(lote_dre)
    partes.append(tipo_unidade)
    return " | ".join(partes)


def _formata_filtros(
    query_params: dict,
    nome_escola: str = None,
    tipo_unidade: str = None,
    data_lancamento: str = None,
):
    if tipo_unidade and data_lancamento:
        return _formata_filtros_por_data(query_params, tipo_unidade)

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


def _eh_relatorio_por_data(resultados) -> bool:
    return (
        isinstance(resultados, list)
        and bool(resultados)
        and "data" in resultados[0]
        and "tipo_unidade" in resultados[0]
        and "escola" not in resultados[0]
    )


def _paginas_por_data(resultados, query_params) -> list[dict]:
    return [
        {
            "filtros": _formata_filtros(
                query_params,
                tipo_unidade=resultado["tipo_unidade"],
                data_lancamento=resultado["data"],
            ),
            "data_lancamento": resultado["data"],
            "resultados": resultado["resultados"],
        }
        for resultado in resultados
    ]


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
    elif _eh_relatorio_por_data(resultados):
        html_string = render_to_string(
            "relatorio_adesao_por_data.html",
            {
                "paginas": _paginas_por_data(resultados, query_params),
                "data_relatorio": data_relatorio,
                "colunas": colunas,
            },
        )
    else:
        if isinstance(resultados, list):
            resultados = {}
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
