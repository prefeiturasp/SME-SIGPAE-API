from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
)


def cria_etapas_de_cronograma(etapas, cronograma=None):
    etapas_criadas = []
    for etapa in etapas:
        etapas_criadas.append(
            EtapasDoCronograma.objects.create(cronograma=cronograma, **etapa)
        )
    return etapas_criadas


def cria_programacao_de_cronograma(programacoes, cronograma=None):
    programacoes_criadas = []
    for programacao in programacoes:
        programacoes_criadas.append(
            ProgramacaoDoRecebimentoDoCronograma.objects.create(
                cronograma=cronograma, **programacao
            )
        )
    return programacoes_criadas


def totalizador_relatorio_cronograma(queryset):
    status_count = {
        CronogramaWorkflow.states[s].title: queryset.filter(status=s).count()
        for s in CronogramaWorkflow.states
    }
    ordered_status_count = dict(
        sorted(status_count.items(), key=lambda e: e[1], reverse=True)
    )
    return ordered_status_count
