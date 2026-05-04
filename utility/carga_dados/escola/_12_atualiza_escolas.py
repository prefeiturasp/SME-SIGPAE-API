import json
import os
import time

import environ
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from src.escola.management.commands.helper import (
    calcula_total_alunos_por_escola_por_periodo,
)
from src.escola.models import Escola, EscolaPeriodoEscolar, PeriodoEscolar
from utility.carga_dados.escola.helper import bcolors, printa_pontinhos

ROOT_DIR = environ.Path(__file__) - 1
with open(os.path.join(ROOT_DIR, "planilhas_de_carga", "total_alunos.json"), "r") as f:
    json_data_totais = json.loads(f.read())

with open(os.path.join(ROOT_DIR, "planilhas_de_carga", "escolas.json"), "r") as f:
    json_data_escola = json.loads(f.read())

escola_totais = calcula_total_alunos_por_escola_por_periodo(json_data_totais)


def _atualiza_totais_alunos_escola(escola_totais):  # noqa C901
    for codigo_eol, dados in escola_totais.items():
        try:
            escola_object = Escola.objects.get(codigo_eol=codigo_eol)
            for periodo_escolar_str, quantidade_alunos_periodo in dados.items():
                periodo_escolar_object = PeriodoEscolar.objects.get(
                    nome=periodo_escolar_str.upper()
                )
                escola_periodo, created = EscolaPeriodoEscolar.objects.get_or_create(
                    periodo_escolar=periodo_escolar_object, escola=escola_object
                )
                if escola_periodo.quantidade_alunos != quantidade_alunos_periodo:
                    msg = f"Atualizando qtd alunos da escola {escola_object.nome} de {escola_periodo.quantidade_alunos} para {quantidade_alunos_periodo} no período da {periodo_escolar_object.nome}"  # noqa
                    print(msg)
                    escola_periodo.quantidade_alunos = quantidade_alunos_periodo
                    escola_periodo.save()

        except ObjectDoesNotExist:
            continue
        except IntegrityError as e:
            msg = f"{bcolors.FAIL}Dados inconsistentes: {e}{bcolors.ENDC}"
            print(msg)
            continue


def _atualiza_dados_da_escola(json):  # noqa C901
    for escola_json in json["results"]:
        codigo_eol_escola = escola_json["cd_unidade_educacao"].strip()
        nome_unidade_educacao = escola_json["nm_unidade_educacao"].strip()
        tipo_ue = escola_json["sg_tp_escola"].strip()
        nome_escola = f"{tipo_ue} {nome_unidade_educacao}"
        try:
            escola_object = Escola.objects.get(codigo_eol=codigo_eol_escola)
        except ObjectDoesNotExist:
            msg = f"Escola código EOL: {codigo_eol_escola} não existe no banco ainda"
            # print(msg)
            continue
        if escola_object.nome != nome_escola:
            msg = f"Atualizando nome da escola {escola_object} para {nome_escola}"
            print(msg)
            escola_object.nome = nome_escola
            escola_object.save()


print(
    f"{bcolors.WARNING}Atualiza os dados das escolas (nome e totais de alunos por período escolar) baseado num dump da api do EOL..{bcolors.ENDC}"
)
time.sleep(4)
_atualiza_dados_da_escola(json_data_escola)
_atualiza_totais_alunos_escola(escola_totais)
printa_pontinhos()
