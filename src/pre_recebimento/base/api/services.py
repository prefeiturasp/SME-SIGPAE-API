"""Serviços da API do submódulo base de pré-recebimento.

Este módulo concentra serviços compartilhados pelos submódulos de
pré-recebimento, como o ``BaseServiceDashboard`` usado na montagem dos
dados dos dashboards por perfil e status.
"""

from typing import Type

from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer


class BaseServiceDashboard:
    """Service base para montagem dos dados dos dashboards.

    Deve ser estendido pelos serviços concretos dos submódulos. Na
    implementação, sobrescreva ``STATUS_POR_PERFIL`` com o mapeamento dos
    perfis e os respectivos status exibidos nos cards do dashboard.
    """

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
        """Retorna a lista de status exibidos para o perfil do usuário.

        Args:
            user: Usuário autenticado.

        Returns:
            Lista de status (strings) configurados em ``STATUS_POR_PERFIL``
            para o perfil do vínculo atual do usuário.

        Raises:
            ValueError: Se o perfil não estiver mapeado em
                ``STATUS_POR_PERFIL``.
        """
        perfil = user.vinculo_atual.perfil.nome

        if perfil not in cls.STATUS_POR_PERFIL:
            raise ValueError("Perfil não existe")

        return cls.STATUS_POR_PERFIL[perfil]

    def get_dados_dashboard(self) -> list:
        """Monta os dados do dashboard.

        Se houver o parâmetro ``status`` na query string, retorna os dados
        da visualização "ver mais" para os status informados; caso
        contrário, retorna os dados agrupados por status (cards) conforme
        o perfil do usuário.

        Returns:
            Lista de dicionários com os dados do dashboard.
        """
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
        """Monta os dados da visualização "ver mais" por status.

        Args:
            queryset_base: QuerySet já filtrado.
            lista_status_ver_mais: Lista de status solicitados.
            offset: Deslocamento para paginação.
            limit: Limite de registros.

        Returns:
            Dicionário com ``status``, ``total`` e ``dados`` serializados.
        """
        qs = queryset_base.filter(status__in=lista_status_ver_mais)
        dados = {
            "status": lista_status_ver_mais,
            "total": len(qs),
            "dados": self.serializer_class(qs[offset : offset + limit], many=True).data,
        }

        return dados

    def _get_dados_cards(self, queryset_base, offset, limit):
        """Monta os dados dos cards do dashboard por status.

        Para cada status configurado para o perfil do usuário, filtra o
        queryset e serializa os registros.

        Args:
            queryset_base: QuerySet já filtrado.
            offset: Deslocamento para paginação.
            limit: Limite de registros.

        Returns:
            Lista de dicionários com ``status`` e ``dados`` serializados.
        """
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
