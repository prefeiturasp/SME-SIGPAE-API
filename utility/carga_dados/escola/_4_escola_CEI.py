"""
Diretoria regional:
- Campos:
    nome, descricao, codigo
"""

import time

import environ
import numpy as np
import pandas as pd

from src.dados_comuns.models import Contato
from src.escola.models import (
    DiretoriaRegional,
    Escola,
    Lote,
    TipoGestao,
    TipoUnidadeEscolar,
)
from utility.carga_dados.escola.helper import (
    bcolors,
    busca_sigla_lote,
    coloca_zero_a_esquerda,
    normaliza_nome,
    printa_pontinhos,
    somente_digitos,
)

ROOT_DIR = environ.Path(__file__) - 1

df = pd.read_excel(
    f"{ROOT_DIR}/planilhas_de_carga/escola_dre_codae.xlsx",
    converters={"EOL": str, "TELEFONE2": str, "COD. CODAE": str, "CEP": str},
    sheet_name="CEI",
)

# tira os NAN e troca por espaco vazio ''
df = df.replace(np.nan, "", regex=True)
# padroniza os dados
df["EOL"] = df["EOL"].str.strip().str.upper()
df["EOL"] = df["EOL"].apply(coloca_zero_a_esquerda)

df["TIPO DE U.E"] = df["TIPO DE U.E"].str.strip().str.upper()
df["TIPO DE U.E"] = df["TIPO DE U.E"].apply(normaliza_nome)

df["NOME"] = df["NOME"].str.strip().str.upper()

df["DRE"] = df["DRE"].str.strip().str.upper()
df["DRE"] = df["DRE"].apply(normaliza_nome)

df["SIGLA/LOTE"] = df["SIGLA/LOTE"].str.strip().str.upper()
df["E-MAIL"] = df["E-MAIL"].str.strip().str.upper()

df["ENDEREÇO"] = df["ENDEREÇO"].str.strip().str.upper()
df["ENDEREÇO"] = df["ENDEREÇO"].apply(normaliza_nome)

df["Nº"] = df["Nº"].str.strip().str.upper()

df["BAIRRO"] = df["BAIRRO"].str.strip().str.upper()
df["BAIRRO"] = df["BAIRRO"].apply(normaliza_nome)

df["CEP"] = df["CEP"].str.strip().str.upper()
df["CEP"] = df["CEP"].apply(somente_digitos)

df["TELEFONE"] = df["TELEFONE"].str.strip().str.upper()
df["TELEFONE"] = df["TELEFONE"].apply(somente_digitos)
df["TELEFONE2"] = df["TELEFONE2"].str.strip().str.upper()
df["TELEFONE2"] = df["TELEFONE2"].apply(somente_digitos)

df["EMPRESA"] = df["EMPRESA"].str.strip().str.upper()
df["COD. CODAE"] = df["COD. CODAE"].str.strip().str.upper()


def cria_tipo_unidade_escolar():
    cont = 0
    for index, row in df.iterrows():
        iniciais = row["TIPO DE U.E"]
        obj, created = TipoUnidadeEscolar.objects.get_or_create(iniciais=iniciais)
        if created:
            cont += 1
            print(f"<TipoUnidadeEscolar> {obj.iniciais} criado.")
    if cont >= 1:
        print(
            f"{bcolors.OKBLUE}Foram criados {cont} <TipoUnidadeEscolar>...{bcolors.ENDC}"
        )
    time.sleep(3)


def cria_escola():
    cont = 0
    for index, row in df.iterrows():
        dre_str = row["DRE"]
        tipo_ue_str = row["TIPO DE U.E"]
        lote_sigla_str = row["SIGLA/LOTE"]
        cod_codae = row["COD. CODAE"]
        t1 = row["TELEFONE"]
        if 8 < len(t1) > 10:
            t1 = None
        t2 = row["TELEFONE2"]
        if 8 < len(t2) > 10:
            t2 = None
        if not cod_codae:
            cod_codae = None

        dre_obj, created_dre = DiretoriaRegional.objects.get_or_create(nome=dre_str)

        tipo_ue_obj, created_ue = TipoUnidadeEscolar.objects.get_or_create(
            iniciais=tipo_ue_str
        )

        tipo_gestao = TipoGestao.objects.get(id=1)  # so tem um...

        lote_obj = Lote.objects.get(id=busca_sigla_lote(lote_sigla_str))

        contato_obj, created_contato = Contato.objects.get_or_create(
            telefone=t1, telefone2=t2, email=row["E-MAIL"], celular=""
        )

        escola_obj, created = Escola.objects.get_or_create(
            nome=f"{row['TIPO DE U.E']} {row['NOME']}",
            codigo_eol=row["EOL"],
            # codigo_codae=cod_codae,
            diretoria_regional=dre_obj,
            tipo_unidade=tipo_ue_obj,
            tipo_gestao=tipo_gestao,
            lote=lote_obj,
            contato=contato_obj,
        )

        if created:
            cont += 1
            print(f"<Escola> {escola_obj.nome} criada.")
    print(f"{bcolors.OKBLUE}Criadas {cont} <Escola> do tipo CEI...{bcolors.ENDC}")
    time.sleep(4)


cria_tipo_unidade_escolar()
cria_escola()
printa_pontinhos()
