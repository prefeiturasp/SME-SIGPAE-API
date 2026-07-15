import logging

from django.core.management import BaseCommand

from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
)
from src.escola.models import PeriodoEscolar

logger = logging.getLogger("sigpae.cmd_gerar_logs_dietas_periodo_escolar")


class Command(BaseCommand):
    """Script para criar logs de dietas especiais com periodo escolar."""

    help = "Corrige alergias/intolerancias duplicadas"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("*** Gerando logs ***"))
        logs_para_criar = []
        dict_periodos = PeriodoEscolar.dict_periodos()
        for log in LogQuantidadeDietasAutorizadas.objects.all():
            for periodo_escolar_nome in log.escola.periodos_escolares_com_alunos:
                novo_log = LogQuantidadeDietasAutorizadas(
                    quantidade=log.quantidade,
                    escola=log.escola,
                    data=log.data,
                    periodo_escolar=dict_periodos[periodo_escolar_nome],
                    classificacao=log.classificacao,
                )
                logs_para_criar.append(novo_log)
        LogQuantidadeDietasAutorizadas.objects.bulk_create(logs_para_criar)
        self.stdout.write(
            self.style.SUCCESS(f"*** {len(logs_para_criar)} logs criados ***")
        )
