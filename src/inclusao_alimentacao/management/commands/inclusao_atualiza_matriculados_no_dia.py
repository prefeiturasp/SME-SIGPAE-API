from django.core.management.base import BaseCommand

from src.escola.models import EscolaPeriodoEscolar
from src.inclusao_alimentacao.models import (
    InclusaoAlimentacaoDaCEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
)


class Command(BaseCommand):
    help = """
    Popular coluna matriculados_quando_criado com base na data das solicitações de inclusao.
    """

    def handle(self, *args, **options):
        self.stdout.write("Iniciando processo de popular matriculados_quando_criado.")
        self.popular_inclusao_cei()

    def popular_inclusao_cei(self):
        self.stdout.write("+++ INICIANDO INCLUSAO CEI +++")
        class_inclusao = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI
        solicitacoes_pks = class_inclusao.objects.filter(
            matriculados_quando_criado=None
        )
        solicitacoes_pks = solicitacoes_pks.values_list(
            "inclusao_alimentacao_da_cei", flat=True
        ).distinct()
        solicitacoes = InclusaoAlimentacaoDaCEI.objects.filter(id__in=solicitacoes_pks)
        for solicitacao in solicitacoes:
            escola_periodo = EscolaPeriodoEscolar.objects.get(
                periodo_escolar__nome="INTEGRAL", escola__uuid=solicitacao.escola.uuid
            )
            faixa_alunos = escola_periodo.alunos_por_faixa_etaria(solicitacao.data)
            inclusoes_faixas = solicitacao.quantidade_alunos_da_inclusao.all()
            for faixa in inclusoes_faixas:
                matriculados_quando_criado = faixa_alunos[faixa.faixa_etaria.uuid]
                faixa.matriculados_quando_criado = matriculados_quando_criado
                uuid = faixa.faixa_etaria.uuid
                qtd = matriculados_quando_criado
                self.stdout.write(
                    f"Faixa uuid: {uuid} - matriculados quando criado: {qtd}"
                )
                faixa.save()
        self.stdout.write("+++ FINALIZANDO INCLUSAO CEI +++")
