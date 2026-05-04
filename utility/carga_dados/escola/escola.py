from unicodedata import normalize

import pandas as pd

from src.escola.models import (
    DiretoriaRegional,
    Escola,
    TipoGestao,
    TipoUnidadeEscolar,
)

caminho_excel = "/home/amcom/Documents/planilhas_de_carga/escola_dre_codae.xlsx"

arquivo_excel = pd.ExcelFile(caminho_excel)

ESC_SHEET_NAME = ("EMPRESAS",)


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


def busca_escola_dre_codae(planilhas):
    escolas = []
    for planilha in planilhas:
        escolas.extend(obtem_objetos(planilha))
    return escolas


def normaliza_nome(nome):
    nome = normalize("NFKD", nome).encode("ASCII", "ignore").decode("ASCII")
    return nome


def retira_espacos_entre_strings(palavra):
    sem_espaco = " "
    if "/" in palavra:
        for iteravel in palavra:
            if iteravel != " ":
                sem_espaco += iteravel
            else:
                pass
    else:
        for iteravel in palavra:
            sem_espaco += iteravel
    return sem_espaco


def busca_caso_sigla(sigla):  # noqa: C901
    if sigla == " CS":
        return 1
    elif sigla == " FO":
        return 2
    elif sigla == " G":
        return 3
    elif sigla == " IP I":
        return 4
    elif sigla == " IP II":
        return 5
    elif sigla == " IQ":
        return 6
    elif sigla == " JT":
        return 7
    elif sigla == " MP I" or sigla == " MP":
        return 8
    elif sigla == " MP II":
        return 9
    elif sigla == " PE I":
        return 10
    elif sigla == " PE II":
        return 11
    elif sigla == " SM I":
        return 12
    elif sigla == " SM II":
        return 13
    elif sigla == " SAM":
        # Santo Amaro > Não tem escola associada a esse lote OBS: "SAM" eh nao existe
        return 14
    elif sigla == " PIR":
        # Pirituba > Não tem escola associada a esse lote OBS: "PIR" eh nao existe
        return 15
    elif sigla == " BTT":
        # Butanta > Não tem escola associada a esse lote OBS: "BTT" eh nao existe
        return 16
    elif sigla == " CL I":
        return 17
    elif sigla == " CL II":
        return 18


def obtem_objetos(planilha):
    lista_objetos = []
    for index in planilha.index:
        nome_dre = normaliza_nome(planilha["DRE"][index])
        nome_dre = retira_espacos_entre_strings(nome_dre)

        sigla_lote = retira_espacos_entre_strings(planilha["SIGLA/LOTE"][index])

        lote_id = busca_caso_sigla(sigla_lote)

        objeto = {
            "eol": str(planilha["EOL"][index]),
            "codae": str(planilha["COD. CODAE"][index]),
            "nome": planilha["NOME"][index],
            "dre": nome_dre,
            "lote_id": lote_id,
            "unidade": str(planilha["TIPO DE U.E"][index]),
            "gestao": "TERCEIRIZADA",
        }
        lista_objetos.append(objeto)
    return lista_objetos


def cria_e_busca_objeto_gestao(tipo_gestao):
    try:
        gestao = TipoGestao.objects.get(nome=tipo_gestao)
    except:  # noqa: E722
        tp_gestao = TipoGestao(nome=tipo_gestao)
        gestao = tp_gestao.save()
    return gestao


def cria_e_busca_objeto_unidade_escolar(tipo_unidade):
    tp_unidade = TipoUnidadeEscolar(iniciais=tipo_unidade)
    unidade = tp_unidade.save()

    return unidade


def busca_relacionamento_dre(nome_obj):
    try:
        dre = DiretoriaRegional.objects.get(nome=nome_obj).id
    except DiretoriaRegional.DoesNotExist:
        dre = None
    return dre


def normaliza_codigo_eol(cod_eol):
    for i in range(6 - len(cod_eol)):
        cod_eol = "0" + cod_eol
    return cod_eol


def monta_salva_objeto(escolas):
    for escola in escolas:
        tipo_gestao = cria_e_busca_objeto_gestao(escola["gestao"])
        tipo_unidade = cria_e_busca_objeto_unidade_escolar(escola["unidade"])
        id_dre = busca_relacionamento_dre(escola["dre"])
        codae = str(escola["codae"]).split(".")[0]
        eol = normaliza_codigo_eol(escola["eol"])
        esc = Escola(
            nome=escola["nome"],
            codigo_eol=eol,
            codigo_codae=codae,
            diretoria_regional_id=id_dre,
            lote_id=escola["lote_id"],
            tipo_gestao=tipo_gestao,
            tipo_unidade=tipo_unidade,
        )
        esc.save()
    return None


nomes_sheet = busca_nome_sheet_planilha(arquivo_excel, ESC_SHEET_NAME)

planilhas = busca_planilhas_do_excel(nomes_sheet)

objetos_da_planilha = busca_escola_dre_codae(planilhas)

monta_salva_objeto(objetos_da_planilha)
