import re

import pandas as pd
import pdfplumber
import requests
from django.core.management.base import BaseCommand

from sme_sigpae_api.dados_comuns.constants import DJANGO_EOL_SGP_API_TOKEN

HEADERS = {"x-api-eol-key": DJANGO_EOL_SGP_API_TOKEN}

API_URL = (
    "https://smeintegracaoapi.sme.prefeitura.sp.gov.br/api/funcionarios/DadosSigpae/{}"
)


def normalizar_cpf(cpf_str: str) -> str:
    """Remove pontos, traços e mantém só os dígitos"""
    return re.sub(r"\D", "", cpf_str)


def extrair_cpfs_pdf(pdf_path: str) -> list[str]:
    """Extrai CPFs da última coluna das tabelas de um PDF"""
    with pdfplumber.open(pdf_path) as pdf:
        return [
            cpf
            for page in pdf.pages
            for table in page.extract_tables()
            for row in table
            for cpf in [extrair_cpf_de_linha(row)]
            if cpf
        ]


def extrair_cpf_de_linha(row: list[str]) -> str | None:
    """Pega o último campo da linha, normaliza e valida CPF"""
    if not row:
        return None
    cpf_raw = row[-1]
    if not cpf_raw:
        return None
    cpf_norm = normalizar_cpf(cpf_raw)
    if cpf_norm and len(cpf_norm) == 11:
        return cpf_norm
    return None


def consultar_api(cpf: str) -> dict:
    """Consulta a API da SME para o CPF"""
    url = API_URL.format(cpf)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code == 200:
        return resp.json()
    else:
        return {"cpf": cpf, "erro": resp.status_code}


def salvar_excel(dados: list[dict], output_file: str):
    """Salva a lista de dicionários em um Excel"""
    df = pd.json_normalize(dados)
    df.to_excel(output_file, index=False)


class Command(BaseCommand):
    help = "Extrai CPFs de um PDF, consulta na API da SME e gera um Excel"

    def add_arguments(self, parser):
        parser.add_argument("pdf_entrada", type=str, help="Caminho do PDF de entrada")
        parser.add_argument(
            "--saida",
            type=str,
            default="resultado.xlsx",
            help="Arquivo Excel de saída (default: resultado.xlsx)",
        )

    def handle(self, *args, **options):
        pdf_entrada = options["pdf_entrada"]
        arquivo_saida = options["saida"]

        self.stdout.write(self.style.NOTICE("Extraindo CPFs do PDF..."))
        cpfs = extrair_cpfs_pdf(pdf_entrada)

        resultados = []
        for cpf in cpfs:
            self.stdout.write(f"Consultando {cpf}...")
            dados = consultar_api(cpf)
            resultados.append(dados)

        self.stdout.write(self.style.NOTICE("Salvando resultados em Excel..."))
        salvar_excel(resultados, arquivo_saida)

        self.stdout.write(
            self.style.SUCCESS(f"Concluído! Arquivo salvo em {arquivo_saida}")
        )
