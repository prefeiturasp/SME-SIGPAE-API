import datetime
import importlib

from django.contrib import admin

from .models import (
    AlimentacaoLancamentoEspecial,
    CategoriaMedicao,
    ClausulaDeDesconto,
    DiaSobremesaDoce,
    Empenho,
    GrupoMedicao,
    Medicao,
    ParametrizacaoFinanceira,
    ParametrizacaoFinanceiraTabela,
    ParametrizacaoFinanceiraTabelaValor,
    PermissaoLancamentoEspecial,
    RelatorioFinanceiro,
    SolicitacaoMedicaoInicial,
    TipoContagemAlimentacao,
    ValorMedicao,
)

admin.site.register(AlimentacaoLancamentoEspecial)
admin.site.register(CategoriaMedicao)
admin.site.register(DiaSobremesaDoce)
admin.site.register(GrupoMedicao)
admin.site.register(TipoContagemAlimentacao)


@admin.register(SolicitacaoMedicaoInicial)
class SolicitacaoMedicaoInicialAdmin(admin.ModelAdmin):
    list_display = ("id_externo", "escola", "mes", "ano", "criado_em", "status")
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = ("mes", "ano", "status")


@admin.register(Medicao)
class MedicaoAdmin(admin.ModelAdmin):
    list_display = (
        "get_escola",
        "get_mes",
        "get_ano",
        "periodo_escolar",
        "grupo",
        "get_uuid_sol_medicao",
        "criado_em",
        "status",
    )
    search_fields = (
        "solicitacao_medicao_inicial__escola__nome",
        "solicitacao_medicao_inicial__escola__codigo_eol",
    )
    list_filter = (
        "periodo_escolar__nome",
        "grupo",
        "solicitacao_medicao_inicial__mes",
        "solicitacao_medicao_inicial__ano",
        "status",
    )

    @admin.display(description="Solicitação Medição Inicial")
    def get_uuid_sol_medicao(self, obj):
        return obj.solicitacao_medicao_inicial.id_externo

    @admin.display(description="Escola")
    def get_escola(self, obj):
        return f"{obj.solicitacao_medicao_inicial.escola.codigo_eol}: {obj.solicitacao_medicao_inicial.escola.nome}"

    @admin.display(description="Mês")
    def get_mes(self, obj):
        return obj.solicitacao_medicao_inicial.mes

    @admin.display(description="Ano")
    def get_ano(self, obj):
        return obj.solicitacao_medicao_inicial.ano


@admin.register(PermissaoLancamentoEspecial)
class PermissaoLancamentoEspecialAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "periodo_escolar",
        "get_data_inicial",
        "get_data_final",
        "diretoria_regional",
        "get_alimentacoes_lancamento_especial",
        "alterado_em",
    )
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = ("diretoria_regional",)

    @admin.display(description="Alimentações Lançamento Especial")
    def get_alimentacoes_lancamento_especial(self, obj):
        return [ali.nome for ali in obj.alimentacoes_lancamento_especial.all()]

    @admin.display(description="Data Inicial")
    def get_data_inicial(self, obj):
        return (
            datetime.date.strftime(obj.data_inicial, "%d/%m/%Y")
            if obj.data_inicial
            else "-"
        )

    @admin.display(description="Data Final")
    def get_data_final(self, obj):
        return (
            datetime.date.strftime(obj.data_final, "%d/%m/%Y")
            if obj.data_final
            else "-"
        )


@admin.register(ValorMedicao)
class ValorMedicaoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "valor",
        "medicao",
        "get_escola",
        "faixa_etaria",
        "infantil_ou_fundamental",
    )
    search_fields = (
        "valor",
        "medicao__solicitacao_medicao_inicial__escola__nome",
        "medicao__solicitacao_medicao_inicial__escola__codigo_eol",
    )
    list_filter = (
        "medicao__solicitacao_medicao_inicial__mes",
        "medicao__solicitacao_medicao_inicial__ano",
        "medicao__periodo_escolar__nome",
        "medicao__grupo",
        "categoria_medicao",
        "nome_campo",
        "infantil_ou_fundamental",
    )

    @admin.display(description="Escola")
    def get_escola(self, obj):
        escola = obj.medicao.solicitacao_medicao_inicial.escola
        return f"{escola.codigo_eol}: {escola.nome}"


@admin.register(Empenho)
class EmpenhoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "contrato", "edital", "status", "alterado_em")
    search_fields = ("numero",)
    list_filter = ("alterado_em", "status")
    ordering = ("-alterado_em",)


@admin.register(ClausulaDeDesconto)
class ClausulaDeDescontoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "porcentagem_desconto", "criado_em", "alterado_em")
    search_fields = ("edital__numero", "numero_clausula", "item_clausula")
    list_filter = ("alterado_em",)
    ordering = ("-alterado_em",)


@admin.register(ParametrizacaoFinanceira)
class ParametrizacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("edital", "lote", "get_tipos_unidades")
    search_fields = (
        "edital__numero",
        "lote__nome",
        "grupo_unidade_escolar__tipos_unidades__iniciais",
    )
    list_filter = (
        "edital__numero",
        "lote__nome",
        "grupo_unidade_escolar__tipos_unidades__iniciais",
    )

    @admin.display(description="Tipo Unidade")
    def get_tipos_unidades(self, obj):
        return ", ".join(
            [
                tipo_unidade.iniciais
                for tipo_unidade in obj.grupo_unidade_escolar.tipos_unidades.all()
            ]
        )


@admin.register(ParametrizacaoFinanceiraTabela)
class ParametrizacaoFinanceiraTabelaAdmin(admin.ModelAdmin):
    list_display = ("nome", "periodo_escolar", "parametrizacao_financeira")
    search_fields = ("nome", "periodo_escolar")
    list_filter = ("nome", "periodo_escolar")


@admin.register(ParametrizacaoFinanceiraTabelaValor)
class ParametrizacaoFinanceiraTabelaValorAdmin(admin.ModelAdmin):
    list_display = (
        "tabela",
        "nome_campo",
        "tipo_alimentacao",
        "faixa_etaria",
        "tipo_valor",
        "valor",
    )
    search_fields = ("tabela", "tipo_alimentacao__nome", "tipo_valor")
    list_filter = ("tabela", "tipo_alimentacao__nome", "tipo_valor", "faixa_etaria")


@admin.register(RelatorioFinanceiro)
class RelatorioFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("__str__", "grupo_unidade_escolar")


importlib.import_module("sme_sigpae_api.medicao_inicial.recreio_nas_ferias.admin")
