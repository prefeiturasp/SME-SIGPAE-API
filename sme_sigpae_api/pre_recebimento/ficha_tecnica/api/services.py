
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
    FichaTecnicaDoProdutoWorkflow,
)
from sme_sigpae_api.pre_recebimento.base.api.services import BaseServiceDashboard


class ServiceDashboardFichaTecnica(BaseServiceDashboard):
    STATUS_POR_PERFIL = {
        COORDENADOR_GESTAO_PRODUTO: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        ADMINISTRADOR_GESTAO_PRODUTO: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        COORDENADOR_CODAE_DILOG_LOGISTICA: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        ADMINISTRADOR_CODAE_GABINETE: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        DILOG_DIRETORIA: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        DILOG_QUALIDADE: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        DILOG_ABASTECIMENTO: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
        DILOG_CRONOGRAMA: [
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
            FichaTecnicaDoProdutoWorkflow.APROVADA,
            FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        ],
    }

