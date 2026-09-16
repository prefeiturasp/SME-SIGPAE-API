"""Configuração do Django Admin do módulo de recebimento."""

import importlib

from django.contrib import admin

from src.recebimento.forms import QuestaoForm
from src.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
    QuestoesPorProduto,
    ReposicaoCronogramaFichaRecebimento,
    VeiculoFichaDeRecebimento,
)

importlib.import_module("src.recebimento.ajuste_saldo_laudo.admin")


@admin.register(QuestaoConferencia)
class QuestaoConferenciaAdmin(admin.ModelAdmin):
    """Admin das questões de conferência.

    Exibe ``questao``, ``tipo_questao``, ``pergunta_obrigatoria``,
    ``posicao`` e ``status``; ordena por posição e criação; busca por texto
    da questão; filtra por tipo e status. ``pergunta_obrigatoria`` e
    ``posicao`` são editáveis na listagem. Usa ``QuestaoForm``, que valida
    a unicidade da posição por tipo de questão.
    """

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
    """Admin das questões por produto.

    Exibe a ficha técnica na listagem e edita as questões primárias e
    secundárias com o widget ``filter_horizontal``.
    """

    list_display = ("ficha_tecnica",)
    filter_horizontal = ("questoes_primarias", "questoes_secundarias")


class VeiculoFichaDeRecebimentoInline(admin.StackedInline):
    """Inline dos veículos da ficha de recebimento."""

    model = VeiculoFichaDeRecebimento
    extra = 0


class ArquivoFichaRecebimentoInline(admin.StackedInline):
    """Inline dos arquivos da ficha de recebimento."""

    model = ArquivoFichaRecebimento
    extra = 0


class QuestaoFichaRecebimentoInline(admin.StackedInline):
    """Inline das respostas às questões da ficha de recebimento."""

    model = QuestaoFichaRecebimento
    extra = 0


class OcorrenciaFichaRecebimentoInline(admin.StackedInline):
    """Inline das ocorrências da ficha de recebimento."""

    model = OcorrenciaFichaRecebimento
    extra = 0


@admin.register(FichaDeRecebimento)
class FichaDeRecebimentoAdmin(admin.ModelAdmin):
    """Admin das fichas de recebimento.

    Exibe a representação textual e a ``data_entrega`` na listagem, com os
    veículos, arquivos, questões e ocorrências editados em inlines.
    """

    list_display = ("__str__", "data_entrega")
    inlines = [
        VeiculoFichaDeRecebimentoInline,
        ArquivoFichaRecebimentoInline,
        QuestaoFichaRecebimentoInline,
        OcorrenciaFichaRecebimentoInline,
    ]


admin.site.register(ReposicaoCronogramaFichaRecebimento)
