from django_filters import rest_framework as filters

from ..models import Notificacao
from ..models import PerguntaFrequente


class NotificacaoFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    tipo = filters.MultipleChoiceFilter(
        field_name="tipo",
        choices=[(str(state), state) for state in Notificacao.TIPO_NOTIFICACAO_NOMES],
    )
    categoria = filters.CharFilter(
        field_name="categoria",
        lookup_expr="icontains",
    )
    data_inicial = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="lte",
    )
    lido = filters.BooleanFilter(field_name="lido")


class CentralDeDownloadFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    identificador = filters.CharFilter(
        field_name="identificador",
        lookup_expr="exact",
    )
    status = filters.CharFilter(
        field_name="status",
        lookup_expr="exact",
    )
    data_geracao = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="exact",
    )
    visto = filters.BooleanFilter(field_name="visto")


class ListaCharFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class PerguntaFrequenteFilter(filters.FilterSet):
    titulo = filters.CharFilter(
        field_name="pergunta",
        lookup_expr="icontains",
    )
    categoria = filters.UUIDFilter(
        field_name="categoria__uuid",
    )
    perfil = ListaCharFilter(
        method="filtrar_perfis",
    )

    def filtrar_perfis(self, queryset, _name, value):
        if not value:
            return queryset

        if "todos" in value:
            return queryset.filter(todos_os_perfis=True)

        return queryset.filter(
            perfis__uuid__in=value
        ).distinct()

    class Meta:
        model = PerguntaFrequente
        fields = []
