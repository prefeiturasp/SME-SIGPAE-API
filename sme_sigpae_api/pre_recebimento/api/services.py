from typing import Type

from django.db.models import QuerySet, Value
from django_filters.rest_framework import FilterSet
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer

from sme_sigpae_api.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_PRODUTO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_GESTAO_PRODUTO,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    USUARIO_EMPRESA,
)
from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaAlteracaoWorkflow,
    DocumentoDeRecebimentoWorkflow,
    FichaTecnicaDoProdutoWorkflow,
    LayoutDeEmbalagemWorkflow,
)
from sme_sigpae_api.pre_recebimento.models.cronograma import (
    SolicitacaoAlteracaoCronograma,
)


class BaseServiceDashboard:
    STATUS_POR_PERFIL = {}

    def __init__(
        self,
        original_queryset: QuerySet,
        filter_class: Type[FilterSet],
        serializer_class: Type[ModelSerializer],
        request: Request,
    ) -> None:
        """
        Service Base que deve ser extendido para lidar com perfis e os diferentes status dos cards dos dashboards.

        Na sua implementação concreta do Service, sobreescreva o dicionário STATUS_POR_PERFIL com um mapeamento
        dos perfils e os respectivos status dos cards desejados.

        Exemplo:

        STATUS_POR_PERFIL = {
            PERFIL_A: [
                'EM_ANALISE',
                'APROVADO',
                'REPROVADO',
            ],
            PERFIL_B: [
                'EM_ANALISE',
                'SOLICITADO_CORRECAO',
            ],
            PERFIL_C: [
                'APROVADO',
                'REPROVADO',
            ],
        }
        """
        self.original_queryset = original_queryset
        self.filter_class = filter_class
        self.serializer_class = serializer_class
        self.request = request

    @classmethod
    def get_dashboard_status(cls, user) -> list:
        perfil = user.vinculo_atual.perfil.nome

        if perfil not in cls.STATUS_POR_PERFIL:
            raise ValueError("Perfil não existe")

        return cls.STATUS_POR_PERFIL[perfil]

    def get_dados_dashboard(self) -> list:
        lista_status_ver_mais = self.request.query_params.getlist("status", None)
        offset = int(self.request.query_params.get("offset", 0))
        limit = int(self.request.query_params.get("limit", 6))

        filtered_queryset = self.filter_class(
            self.request.query_params, self.original_queryset
        ).qs

        if lista_status_ver_mais:
            dados = self._get_dados_ver_mais(
                filtered_queryset, lista_status_ver_mais, offset, limit
            )

        else:
            dados = self._get_dados_cards(filtered_queryset, offset, limit)

        return dados

    def _get_dados_ver_mais(self, queryset_base, lista_status_ver_mais, offset, limit):
        qs = queryset_base.filter(status__in=lista_status_ver_mais)
        dados = {
            "status": lista_status_ver_mais,
            "total": len(qs),
            "dados": self.serializer_class(qs[offset : offset + limit], many=True).data,
        }

        return dados

    def _get_dados_cards(self, queryset_base, offset, limit):
        dados = []
        for status_perfil in self.get_dashboard_status(self.request.user):
            status_perfil_list = [status_perfil]
            qs = queryset_base.filter(status__in=status_perfil_list)
            dados.append(
                {
                    "status": status_perfil,
                    "dados": self.serializer_class(
                        qs[offset : offset + limit], many=True
                    ).data,
                }
            )

        return dados


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
    }


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
