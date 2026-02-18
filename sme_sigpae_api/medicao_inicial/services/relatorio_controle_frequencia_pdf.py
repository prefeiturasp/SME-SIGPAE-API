import datetime
import io
from calendar import monthrange

from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.loader import render_to_string
from PyPDF4 import PdfFileReader, PdfFileWriter
from weasyprint import HTML

from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.escola.utils import (
    formata_periodos_pdf_controle_frequencia,
    trata_filtro_data_relatorio_controle_frequencia_pdf,
)
from sme_sigpae_api.medicao_inicial.utils import (
    get_data_relatorio,
    get_pdf_merge_cabecalho,
    get_queryset_filtrado,
    queryset_alunos_matriculados,
)


def gera_relatorio_controle_frequencia_pdf(query_params, escola_uuid):
    from sme_sigpae_api.escola.api.viewsets import RelatorioControleDeFrequenciaViewSet

    vs_relatorio_controle = RelatorioControleDeFrequenciaViewSet()
    escola = Escola.objects.get(uuid=escola_uuid)
    mes_ano = query_params.get("mes_ano")
    mes, ano = mes_ano.split("_")
    data_referencia = datetime.date(int(ano), int(mes), 1)
    qs = queryset_alunos_matriculados(escola, data_referencia)
    queryset = qs.filter(escola=escola)
    periodos_uuids = query_params.get("periodos")
    escola_eh_cei_ou_cemei = escola.eh_cei_data(
        data_referencia
    ) or escola.eh_cemei_data(data_referencia)

    filtros = {}

    _, num_dias = monthrange(
        int(ano),
        int(mes),
    )
    mes_seguinte = trata_filtro_data_relatorio_controle_frequencia_pdf(
        filtros, query_params, ano, mes, num_dias
    )

    queryset = get_queryset_filtrado(
        vs_relatorio_controle, queryset, filtros, periodos_uuids
    )

    qtd_matriculados = vs_relatorio_controle.filtrar_alunos_matriculados(
        queryset, escola_eh_cei_ou_cemei, periodos_uuids
    )
    total_matriculados = qtd_matriculados["total_matriculados"]

    periodos = formata_periodos_pdf_controle_frequencia(
        qtd_matriculados, queryset, query_params, escola, mes_seguinte
    )

    data_relatorio = get_data_relatorio(query_params)
    mes_ano_formatado = f"{converte_numero_em_mes(int(mes))}/{ano}"

    dias_do_mes = []
    dia = 1
    if query_params.get("data_inicial"):
        _, _, dia_inicial = query_params.get("data_inicial").split("-")
        dia = int(dia_inicial)
        num_dias = 1
    if query_params.get("data_final"):
        _, _, dia_final = query_params.get("data_final").split("-")
        num_dias = int(dia_final)
    if num_dias == 1:
        dias_do_mes.append(f"{dia:02d}")
    else:
        while dia <= num_dias:
            dias_do_mes.append(f"{dia:02d}")
            dia += 1

    matriculados_data_str = f"em {data_relatorio}"

    if (
        query_params.get("data_inicial")
        and query_params.get("data_final")
        and query_params.get("data_inicial") != query_params.get("data_final")
    ):
        _, _, dia_inicial = query_params.get("data_inicial").split("-")
        _, _, dia_final = query_params.get("data_final").split("-")
        matriculados_data_str = f"entre {int(dia_inicial):02d}/{int(mes):02d}/{ano} e {int(dia_final):02d}/{int(mes):02d}/{ano}"

    html_string = render_to_string(
        "relatorio_controle_frequencia.html",
        {
            "filtros": filtros,
            "data_relatorio": data_relatorio,
            "total_matriculados": total_matriculados,
            "periodos": periodos,
            "mes_ano_formatado": mes_ano_formatado,
            "dias_do_mes": dias_do_mes,
            "matriculados_data_str": matriculados_data_str,
            "escola_nome": escola.nome,
            "mes_ano": query_params.get("mes_ano"),
        },
    )

    html_string_cabecalho_relatorio_controle_frequencia = render_to_string(
        "cabecalho_relatorio_controle_frequencia.html",
        {
            "escola_nome": escola.nome,
            "data_relatorio": data_relatorio,
        },
    )

    html_pdf_cabecalho_relatorio_controle_frequencia = HTML(
        string=html_string_cabecalho_relatorio_controle_frequencia,
        base_url=staticfiles_storage.location,
    ).write_pdf()
    html_pdf_relatorio_controle_frequencia = HTML(
        string=html_string, base_url=staticfiles_storage.location
    ).write_pdf()

    arquivo_final = io.BytesIO()
    pdf_cabecalho_relatorio_controle_frequencia = PdfFileReader(
        io.BytesIO(html_pdf_cabecalho_relatorio_controle_frequencia), strict=False
    )
    pdf_relatorio_controle_frequencia = PdfFileReader(
        io.BytesIO(html_pdf_relatorio_controle_frequencia), strict=False
    )
    pdf_writer = PdfFileWriter()

    pdf_writer = get_pdf_merge_cabecalho(
        pdf_relatorio_controle_frequencia,
        pdf_cabecalho_relatorio_controle_frequencia,
        pdf_writer,
    )
    pdf_writer.write(arquivo_final)
    arquivo_final.seek(0)

    return arquivo_final.read()
