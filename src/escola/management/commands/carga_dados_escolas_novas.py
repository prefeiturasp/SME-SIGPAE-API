import csv

from django.core.management.base import BaseCommand

from src.escola.models import (  # noqa
    DiretoriaRegional,
    Escola,
    Lote,
    TipoGestao,
    TipoUnidadeEscolar,
)
from utility.carga_dados.helper import progressbar


def csv_to_list(filename: str) -> list:
    with open(filename) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=",")
        csv_data = [line for line in reader]
    return csv_data


def cria_novas_escolas(
    unidade_escolar, codigo_eol, dre, nome_tipo_unidade, lote
):  # noqa
    tipo_gestao = TipoGestao.objects.get(nome="TERC TOTAL")
    tipo_unidade = TipoUnidadeEscolar.objects.filter(
        iniciais=nome_tipo_unidade
    ).first()  # noqa
    nome = f"{nome_tipo_unidade} {unidade_escolar}"
    Escola.objects.create(
        nome=nome,
        codigo_eol=codigo_eol,
        diretoria_regional=dre,
        tipo_unidade=tipo_unidade,
        tipo_gestao=tipo_gestao,
        lote=lote,
    )


class Command(BaseCommand):
    help = "Importa dados de planilhas específicas das escolas de DRE específicas."

    # flake8: noqa: C901
    def handle(self, *args, **options):
        self.stdout.write("Importando dados...")

        arquivo_escolas_novas = "src/escola/data/escolas_novas_codigo_eol.csv"

        escolas_novas = csv_to_list(arquivo_escolas_novas)

        for item in progressbar(escolas_novas, "Escolas Novas"):
            codigo_eol = str(item["CODIGO_EOL"]).replace(".0", "").zfill(6)
            if Escola.objects.filter(codigo_eol=codigo_eol).first():
                continue
            if (
                item["DRE"].strip() == "CLI I" or item["DRE"].strip() == "CLI II"
            ):  # noqa
                item_dre = "CL"
            else:
                item_dre = item["DRE"].strip()
            dre = DiretoriaRegional.objects.get(iniciais__icontains=item_dre)
            item_lote = item["DRE"]
            lote = Lote.objects.get(iniciais=item_lote)
            cria_novas_escolas(
                item["UNIDADE_ESCOLAR"], codigo_eol, dre, item["TIPO"].strip(), lote
            )  # noqa
        print(Escola.objects.all().count(), "escolas")  # noqa T001
