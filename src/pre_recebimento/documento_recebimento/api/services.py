from src.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
)
from src.dados_comuns.fluxo_status import (
    DocumentoDeRecebimentoWorkflow,
)
from src.pre_recebimento.base.api.services import BaseServiceDashboard


class ServiceDashboardDocumentosDeRecebimento(BaseServiceDashboard):
    STATUS_POR_PERFIL = {
        DILOG_QUALIDADE: [
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
            DocumentoDeRecebimentoWorkflow.APROVADO,
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
        ],
        COORDENADOR_CODAE_DILOG_LOGISTICA: [
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
            DocumentoDeRecebimentoWorkflow.APROVADO,
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
        ],
        DILOG_CRONOGRAMA: [
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
            DocumentoDeRecebimentoWorkflow.APROVADO,
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
        ],
        ADMINISTRADOR_CODAE_GABINETE: [
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
            DocumentoDeRecebimentoWorkflow.APROVADO,
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
        ],
        DILOG_DIRETORIA: [
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_ANALISE,
            DocumentoDeRecebimentoWorkflow.APROVADO,
            DocumentoDeRecebimentoWorkflow.ENVIADO_PARA_CORRECAO,
        ],
    }
