from django.core.management.base import BaseCommand

from src.escola.models import EscolaPeriodoEscolar
from src.kit_lanche.models import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
)


class Command(BaseCommand):
    help = """
    Popular coluna matriculados_quando_criado com base na data das solicitações de kit lanche.
    """

    def handle(self, *args, **options):
        self.stdout.write("Iniciando processo de popular matriculados_quando_criado.")
        self.popular_kit_lanche_cei()

    def popular_kit_lanche_cei(self):
        self.stdout.write("+++ INICIANDO KIT LANCHE CEI +++")
        class_faixa = FaixaEtariaSolicitacaoKitLancheCEIAvulsa
        solicitacoes_pks = class_faixa.objects.filter(matriculados_quando_criado=None)
        solicitacoes_pks = solicitacoes_pks.values_list(
            "solicitacao_kit_lanche_avulsa", flat=True
        ).distinct()
        solicitacoes = SolicitacaoKitLancheCEIAvulsa.objects.filter(
            id__in=solicitacoes_pks
        )
        for solicitacao in solicitacoes:
            escola_periodo = EscolaPeriodoEscolar.objects.get(
                periodo_escolar__nome="INTEGRAL", escola__uuid=solicitacao.escola.uuid
            )
            faixa_alunos = escola_periodo.alunos_por_faixa_etaria(solicitacao.data)
            inclusoes_faixas = solicitacao.faixas_etarias.all()
            for faixa in inclusoes_faixas:
                matriculados_quando_criado = faixa_alunos[faixa.faixa_etaria.uuid]
                faixa.matriculados_quando_criado = matriculados_quando_criado
                uuid = faixa.faixa_etaria.uuid
                self.stdout.write(
                    f"Faixa uuid: {uuid} - matriculados quando criado: {matriculados_quando_criado}"
                )
                faixa.save()
        self.stdout.write("+++ FINALIZANDO KIT LANCHE CEI +++")
