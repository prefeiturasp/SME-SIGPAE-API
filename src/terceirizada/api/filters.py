from django_filters import rest_framework as filters


class TerceirizadaFilter(filters.FilterSet):
    modulo = filters.CharFilter(
        field_name="emails_terceirizadas__modulo__nome",
        lookup_expr="icontains",
    )
    dre_uuid = filters.CharFilter(
        field_name="lotes__diretoria_regional__uuid",
        lookup_expr="icontains",
    )
    busca = filters.CharFilter(method="filtrar_empresa")
    tipo_empresa = filters.CharFilter(
        field_name="tipo_empresa", lookup_expr="icontains"
    )

    def filtrar_empresa(self, queryset, name, value):
        return (
            queryset.filter(cnpj__icontains=value)
            | queryset.filter(razao_social__icontains=value)
            | queryset.filter(nome_fantasia__icontains=value)
        )


class EmailTerceirizadaPorModuloFilter(filters.FilterSet):
    modulo = filters.CharFilter(
        field_name="modulo__nome",
        lookup_expr="icontains",
    )


class ContratoFilter(filters.FilterSet):
    busca = filters.CharFilter(method="filtrar_contrato")

    def filtrar_contrato(self, queryset, name, value):
        return (
            queryset.filter(contratos__numero__icontains=value)
            | queryset.filter(contratos__processo__icontains=value)
            | queryset.filter(contratos__edital__numero__icontains=value)
            | queryset.filter(contratos__edital__tipo_contratacao__icontains=value)
        ).distinct()
