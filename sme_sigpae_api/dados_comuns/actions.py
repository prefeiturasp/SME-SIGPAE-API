from datetime import date, datetime

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from unidecode import unidecode

from .utils import ExportExcelAction


def style_output_file(file):
    black_font = Font(color="000000", bold=True)
    for cell in file["1:1"]:
        cell.font = black_font

    for column_cells in file.columns:
        length = max(len((cell.value)) for cell in column_cells)
        length += 10
        file.column_dimensions[column_cells[0].column_letter].width = length

    return file


def convert_data_date(value):
    return value.strftime("%d/%m/%Y, %H:%M:%S")


def convert_boolean_field(value):
    if value:
        return "Sim"
    return "Não"


def _format_export_value(self, obj, field):
    is_admin_field = hasattr(self, field)
    if is_admin_field:
        return getattr(self, field)(obj)

    value = getattr(obj, field)
    if isinstance(value, (datetime, date)):
        return convert_data_date(value)
    if isinstance(value, bool):
        return convert_boolean_field(value)
    if value is None:
        return "-"

    return value


def export_as_xls(self, request, queryset, field_names):
    opts = self.model._meta
    field_names = field_names if field_names else self.list_display
    file_name = unidecode(opts.verbose_name)

    wb = Workbook()
    ws = wb.active
    ws.append(ExportExcelAction.generate_header(self, self.model, field_names))

    for obj in queryset:
        row = [str(self._format_export_value(obj, field)) for field in field_names]
        ws.append(row)

    ws = style_output_file(ws)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename={file_name}.xlsx"
    wb.save(response)
    return response


export_as_xls.short_description = "Exportar para excel"
