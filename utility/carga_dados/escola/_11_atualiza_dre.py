import json
import os

import environ

from src.escola.models import DiretoriaRegional
from utility.carga_dados.escola.helper import bcolors, printa_pontinhos

ROOT_DIR = environ.Path(__file__) - 1
with open(os.path.join(ROOT_DIR, "planilhas_de_carga", "dres.json"), "r") as f:
    json_data = json.loads(f.read())

for diret in json_data["results"]:
    codigo_dre = diret["cod_dre"].strip()
    sigla_dre = diret["sg_dre"].strip()
    dre_nome = diret["dre"].strip()

    dre_object, created = DiretoriaRegional.objects.get_or_create(codigo_eol=codigo_dre)
    dre_object.iniciais = sigla_dre
    dre_object.nome = dre_nome
    dre_object.save()

    if created:
        print(
            f"{bcolors.OKBLUE}<DiretoriaRegional> criada.. {dre_object.nome}{bcolors.ENDC}"
        )
    else:
        print(
            f"{bcolors.OKBLUE}<DiretoriaRegional> atualizada.. {dre_object.nome}{bcolors.ENDC}"
        )

printa_pontinhos()
