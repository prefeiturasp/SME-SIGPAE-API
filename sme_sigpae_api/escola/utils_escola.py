import asyncio
import logging
import subprocess  # nosec
import time
from datetime import date, datetime
from tempfile import NamedTemporaryFile

import httpx
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    DJANGO_EOL_API_TOKEN,
    DJANGO_EOL_API_URL,
)
from sme_sigpae_api.escola.models import (
    Escola,
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
    TipoGestao,
)
from utility.carga_dados.helper import excel_to_list_with_openpyxl

logger = logging.getLogger("sigpae.taskEscola")

MDATA = datetime.now().strftime("%Y%m%d_%H%M%S")
DEFAULT_HEADERS = {"Authorization": f"Token {DJANGO_EOL_API_TOKEN}"}
DATA = date.today().isoformat().replace("-", "_")
PATH = str(settings.MEDIA_ROOT)
dict_codigos_escolas = {}
dict_codigo_aluno_por_codigo_escola = {}


def get_codigo_eol_escola(valor):
    return valor.strip().zfill(6)


def get_codigo_eol_aluno(valor):
    return str(valor).strip().zfill(7)


def gera_dict_codigos_escolas(items_codigos_escolas):
    for item in items_codigos_escolas:
        dict_codigos_escolas[str(item["CÓDIGO UNIDADE"])] = str(item["CODIGO EOL"])


def grava_codescola_nao_existentes(valor):
    with open(f"{PATH}/codescola_nao_existentes.txt", "a") as f:
        f.write(f"{valor}\n")


def gera_dict_codigo_aluno_por_codigo_escola(items):
    for item in items:
        try:
            codigo_eol_escola = dict_codigos_escolas[item["CodEscola"]]
        except Exception as e:
            # Grava os CodEscola não existentes em unidades_da_rede_28.01_.xlsx
            grava_codescola_nao_existentes(item["CodEscola"])
            raise e

        cod_eol_aluno = get_codigo_eol_aluno(item["CodEOLAluno"])
        # chave: cod_eol_aluno, valor: codigo_eol_escola
        dict_codigo_aluno_por_codigo_escola[cod_eol_aluno] = get_codigo_eol_escola(
            codigo_eol_escola
        )


def get_escolas_unicas(items):
    """A partir da planilha, pegar todas as escolas únicas "escolas_da_planilha".

    Retorna escolas únicas.
    """
    escolas = []
    for item in items:
        escolas.append(item["CodEscola"])
    return set(escolas)


class EOLException(Exception):
    pass


def escreve_escolas_json(arquivo, texto):
    with open(arquivo, "a") as f:
        f.write(texto)
    return arquivo


def ajustes_no_arquivo(arquivo):
    # Troca aspas simples por aspas duplas (foi necessário dois replace).
    subprocess.run(f'sed -i "s/\'/?/g" {arquivo}', shell=True)  # nosec
    subprocess.run(f"sed -i 's/?/\"/g' {arquivo}", shell=True)  # nosec

    # Insere uma vírgula em todas as linhas exceto na última
    subprocess.run(f"sed -i '$ !s/$/,/' {arquivo}", shell=True)  # nosec

    # remove virgula da primeira linha
    subprocess.run(f"sed -i '1s/,//' {arquivo}", shell=True)  # nosec


async def get_informacoes_escola_turma_aluno(tempfile: str, codigo_eol: str):
    headers = DEFAULT_HEADERS
    async with httpx.AsyncClient(headers=headers, timeout=120) as client:
        url = f"{DJANGO_EOL_API_URL}/escola_turma_aluno/{codigo_eol}"
        response = await client.get(url)
        if response.status_code == status.HTTP_200_OK:
            results = response.json()["results"]
            if len(results) == 0:
                raise EOLException(f"Resultados para o código: {codigo_eol} vazios")

            escreve_escolas_json(tempfile, f'"{codigo_eol}": {results}\n')

            return results
        else:
            with open(f"{PATH}/codigo_eol_erro_da_api_eol.txt", "a") as f:
                f.write(f"{codigo_eol}\n")


def create_tempfile():
    tmp = NamedTemporaryFile()
    filename = f"{tmp.name}.json"
    return filename


async def main(tempfile, escolas_da_planilha):
    task_list = []

    for escola in escolas_da_planilha:
        try:
            codigo_eol_escola = get_codigo_eol_escola(dict_codigos_escolas[escola])
            task_list.append(
                get_informacoes_escola_turma_aluno(tempfile, codigo_eol_escola)
            )
        except Exception as e:
            # Grava os CodEscola não existentes em unidades_da_rede_28.01_.xlsx
            grava_codescola_nao_existentes(escola)
            raise e

    await asyncio.gather(*task_list)


def get_escolas(arquivo, arquivo_codigos_escolas, tempfile, in_memory):
    items = excel_to_list_with_openpyxl(arquivo, in_memory=in_memory)
    items_codigos_escolas = excel_to_list_with_openpyxl(
        arquivo_codigos_escolas, in_memory=in_memory
    )

    gera_dict_codigos_escolas(items_codigos_escolas)
    gera_dict_codigo_aluno_por_codigo_escola(items)

    # A partir da planilha, pegar todas as escolas únicas "escolas_da_planilha"
    escolas_da_planilha = list(get_escolas_unicas(items))

    # Particiona os intervalos da lista para fazer apenas 100 requisições por vez.
    limit = 100
    for i in range(0, len(escolas_da_planilha) + 1, limit):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main(tempfile, escolas_da_planilha[i : i + limit]))
        print("Waiting...")  # noqa T001
        time.sleep(10)

    ajustes_no_arquivo(tempfile)
    escreve_escolas_json(tempfile, "}\n")

    return tempfile


def atualiza_codigo_codae_das_escolas(path_planilha, id_planilha):  # noqa: C901
    dados_planilha = excel_to_list_with_openpyxl(path_planilha)

    count = 0
    for info_escola in dados_planilha:
        if info_escola.get("codigo_eol"):
            escola = Escola.objects.filter(
                codigo_eol=f'{info_escola.get("codigo_eol"):06d}'
            ).first()

            if escola:
                escola.codigo_codae = f'{info_escola.get("codigo_unidade"):05d}'
                escola.save()
                count += 1

    try:
        obj_planilha = PlanilhaEscolaDeParaCodigoEolCodigoCoade.objects.get(
            id=id_planilha
        )
        obj_planilha.codigos_codae_vinculados = True
        obj_planilha.save()
    except ObjectDoesNotExist:
        pass

    logger.debug(f"Código(s) codae de {count} escola(s) foram atualizados")


def atualiza_tipo_gestao_das_escolas(path_planilha, id_planilha):  # noqa: C901
    dados_planilha = excel_to_list_with_openpyxl(path_planilha)

    def retorna_tipo_gestao(tipo):
        parceira = TipoGestao.objects.get(nome="PARCEIRA")
        mista = TipoGestao.objects.get(nome="MISTA")
        direta = TipoGestao.objects.get(nome="DIRETA")
        terc_total = TipoGestao.objects.get(nome="TERC TOTAL")

        tipo_gestao = {
            "PARCEIRA": parceira,
            "MISTA": mista,
            "DIRETA": direta,
            "TERCEIRIZADA TOTAL": terc_total,
        }
        return tipo_gestao.get(tipo)

    count = 0
    for info_escola in dados_planilha:
        if info_escola.get("CÓDIGO EOL"):
            try:
                escola = Escola.objects.get(
                    codigo_eol=f'{info_escola.get("CÓDIGO EOL"):06d}'
                )
                escola.tipo_gestao = retorna_tipo_gestao(info_escola.get("TIPO"))
                escola.save()
                count += 1
            except ObjectDoesNotExist:
                pass

    try:
        obj_planilha = PlanilhaAtualizacaoTipoGestaoEscola.objects.get(id=id_planilha)
        obj_planilha.processamento_com_sucesso()
    except ObjectDoesNotExist:
        pass

    logger.debug(f"Tipo de gestão de {count} escola(s) foram atualizados")
