import environ
import numpy as np
import pandas as pd

from src.escola.models import Codae
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
    f"{ROOT_DIR}/planilhas_de_carga/CODAE_RF_CPF2020.xlsx",
    converters={"Nome": str, "RF": str, "CPF": str, "Núcleo da CODAE": str},
    sheet_name="codae",
)

# tira os NAN e troca por espaco vazio ''
df = df.replace(np.nan, "", regex=True)

# padroniza os dados
df["Nome"] = df["Nome"].str.strip().str.upper()
df["CPF"] = df["CPF"].str.strip().str.upper()
df["RF"] = df["RF"].str.strip().str.upper()
df["Núcleo da CODAE"] = df["Núcleo da CODAE"].str.strip().str.upper()


def retorna_apenas_numeros_registro_funcional(registro_funcional):
    return registro_funcional.replace(".", "").replace("-", "")


def cria_usuario_gestor_alimentacao_ou_dieta_especial(registro_funcional, nome, cpf):
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


def atribui_e_salva_cargos_a_codae(cargos):
    codae, created = Codae.objects.get_or_create(nome="CODAE")
    for cargo in cargos:
        cria_vinculo_de_perfil_usuario(cargo["perfil"], cargo["usuario"], codae)
        print(
            f'{bcolors.OKBLUE}<Usuario>: {cargo["usuario"].nome} foi criado e atribuido ao <Perfil> CODAE: {cargo["perfil"].nome}{bcolors.ENDC}'
        )


def percorre_data_frame():
    gestao_alimentacao, created = Perfil.objects.get_or_create(
        nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA",
        ativo=True,
        super_usuario=True,
    )
    # DIFIR - Divisão Financeira
    # GTIC - Gestão de Tecnologia e Informação

    dieta_especial, created = Perfil.objects.get_or_create(
        nome="COORDENADOR_DIETA_ESPECIAL", ativo=True, super_usuario=True
    )
    for index, row in df.iterrows():
        gestor_de_alimentacao_ou_dieta = (
            cria_usuario_gestor_alimentacao_ou_dieta_especial(
                row["RF"], row["Nome"], row["CPF"]
            )
        )
        if row["Núcleo da CODAE"] == "DIETA ESPECIAL":
            perfil = dieta_especial
        # elif row['Núcleo da CODAE'] == 'GTIC':
        #     perfil = gestao_tecnologia_informacao
        # elif row['Núcleo da CODAE'] == 'DIFIR':
        #     perfil = gestao_financeira
        else:
            perfil = gestao_alimentacao

        atribui_e_salva_cargos_a_codae(
            [
                {"usuario": gestor_de_alimentacao_ou_dieta, "perfil": perfil},
            ]
        )


percorre_data_frame()
printa_pontinhos()
