from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Alimento,
    ConferenciaGuia,
    Embalagem,
    Guia,
    LogSolicitacaoDeCancelamentoPeloPapa,
    NotificacaoOcorrenciasGuia,
    PrevisaoContratualNotificacao,
    SolicitacaoDeAlteracaoRequisicao,
    SolicitacaoRemessa,
    TipoEmbalagem,
)
from .models.guia import ConferenciaIndividualPorAlimento, InsucessoEntregaGuia
from .services import cancelar_guias, inativa_tipos_de_embabalagem


class GuiaInline(admin.StackedInline):
    model = Guia
    extra = 1  # Quantidade de linhas que serão exibidas.
    show_change_link = True


class AlimentoInline(admin.TabularInline):
    model = Alimento
    extra = 1  # Quantidade de linhas que serão exibidas.


@admin.register(SolicitacaoRemessa)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ("cnpj", "numero_solicitacao", "status", "get_situacao", "get_guias")
    ordering = ("-alterado_em",)
    search_fields = ("numero_solicitacao",)
    list_filter = ("status",)
    readonly_fields = ("uuid",)
    inlines = [GuiaInline]

    def get_guias(self, obj):
        return ", ".join([guias.numero_guia for guias in obj.guias.all()])

    get_guias.short_description = "Guias"

    def get_situacao(self, obj):
        color = "green"
        if obj.situacao == "ARQUIVADA":
            color = "red"
        return format_html(
            f'<div style="width:80px; color:white; text-align:center; background:{color}; '
            f'border-radius:5px;">{obj.get_situacao_display()}</div>'
        )

    get_situacao.short_description = "Situação Da Solicitacão"


@admin.register(Guia)
class GuiaAdmin(admin.ModelAdmin):
    list_display = (
        "get_cnpj",
        "get_solicitacao",
        "get_status_solicitacao",
        "numero_guia",
        "get_situacao",
        "data_entrega",
        "codigo_unidade",
        "nome_unidade",
        "status",
    )
    search_fields = (
        "numero_guia",
        "solicitacao__numero_solicitacao",
        "nome_unidade",
        "codigo_unidade",
    )
    list_filter = ("status",)
    ordering = ("-alterado_em",)
    readonly_fields = ("uuid",)
    inlines = [AlimentoInline]
    actions = ["cancelar_guias"]

    def get_situacao(self, obj):
        color = "green"
        if obj.situacao == "ARQUIVADA":
            color = "red"
        return format_html(
            f'<div style="width:80px; color:white; text-align:center; background:{color}; '
            f'border-radius:5px;">{obj.get_situacao_display()}</div>'
        )

    get_situacao.short_description = "Situação Guia"

    def get_cnpj(self, obj):
        return obj.solicitacao.cnpj

    get_cnpj.short_description = "CNPJ Armazem"

    def get_solicitacao(self, obj):
        return obj.solicitacao.numero_solicitacao

    get_solicitacao.short_description = "Número Solicitação"

    def get_status_solicitacao(self, obj):
        return obj.solicitacao.get_status_display()

    get_status_solicitacao.short_description = "Status da Solicitação"

    def cancelar_guias(self, request, queryset):
        cancelar_guias(queryset)

    cancelar_guias.short_description = "Realizar Cancelamento"


@admin.register(TipoEmbalagem)
class TipoEmbalagemAdmin(admin.ModelAdmin):
    list_display = ("get_tipo",)
    actions = ["inativa_embalagens"]

    def get_tipo(self, obj):
        return f"{obj.sigla} - {obj.descricao}"

    get_tipo.short_description = "Tipo de embalagem"

    def inativa_embalagens(self, request, queryset):
        inativa_tipos_de_embabalagem(queryset)
        self.message_user(request, "Tipos de embalagens inativadas.")

    inativa_embalagens.short_description = "Inativar Tipos de Embalagens"

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Embalagem)
class EmbalagemAdmin(admin.ModelAdmin):
    list_display = (
        "get_guia",
        "get_alimento",
        "descricao_embalagem",
        "capacidade_embalagem",
        "unidade_medida",
        "tipo_embalagem",
    )
    search_fields = (
        "descricao_embalagem",
        "capacidade_embalagem",
        "unidade_medida",
        "tipo_embalagem",
    )
    ordering = ("-alterado_em",)

    def has_change_permission(self, request, obj=None):
        return False

    def get_alimento(self, obj):
        return obj.alimento.nome_alimento

    get_alimento.short_description = "Nome do Alimento"

    def get_guia(self, obj):
        return obj.alimento.guia.numero_guia

    get_guia.short_description = "Número da Guia"


@admin.register(SolicitacaoDeAlteracaoRequisicao)
class SolicitacaoDeAlteracaoRequisicaoAdmin(admin.ModelAdmin):
    list_display = ("numero_solicitacao", "motivos")
    search_fields = ("numero_solicitacao",)
    list_filter = ("motivo",)
    readonly_fields = (
        "numero_solicitacao",
        "motivo",
        "requisicao",
        "usuario_solicitante",
        "criado_em",
        "justificativa",
    )

    def motivos(self, obj):
        return obj.get_motivo_display()


@admin.register(ConferenciaGuia)
class ConferenciaGuiaAdmin(admin.ModelAdmin):
    list_display = ("get_guia", "data_recebimento", "eh_reposicao")
    search_fields = ("guia__numero_guia",)
    readonly_fields = ("criado_em",)

    def get_guia(self, obj):
        return obj.guia.numero_guia

    get_guia.short_description = "Número Guia"


@admin.register(ConferenciaIndividualPorAlimento)
class ConferenciaIndividualPorAlimentoAdmin(admin.ModelAdmin):
    list_display = ("nome_alimento",)


@admin.register(InsucessoEntregaGuia)
class InsucessoEntregaGuiaAdmin(admin.ModelAdmin):
    list_display = ("get_guia", "get_data_tentativa")
    search_fields = ("guia__numero_guia",)
    readonly_fields = ("criado_em",)

    def get_guia(self, obj):
        return obj.guia.numero_guia

    get_guia.short_description = "Número Guia"

    def get_data_tentativa(self, obj):
        return obj.guia.data_entrega

    get_data_tentativa.short_description = "Data Tentativa da Entrega"


@admin.register(LogSolicitacaoDeCancelamentoPeloPapa)
class LogSolicitacaoDeCancelamentoPeloPapaAdmin(admin.ModelAdmin):
    def get_requisicao(self, obj):
        return obj.requisicao.numero_solicitacao

    get_requisicao.short_description = "Número Solicitação"
    list_display = ("get_requisicao", "sequencia_envio", "foi_confirmada", "criado_em")
    readonly_fields = (
        "requisicao",
        "guias",
        "sequencia_envio",
        "criado_em",
        "alterado_em",
        "foi_confirmada",
    )


class PrevisaoInline(admin.TabularInline):
    model = PrevisaoContratualNotificacao
    extra = 1  # Quantidade de linhas que serão exibidas.


@admin.register(NotificacaoOcorrenciasGuia)
class NotificacaoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("numero", "status", "processo_sei", "get_guias")
    ordering = ("-alterado_em",)
    search_fields = ("numero",)
    list_filter = ("status",)
    readonly_fields = ("uuid",)
    inlines = [GuiaInline, PrevisaoInline]

    def get_guias(self, obj):
        return ", ".join([guias.numero_guia for guias in obj.guias_notificadas.all()])

    get_guias.short_description = "Guias"
