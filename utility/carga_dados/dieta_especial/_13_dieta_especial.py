import environ
import pandas as pd

from sme_sigpae_api.dieta_especial.models import Alimento
from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
    MotivoNegacao,
)
from utility.carga_dados.escola.helper import printa_pontinhos

ROOT_DIR = environ.Path(__file__) - 1


def importa_alergias_intolerancias():
    df = pd.read_excel(
        f"{ROOT_DIR}/planilhas_de_carga/relacao_diagnostico.xlsx",
        sheet_name="Relátorio Diagnóstico",
    )

    for index, row in df.iterrows():
        alergia = AlergiaIntolerancia.objects.create(descricao=row["Diagnóstico"])
        print(f"<AlergiaIntolerancia> {alergia.descricao} criada...")


def importa_alimentos():
    df = pd.read_excel(
        f"{ROOT_DIR}/planilhas_de_carga/alimentos.xlsx",
        sheet_name="Planilha1",
        header=1,
    )
    for index, row in df.iterrows():
        value = row["Dieta Especial - PARA:"]
        if pd.notna(value):
            alm = Alimento.objects.create(nome=value)
            print(f"<Alimento> {alm.nome} criado...")


def importa_motivos_negacao():
    df = pd.read_excel(
        f"{ROOT_DIR}/planilhas_de_carga/motivos_negacao.xlsx", sheet_name="Planilha1"
    )

    for index, row in df.iterrows():
        mot = MotivoNegacao.objects.create(descricao=row["Motivos"])
        print(f"<MotivoNegacao> {mot.descricao} criado...")


def cria_classificacoes_dieta():
    classificacoes = [
        ["Tipo A", "Classificação da dieta tipo A deve vir aqui"],
        ["Tipo A Enteral", "Classificação da dieta tipo A Enteral deve vir aqui"],
        ["Tipo B", "Classificação da dieta tipo B deve vir aqui"],
        ["Tipo C", "Classificação da dieta tipo C deve vir aqui"],
    ]
    for nome, descricao in classificacoes:
        classificacao = ClassificacaoDieta.objects.create(
            nome=nome, descricao=descricao
        )
        print(
            f"<ClassificacaoDieta> {classificacao.nome} {classificacao.descricao} criada..."
        )


importa_alergias_intolerancias()
importa_alimentos()
importa_motivos_negacao()
cria_classificacoes_dieta()

printa_pontinhos()
