from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet


def cria_validacao_lista_em_sheet_oculto(
    lista: list,
    hidden_sheet: Worksheet,
    worksheet: Worksheet,
    workbook: Workbook,
    str_coluna_no_sheet_oculto: str,
    idx_coluna_no_sheet_oculto: int,
    nome_elementos: str,
    artigo: str,
    str_coluna_headers: str,
) -> Worksheet:
    for index, elemento in enumerate(lista, start=1):
        hidden_sheet.cell(row=index, column=idx_coluna_no_sheet_oculto, value=elemento)

    nome_validacao = f"ValidacaoLista{nome_elementos}s"

    validacao_lista = DefinedName(
        name=nome_validacao,
        attr_text=f"'HiddenSheet'!${str_coluna_no_sheet_oculto}$1:${str_coluna_no_sheet_oculto}${str(len(lista))}",
        hidden=True,
    )

    workbook.defined_names.add(validacao_lista)

    dv = DataValidation(type="list", formula1=nome_validacao, allow_blank=True)
    dv.error = f"{nome_elementos} Inválid{artigo}"
    dv.errorTitle = f"{nome_elementos} não permitid{artigo}"
    worksheet.add_data_validation(dv)
    dv.add(f"{str_coluna_headers}2:{str_coluna_headers}1048576")

    return worksheet
