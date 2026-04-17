import csv

import environ

from sme_sigpae_api.dieta_especial.protocolo_padrao.models import Alimento
from utility.carga_dados.escola.helper import printa_pontinhos

ROOT_DIR = environ.Path(__file__) - 1


def importa_alimentos():
    csvfile = open(f"{ROOT_DIR}/planilhas_de_carga/alimentos2.csv", newline="")
    reader = csv.reader(csvfile)
    for row in reader:
        alm = Alimento.objects.create(nome=row[0])
        print(f"<Alimento> {alm.nome} criado...")


importa_alimentos()

printa_pontinhos()
