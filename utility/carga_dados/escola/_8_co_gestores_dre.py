import time

import environ
import numpy as np
import pandas as pd

from src.escola.models import DiretoriaRegional
from src.perfil.models import Perfil, Usuario
from utility.carga_dados.escola.helper import (
    bcolors,
    coloca_zero_a_esquerda,
    printa_pontinhos,
    somente_digitos,
)

from .helper import cria_vinculo_de_perfil_usuario

ROOT_DIR = environ.Path(__file__) - 1

df = pd.read_excel(
    f"{ROOT_DIR}/planilhas_de_carga/cogestores2020.xlsx",
    converters={
        "RF": str,
        "RF-SUPLENTE": str,
        "CPF-COGESTOR": str,
        "CPF-SUPLENTE": str,
    },
    sheet_name="cogestores",
)

# tira os NAN e troca por espaco vazio ''
df = df.replace(np.nan, "", regex=True)

# padroniza os dados
df["DRE"] = df["DRE"].str.strip().str.upper()
df["COGESTOR"] = df["COGESTOR"].str.strip().str.upper()
df["RF"] = df["RF"].str.strip().str.upper()
df["CPF-COGESTOR"] = df["CPF-COGESTOR"].str.strip().str.upper()
df["E-MAIL"] = df["E-MAIL"].str.strip()
df["SUPLENTE"] = df["SUPLENTE"].str.strip().str.upper()
df["RF-SUPLENTE"] = df["RF-SUPLENTE"].str.strip().str.upper()
df["CPF-SUPLENTE"] = df["CPF-SUPLENTE"].str.strip().str.upper()
df["E-MAIL-SUPLENTE"] = df["E-MAIL-SUPLENTE"].str.strip()


def busca_diretoria_regional(nome_dre):
    try:
        return DiretoriaRegional.objects.get(iniciais__icontains=nome_dre)
    except DiretoriaRegional.DoesNotExist:
        return None


def retorna_apenas_numeros_registro_funcional(registro_funcional):
    return registro_funcional.replace(".", "").replace("-", "")


def cria_usuario_gestor_ou_suplente(registro_funcional, nome, email, cpf):
    if nome == "SEM SUPLENTE":
        return None
    else:
        email = f"{cpf}@emailteste.sme.prefeitura.sp.gov.br"
        usuario = Usuario.objects.create_user(email, registro_funcional)
        usuario.registro_funcional = retorna_apenas_numeros_registro_funcional(
            registro_funcional
        )
        usuario.nome = nome
        cpf = somente_digitos(cpf)
        usuario.cpf = coloca_zero_a_esquerda(cpf, 11)
        usuario.is_active = False
        usuario.save()
        return usuario


def atribui_e_salva_cargos_a_dre(diretoria_regional, cargos):
    for cargo in cargos:
        if cargo["usuario"] is not None:
            cria_vinculo_de_perfil_usuario(
                cargo["perfil"], cargo["usuario"], diretoria_regional
            )
            print(
                f'{bcolors.OKBLUE}<Usuario>: {cargo["usuario"].nome} foi criado e atribuido a <DiretoriaRegional>: {diretoria_regional.nome}{bcolors.ENDC}'
            )


def percorre_data_frame():
    perfil_gestor, created = Perfil.objects.get_or_create(
        nome="COGESTOR_DRE", ativo=True, super_usuario=True
    )

    for index, row in df.iterrows():
        dre = busca_diretoria_regional(row["DRE"])
        cogestor = cria_usuario_gestor_ou_suplente(
            row["RF"], row["COGESTOR"], row["E-MAIL"], row["CPF-COGESTOR"]
        )
        suplente = cria_usuario_gestor_ou_suplente(
            row["RF-SUPLENTE"],
            row["SUPLENTE"],
            row["E-MAIL-SUPLENTE"],
            row["CPF-SUPLENTE"],
        )
        atribui_e_salva_cargos_a_dre(
            dre,
            [
                {"usuario": cogestor, "perfil": perfil_gestor},
                {"usuario": suplente, "perfil": perfil_gestor},
            ],
        )


percorre_data_frame()
printa_pontinhos()
time.sleep(4)
