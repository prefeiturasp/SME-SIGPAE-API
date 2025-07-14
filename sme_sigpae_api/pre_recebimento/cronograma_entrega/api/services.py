from django.db.models import Value
from rest_framework.request import Request

from sme_sigpae_api.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_EMPRESA,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_VISUALIZACAO,
    USUARIO_EMPRESA,
)
from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaAlteracaoWorkflow,
)
from sme_sigpae_api.pre_recebimento.base.api.services import BaseServiceDashboard
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    SolicitacaoAlteracaoCronograma,
)


class ServiceDashboardSolicitacaoAlteracaoCronogramaProfiles(BaseServiceDashboard):
    STATUS_POR_PERFIL = {
        DILOG_ABASTECIMENTO: [
            CronogramaAlteracaoWorkflow.CRONOGRAMA_CIENTE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG_ABASTECIMENTO,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG_ABASTECIMENTO,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
        DILOG_DIRETORIA: [
            CronogramaAlteracaoWorkflow.APROVADO_DILOG_ABASTECIMENTO,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG_ABASTECIMENTO,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
        DILOG_CRONOGRAMA: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
        COORDENADOR_CODAE_DILOG_LOGISTICA: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
        ADMINISTRADOR_CODAE_GABINETE: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
        DILOG_VISUALIZACAO: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
            CronogramaAlteracaoWorkflow.APROVADO_DILOG,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG,
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
            CronogramaAlteracaoWorkflow.FORNECEDOR_CIENTE,
        ],
    }


class ServiceQuerysetAlteracaoCronograma:
    STATUS_PRIORITARIO = {
        ADMINISTRADOR_EMPRESA: [
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
        ],
        USUARIO_EMPRESA: [
            CronogramaAlteracaoWorkflow.ALTERACAO_ENVIADA_FORNECEDOR,
        ],
        COORDENADOR_CODAE_DILOG_LOGISTICA: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
        ],
        DILOG_CRONOGRAMA: [
            CronogramaAlteracaoWorkflow.EM_ANALISE,
        ],
        DILOG_DIRETORIA: [
            CronogramaAlteracaoWorkflow.APROVADO_DILOG_ABASTECIMENTO,
            CronogramaAlteracaoWorkflow.REPROVADO_DILOG_ABASTECIMENTO,
        ],
        DILOG_ABASTECIMENTO: [
            CronogramaAlteracaoWorkflow.CRONOGRAMA_CIENTE,
        ],
        DILOG_VISUALIZACAO: [],
    }

    def __init__(
        self,
        request: Request,
    ) -> None:
        self.request = request

    @classmethod
    def get_status(self, user) -> list:
        perfil = user.vinculo_atual.perfil.nome

        if perfil not in self.STATUS_PRIORITARIO:
            raise ValueError("Perfil não existe")

        return self.STATUS_PRIORITARIO[perfil]

    def get_queryset(self, filter=False):
        user = self.request.user
        lista_status = self.get_status(user)
        q1 = SolicitacaoAlteracaoCronograma.objects.filter(
            status__in=lista_status,
        ).annotate(ordem=Value(1))
        q2 = SolicitacaoAlteracaoCronograma.objects.exclude(
            status__in=lista_status,
        ).annotate(ordem=Value(2))

        if user.eh_fornecedor:
            q1 = q1.filter(cronograma__empresa=user.vinculo_atual.instituicao)
            q2 = q2.filter(cronograma__empresa=user.vinculo_atual.instituicao)

        if filter:
            q1 = filter(q1)
            q2 = filter(q2)

        return q1.union(q2, all=True).order_by("ordem", "-criado_em")
