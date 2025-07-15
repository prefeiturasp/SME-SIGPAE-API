from sme_sigpae_api.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_GESTAO_PRODUTO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_GESTAO_PRODUTO,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
)
from sme_sigpae_api.dados_comuns.fluxo_status import (
    LayoutDeEmbalagemWorkflow,
)
from sme_sigpae_api.pre_recebimento.base.api.services import BaseServiceDashboard


class ServiceDashboardLayoutEmbalagem(BaseServiceDashboard):
    STATUS_POR_PERFIL = {
        COORDENADOR_CODAE_DILOG_LOGISTICA: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        DILOG_QUALIDADE: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        COORDENADOR_GESTAO_PRODUTO: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        ADMINISTRADOR_GESTAO_PRODUTO: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        ADMINISTRADOR_CODAE_GABINETE: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        DILOG_DIRETORIA: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        DILOG_ABASTECIMENTO: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
        DILOG_CRONOGRAMA: [
            LayoutDeEmbalagemWorkflow.ENVIADO_PARA_ANALISE,
            LayoutDeEmbalagemWorkflow.APROVADO,
            LayoutDeEmbalagemWorkflow.SOLICITADO_CORRECAO,
        ],
    }
