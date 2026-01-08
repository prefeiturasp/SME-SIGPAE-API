from django_filters import rest_framework as filters


class DiaParaCorrecaoFilter(filters.FilterSet):
    uuid_solicitacao_medicao = filters.CharFilter(
        field_name="medicao__solicitacao_medicao_inicial__uuid", lookup_expr="iexact"
    )
    nome_grupo = filters.CharFilter(
        field_name="medicao__grupo__nome", lookup_expr="iexact"
    )
    nome_periodo_escolar = filters.CharFilter(
        field_name="medicao__periodo_escolar__nome", lookup_expr="iexact"
    )


class EmpenhoFilter(filters.FilterSet):
    numero = filters.CharFilter(field_name="numero", lookup_expr="icontains")
    contrato = filters.UUIDFilter(method="filtra_contrato")
    edital = filters.UUIDFilter(method="filtra_edital")

    def filtra_contrato(self, queryset, _, value):
        return queryset.filter(contrato__uuid=value)

    def filtra_edital(self, queryset, _, value):
        return queryset.filter(contrato__edital__uuid=value)


class ClausulaDeDescontoFilter(filters.FilterSet):
    numero_clausula = filters.CharFilter(
        field_name="numero_clausula", lookup_expr="icontains"
    )
    porcentagem_desconto = filters.NumberFilter(
        field_name="porcentagem_desconto", lookup_expr="exact"
    )
    edital = filters.UUIDFilter(method="filtra_edital")

    def filtra_edital(self, queryset, _, value):
        return queryset.filter(edital__uuid=value)


class ParametrizacaoFinanceiraFilter(filters.FilterSet):
    lote = filters.UUIDFilter(field_name="lote__uuid")
    tipos_unidades = filters.CharFilter(method="filtra_tipos_unidades")
    edital = filters.UUIDFilter(field_name="edital__uuid")

    def filtra_tipos_unidades(self, queryset, _, value):
        tipos_unidades_uuids = value.split(",")
        return queryset.filter(
            grupo_unidade_escolar__tipos_unidades__uuid__in=tipos_unidades_uuids
        ).distinct()


class RelatorioFinanceiroFilter(filters.FilterSet):
    lote = filters.CharFilter(method="filtra_lotes")
    grupo_unidade_escolar = filters.CharFilter(method="filtra_grupos")
    mes_ano = filters.CharFilter(method="filtra_mes_ano")
    status = filters.CharFilter(method="filtra_status")

    def filtra_mes_ano(self, queryset, _, value):
        mes, ano = value.split("_")
        return queryset.filter(mes=mes, ano=ano)

    def filtra_lotes(self, queryset, _, value):
        uuids = value.split(",")
        return queryset.filter(lote__uuid__in=uuids)
    
    def filtra_grupos(self, queryset, _, value):
        uuids = value.split(",")
        return queryset.filter(grupo_unidade_escolar__uuid__in=uuids)

    def filtra_status(self, queryset, _, value):
        values = value.split(",")
        return queryset.filter(status__in=values)


class SolicitacaoMedicaoInicialFilter(filters.FilterSet):
    escola_uuid = filters.CharFilter(field_name="escola__uuid", lookup_expr="iexact")
    mes = filters.CharFilter(field_name="mes", lookup_expr="iexact")
    ano = filters.CharFilter(field_name="ano", lookup_expr="iexact")
    recreio_nas_ferias = filters.CharFilter(
        field_name="recreio_nas_ferias__uuid", lookup_expr="iexact"
    )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if not self.data:
            return queryset

        if "recreio_nas_ferias" not in self.data:
            queryset = queryset.filter(recreio_nas_ferias__isnull=True)

        return queryset
