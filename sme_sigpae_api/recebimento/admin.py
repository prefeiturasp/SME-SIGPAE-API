from django.contrib import admin

from sme_sigpae_api.recebimento.forms import QuestaoForm
from sme_sigpae_api.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
    QuestoesPorProduto,
    VeiculoFichaDeRecebimento,
)


@admin.register(QuestaoConferencia)
class QuestaoConferenciaAdmin(admin.ModelAdmin):
    form = QuestaoForm
    list_display = (
        "questao",
        "tipo_questao",
        "pergunta_obrigatoria",
        "posicao",
        "status",
    )
    ordering = (
        "posicao",
        "criado_em",
    )
    search_fields = ("questao",)
    list_filter = (
        "tipo_questao",
        "status",
    )
    list_editable = ("pergunta_obrigatoria", "posicao")
    readonly_fields = ("uuid",)


@admin.register(QuestoesPorProduto)
class QuestoesPorProdutoAdmin(admin.ModelAdmin):
    list_display = ("ficha_tecnica",)
    filter_horizontal = ("questoes_primarias", "questoes_secundarias")


class VeiculoFichaDeRecebimentoInline(admin.StackedInline):
    model = VeiculoFichaDeRecebimento
    extra = 0


class ArquivoFichaRecebimentoInline(admin.StackedInline):
    model = ArquivoFichaRecebimento
    extra = 0


class QuestaoFichaRecebimentoInline(admin.StackedInline):
    model = QuestaoFichaRecebimento
    extra = 0


class OcorrenciaFichaRecebimentoInline(admin.StackedInline):
    model = OcorrenciaFichaRecebimento
    extra = 0


@admin.register(FichaDeRecebimento)
class FichaDeRecebimentoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "data_entrega")
    inlines = [
        VeiculoFichaDeRecebimentoInline,
        ArquivoFichaRecebimentoInline,
        QuestaoFichaRecebimentoInline,
        OcorrenciaFichaRecebimentoInline,
    ]
