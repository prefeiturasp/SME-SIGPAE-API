from django.http import HttpResponse
from openpyxl import Workbook, styles
from openpyxl.worksheet.datavalidation import DataValidation


def exportar_planilha_importacao_tipo_gestao_escola(request, **kwargs):
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        "attachment; filename=planilha_importacao_tipo_gestao_escolas.xlsx"
    )
    workbook: Workbook = Workbook()
    ws = workbook.active
    ws.title = "UNIDADES COM TIPO DE GESTÃO"
    headers = [
        "CÓDIGO EOL",
        "CÓDIGO CODAE",
        "NOME UNIDADE",
        "TIPO",
    ]
    _font = styles.Font(name="Calibri", sz=11)
    {k: setattr(styles.DEFAULT_FONT, k, v) for k, v in _font.__dict__.items()}
    for i in range(0, len(headers)):
        cabecalho = ws.cell(row=1, column=1 + i, value=headers[i])
        cabecalho.fill = styles.PatternFill("solid", fgColor="ffff99")
        cabecalho.font = styles.Font(name="Calibri", size=11, bold=True)
        cabecalho.border = styles.Border(
            left=styles.Side(border_style="thin", color="000000"),
            right=styles.Side(border_style="thin", color="000000"),
            top=styles.Side(border_style="thin", color="000000"),
            bottom=styles.Side(border_style="thin", color="000000"),
        )
    dv = DataValidation(
        type="list",
        formula1='"PARCEIRA, DIRETA, MISTA, TERCEIRIZADA TOTAL"',
        allow_blank=True,
    )
    dv.error = "Tipo Inválido"
    dv.errorTitle = "Tipo não permitido"
    ws.add_data_validation(dv)
    dv.add("D2:H1048576")

    for colunas in ws.columns:
        unmerged_cells = list(
            filter(
                lambda cell_to_check: cell_to_check.coordinate not in ws.merged_cells,
                colunas,
            )
        )
        length = max(len(str(cell.value)) for cell in unmerged_cells)
        ws.column_dimensions[unmerged_cells[0].column_letter].width = length * 1.3
    workbook.save(response)

    return response
