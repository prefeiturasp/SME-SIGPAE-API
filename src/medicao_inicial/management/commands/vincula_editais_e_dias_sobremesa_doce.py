import logging

import environ
from django.core.management import BaseCommand

from src.medicao_inicial.models import DiaSobremesaDoce
from src.perfil.models import Usuario
from src.terceirizada.models import Edital

logger = logging.getLogger("sigpae.cmd_vincula_editais_e_dias_sobremesa_doce")

env = environ.Env()


class Command(BaseCommand):
    help = "Suja base de dados para que não tenha e-mails verdadeiros em ambientes que não são produção"

    def handle(self, *args, **options):
        if env("DJANGO_ENV") == "production":
            self.stdout.write(
                self.style.SUCCESS("Rodando script para ambiente de PRODUÇÃO")
            )
            self.vincula_editais_ambiente_producao()
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Rodando script para ambiente de {env('DJANGO_ENV')}"
                )
            )
            self.vincula_editais_ambientes_comuns()

    def vincula_editais_ambiente_producao(self):
        lista_editais_prod = [
            "Edital de pregão n° 28/SME/2022",
            "Edital de Pregão n° 35/SME/2022",
            "Edital de pregão n° 30/SME/2022",
            "Edital de Pregão n° 36/SME/2022",
            "Edital de Pregão n°70/SME/2022",
            "Edital de pregão n° 87/SME/2022",
            "Edital de pregão n° 76/SME/2022",
            "Edital de Pregão n° 78/SME/2022",
            "Edital de Pregão n° 74/SME/2022",
        ]
        editais = Edital.objects.filter(numero__in=lista_editais_prod)
        self.vincula_editais(editais)

    def vincula_editais_ambientes_comuns(self):
        editais = Edital.objects.all()
        self.vincula_editais(editais)

    def vincula_editais(self, editais):
        dias_sobremesa_sem_edital = DiaSobremesaDoce.objects.filter(edital__isnull=True)
        if not dias_sobremesa_sem_edital:
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "*** Não existem regitros de DiaSobremesaDoce sem edital ***"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "****************************************************************"
                )
            )
        total_dias_sobremesa_sem_edital = dias_sobremesa_sem_edital.count()
        total_editais = editais.count()
        for i_dia, dia_sobremesa_doce in enumerate(dias_sobremesa_sem_edital):
            self.stdout.write(
                self.style.SUCCESS(
                    f"*** Dia {dia_sobremesa_doce.data} - Unidade {dia_sobremesa_doce.tipo_unidade} - ({i_dia + 1}/{total_dias_sobremesa_sem_edital}) ***"
                )
            )
            for i_edital, edital in enumerate(editais):
                if i_edital == 0:
                    dia_sobremesa_doce.edital = edital
                    dia_sobremesa_doce.save()
                else:
                    DiaSobremesaDoce.objects.create(
                        data=dia_sobremesa_doce.data,
                        tipo_unidade=dia_sobremesa_doce.tipo_unidade,
                        edital=edital,
                        criado_por=Usuario.objects.filter(
                            email="system@admin.com"
                        ).first(),
                    )
                self.stdout.write(
                    self.style.WARNING(
                        f"****** Vinculando edital {edital.numero} - ({i_edital + 1}/{total_editais}) -- {dia_sobremesa_doce.data} - {dia_sobremesa_doce.tipo_unidade} - ({i_dia + 1}/{total_dias_sobremesa_sem_edital}) ******"
                    )
                )
        return
