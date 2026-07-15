import time

import environ
import numpy as np
import pandas as pd

from src.escola.models import Escola
from src.perfil.models import Perfil, Usuario
from utility.carga_dados.escola.helper import bcolors, printa_pontinhos

from .helper import coloca_zero_a_esquerda, cria_vinculo_de_perfil_usuario

ROOT_DIR = environ.Path(__file__) - 1

df = pd.read_csv(
    f"{ROOT_DIR}/planilhas_de_carga/diretores2020.csv",
    sep=",",
    converters={"cd_unidade_base": str, "rf": str, "cd_cpf_pessoa": str},
    engine="python",
)

# exclui registros duplicados no arquivo csv
df.drop_duplicates(subset="cd_cpf_pessoa", keep=False, inplace=True)

# tira os NAN e troca por espaco vazio ''
df = df.replace(np.nan, "", regex=True)

# padroniza os dados
df["cd_unidade_base"] = df["cd_unidade_base"].str.strip(".0")


def busca_escola(codigo_eol):
    try:
        return Escola.objects.get(codigo_eol=codigo_eol)
    except Escola.DoesNotExist:
        return None


def cria_usuario_diretor(cpf, registro_funcional, nome):
    email = f"{cpf}@dev.prefeitura.sp.gov.br"
    diretor = Usuario.objects.create_user(email, registro_funcional)
    diretor.registro_funcional = registro_funcional
    diretor.nome = nome
    diretor.cpf = coloca_zero_a_esquerda(cpf, 11)
    diretor.is_active = False
    diretor.save()
    return diretor


def percorre_data_frame():
    diretores_criados = 0
    diretores_contabilizados = 0
    eol_zerado = 0

    perfil_usuario, created = Perfil.objects.get_or_create(
        nome="DIRETOR", ativo=True, super_usuario=True
    )

    for index, row in df.iterrows():
        diretores_contabilizados += 1
        codigo_eol = coloca_zero_a_esquerda(row["cd_unidade_base"])
        if codigo_eol == "000000":
            eol_zerado += 1
        escola = busca_escola(codigo_eol)

        if escola is not None:
            cpf = row["cd_cpf_pessoa"]
            if not cpf:
                print("cpf vazio..........", row)
                return
            diretor = cria_usuario_diretor(
                row["cd_cpf_pessoa"], row["rf"], row["nm_nome"]
            )
            escola.save()
            cria_vinculo_de_perfil_usuario(perfil_usuario, diretor, escola)
            diretores_criados += 1

            print(f"<Usuario>: {diretor.nome} foi vinculado a <Escola>: {escola.nome}")

    print(
        f"{bcolors.OKBLUE}foram contabilizados {diretores_contabilizados} <Usuario> <Perfil> diretor{bcolors.ENDC}"
    )
    print(
        f"{bcolors.OKBLUE}foram criadas {diretores_criados} contas de <Usuario> atreladas a <Perfil> diretor{bcolors.ENDC}"
    )
    print(
        f"{bcolors.WARNING}foram encontrados {eol_zerado} diretores sem estar atrelados a uma escola{bcolors.ENDC}"
    )
    outras_gestoes = diretores_contabilizados - (diretores_criados + eol_zerado)
    print(
        f"{bcolors.WARNING}foram encontrados {outras_gestoes} diretores atrelados a escolas de outros tipos de gestao{bcolors.ENDC}"
    )


percorre_data_frame()
printa_pontinhos()
time.sleep(4)
