from unicodedata import normalize

import pandas as pd

from src.escola.models import DiretoriaRegional, Lote

caminho_excel = "/home/amcom/Documentos/docs PO alimentacao/lista de lotes.xlsx"

arquivo_excel = pd.ExcelFile(caminho_excel)

# a sheet que voce não deseja ler, voce pode incluir na constante ESC_SHEET_NAME.
ESC_SHEET_NAME = ()


def busca_nome_sheet_planilha(arquivo_excel, ESC_SHEET_NAME):
    nomes = (
        sheet_name
        for sheet_name in arquivo_excel.sheet_names
        if sheet_name not in ESC_SHEET_NAME
    )
    return nomes


def busca_planilhas_do_excel(nomes_sheet):
    planilhas = []
    for nome in nomes_sheet:
        planilhas.append(pd.read_excel(caminho_excel, sheet_name=nome))
    return planilhas


def normaliza_nome(nome):
    nome_dre = normalize("NFKD", nome).encode("ASCII", "ignore").decode("ASCII")
    return nome_dre


def busca_dados_relacionamento(nome):
    nome = " " + nome
    dre = DiretoriaRegional.objects.get(nome=nome)
    return dre


def obtem_objetos(planilha):
    lista_objetos = []
    for index in planilha.index:
        nome = normaliza_nome(planilha["LOTES"][index].upper())
        dre = busca_dados_relacionamento(planilha["DRE"][index])
        objeto = {"nome": nome, "dre_id": dre}
        lista_objetos.append(objeto)
    return lista_objetos


def busca_lotes(planilhas):
    lotes = []
    for planilha in planilhas:
        lotes.extend(obtem_objetos(planilha))
    return lotes


def monta_salva_objeto(lotes):
    for lote in lotes:
        lt = Lote(nome=lote["nome"], diretoria_regional=lote["dre_id"])
        lt.save()
    return None


nomes_sheet = busca_nome_sheet_planilha(arquivo_excel, ESC_SHEET_NAME)

planilhas = busca_planilhas_do_excel(nomes_sheet)

objetos_da_planilha = busca_lotes(planilhas)

monta_salva_objeto(objetos_da_planilha)
