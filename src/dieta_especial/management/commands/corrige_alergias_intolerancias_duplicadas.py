import logging
import re
import unicodedata

from django.core.management import BaseCommand
from django.db.models import F, Func, Value
from django.db.models.functions import Trim, Upper

from src.dieta_especial.solicitacao_dieta_especial.models import (
    AlergiaIntolerancia,
)

logger = logging.getLogger("sigpae.cmd_corrige_alergias_intolerancias_duplicadas")


class Command(BaseCommand):
    """Script para corrigir alergias/intolerancias duplicadas."""

    help = "Corrige alergias/intolerancias duplicadas"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("*** Alergias / Intolerancias ***"))
        self.normalizar_alergias_intolerancias()
        self.corrige_alergias_intolerancias()
        self.remove_duplicados_alergias_intolerancias()

    def remove_duplicados_alergias_intolerancias(self):  # noqa C901
        for alergia in AlergiaIntolerancia.objects.all():
            try:
                alergia_original = AlergiaIntolerancia.objects.filter(
                    descricao=alergia.descricao
                ).first()
                alergias_duplicadas = AlergiaIntolerancia.objects.filter(
                    descricao=alergia.descricao
                ).exclude(id=alergia_original.id)
                for alergia_duplicada in alergias_duplicadas:
                    for (
                        solicitacao
                    ) in alergia_duplicada.solicitacaodietaespecial_set.all():
                        solicitacao.alergias_intolerancias.remove(alergia_duplicada)
                        solicitacao.alergias_intolerancias.add(alergia_original)
                alergias_duplicadas.delete()
            except Exception:
                self.stdout.write(
                    self.style.ERROR(
                        f"Erro ao atualizar alergia/intolerancia {alergia.descricao}"
                    )
                )

    def remove_acentos(self, text):
        text = (
            unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
        )
        return str(text)

    def normalizar_alergias_intolerancias(self):
        self.stdout.write(self.style.SUCCESS("Convertendo para UPPER"))
        AlergiaIntolerancia.objects.update(descricao=Upper("descricao"))
        self.stdout.write(self.style.SUCCESS("Removendo espaços no inicio e fim"))
        AlergiaIntolerancia.objects.update(descricao=Trim("descricao"))
        self.stdout.write(self.style.SUCCESS("Removendo espaços duplos"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="  ").update(
            descricao=Func(F("descricao"), Value("  "), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo pontos"))
        AlergiaIntolerancia.objects.filter(descricao__icontains=".").update(
            descricao=Func(F("descricao"), Value("."), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo virgulas"))
        AlergiaIntolerancia.objects.filter(descricao__icontains=",").update(
            descricao=Func(F("descricao"), Value(","), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo traços"))
        AlergiaIntolerancia.objects.filter(descricao__icontains=" - ").update(
            descricao=Func(F("descricao"), Value(" - "), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo aspas"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="'").update(
            descricao=Func(F("descricao"), Value("'"), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo parênteses"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="(").update(
            descricao=Func(F("descricao"), Value("("), Value(""), function="replace")
        )
        AlergiaIntolerancia.objects.filter(descricao__icontains=")").update(
            descricao=Func(F("descricao"), Value(")"), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Trocando & por E"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="&").update(
            descricao=Func(F("descricao"), Value("&"), Value("E"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Trocando / por espaço"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="/").update(
            descricao=Func(F("descricao"), Value("/"), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo acentos"))
        for alergia in AlergiaIntolerancia.objects.all():
            alergia.descricao = re.sub(r"\s+", " ", alergia.descricao)
            if self.remove_acentos(alergia.descricao) != alergia.descricao:
                alergia.descricao = self.remove_acentos(alergia.descricao)
            alergia.save()

    def corrige_alergias_intolerancias(self):
        self.stdout.write(
            self.style.SUCCESS("Normalizando alergias / intolerancias para unificação")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo ALERGIA AO por ALERGIA"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="ALERGIA AO").update(
            descricao=Func(
                F("descricao"),
                Value("ALERGIA AO"),
                Value("ALERGIA"),
                function="replace",
            )
        )
        self.stdout.write(self.style.SUCCESS("Substituindo ALERGIA A por ALERGIA"))
        AlergiaIntolerancia.objects.filter(descricao__icontains="ALERGIA A").update(
            descricao=Func(
                F("descricao"), Value("ALERGIA A"), Value("ALERGIA"), function="replace"
            )
        )
