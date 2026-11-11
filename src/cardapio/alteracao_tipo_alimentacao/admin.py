from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    DataIntervaloAlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from src.dados_comuns.constants import StringsSearchHelpText


class SubstituicaoAlimentacaoNoPeriodoEscolarInline(admin.TabularInline):
    """Inline do Django para substituições de alimentação no período escolar.

    Exibe e permite editar instâncias de
    :class:`SubstituicaoAlimentacaoNoPeriodoEscolar` diretamente no formulário
    de :class:`AlteracaoCardapio`, incluindo os tipos de alimentação
    substituídos e os substitutos (relações muitos-para-muitos).

    Attributes:
        model (Model): Modelo gerenciado pelo inline.
            Valor: :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`.
        fk_name (str): Campo de ligação com a solicitação.
            Valor: ``"alteracao_cardapio"``.
        extra (int): Número de formulários extras exibidos para novos registros.
            Valor: ``0``.
        autocomplete_fields (tuple[str, ...]): Campos com busca por autocomplete.
            Valores: ``("periodo_escolar", "tipos_alimentacao_de", "tipos_alimentacao_para")``.
        fields (tuple[str, ...]): Campos exibidos no inline.
            Valores: ``("periodo_escolar", "qtd_alunos", "tipos_alimentacao_de", "tipos_alimentacao_para")``.
        show_change_link (bool): Exibe link para a página de edição do registro.
            Valor: ``True``.
    """

    model = SubstituicaoAlimentacaoNoPeriodoEscolar
    fk_name = "alteracao_cardapio"
    extra = 0
    autocomplete_fields = (
        "periodo_escolar",
        "tipos_alimentacao_de",
        "tipos_alimentacao_para",
    )
    fields = (
        "periodo_escolar",
        "qtd_alunos",
        "tipos_alimentacao_de",
        "tipos_alimentacao_para",
    )
    show_change_link = True


class DataIntervaloAlteracaoCardapioInline(admin.TabularInline):
    """Inline do Django para as datas do intervalo da alteração de cardápio.

    Exibe e permite editar instâncias de
    :class:`DataIntervaloAlteracaoCardapio` diretamente no formulário de
    :class:`AlteracaoCardapio`.

    Attributes:
        model (Model): Modelo gerenciado pelo inline.
            Valor: :class:`DataIntervaloAlteracaoCardapio`.
        fk_name (str): Campo de ligação com a solicitação.
            Valor: ``"alteracao_cardapio"``.
        extra (int): Número de formulários extras exibidos para novos registros.
            Valor: ``0``.
        fields (tuple[str, ...]): Campos exibidos no inline.
            Valores: ``("data", "cancelado", "cancelado_justificativa")``.
        show_change_link (bool): Exibe link para a página de edição do registro.
            Valor: ``True``.
    """

    model = DataIntervaloAlteracaoCardapio
    fk_name = "alteracao_cardapio"
    extra = 0
    fields = ("data", "cancelado", "cancelado_justificativa")
    show_change_link = True


@admin.register(AlteracaoCardapio)
class AlteracaoCardapioModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de alteração do tipo de alimentação.

    Configura a listagem administrativa de :class:`AlteracaoCardapio` com
    colunas de escola, lote, DRE, período e status, busca textual por UUID,
    nome e código EOL da escola, filtros por lote, DRE, status e intervalos de
    data. No formulário de edição, os campos de identificação e de conferência
    ficam apenas para leitura e os inlines permitem editar as substituições de
    alimentação por período escolar e as datas do intervalo.

    Attributes:
        inlines (tuple): Inlines exibidos no formulário de edição.
            Valores: ``(SubstituicaoAlimentacaoNoPeriodoEscolarInline, DataIntervaloAlteracaoCardapioInline)``.
        autocomplete_fields (tuple[str, ...]): Campos com busca por autocomplete.
            Valores: ``("escola",)``.
        readonly_fields (tuple[str, ...]): Campos somente leitura no formulário.
            Valores: ``("uuid", "criado_em")``.
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("uuid", "escola", "get_lote", "get_dre", "data_inicial", "data_final", "status")``.
        list_filter (tuple): Filtros laterais disponíveis na listagem.
            Valores: ``(("escola__lote", RelatedOnlyFieldListFilter), ("escola__diretoria_regional", RelatedOnlyFieldListFilter), "status", ("data_inicial", DateRangeFilter), ("data_final", DateRangeFilter))``.
        search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
            Valores: ``("=uuid", "escola__nome", "escola__codigo_eol")``.
        search_help_text (str): Texto auxiliar exibido abaixo do campo de busca.
            Valores: ``"Pesquisar por: UUID, nome da escola, codigo eol da escola"``.
        list_select_related (tuple[str, ...]): Relações carregadas via ``select_related``.
            Valores: ``("escola", "escola__lote", "escola__diretoria_regional")``.
    """

    inlines = (
        SubstituicaoAlimentacaoNoPeriodoEscolarInline,
        DataIntervaloAlteracaoCardapioInline,
    )
    autocomplete_fields = ("escola",)
    readonly_fields = ("uuid", "criado_em")
    list_display = (
        "uuid",
        "escola",
        "get_lote",
        "get_dre",
        "data_inicial",
        "data_final",
        "status",
    )
    list_filter = (
        ("escola__lote", admin.RelatedOnlyFieldListFilter),
        ("escola__diretoria_regional", admin.RelatedOnlyFieldListFilter),
        "status",
        ("data_inicial", DateRangeFilter),
        ("data_final", DateRangeFilter),
    )
    search_fields = ("=uuid", "escola__nome", "escola__codigo_eol")
    search_help_text = (
        StringsSearchHelpText.PESQUISA_POR_UUID_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA.value
    )
    list_select_related = ("escola", "escola__lote", "escola__diretoria_regional")

    @admin.display(description="Lote", ordering="escola__lote__nome")
    def get_lote(self, obj):
        return obj.escola.lote

    @admin.display(description="DRE", ordering="escola__diretoria_regional__nome")
    def get_dre(self, obj):
        return obj.escola.diretoria_regional

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "uuid",
                "status",
                "escola",
                "motivo",
                "data_inicial",
                "data_final",
                "observacao",
                "criado_por",
                "criado_em",
                "foi_solicitado_fora_do_prazo",
                "terceirizada_conferiu_gestao",
            )
        return (
            "escola",
            "motivo",
            "data_inicial",
            "data_final",
            "observacao",
            "criado_por",
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(
                [
                    "escola",
                    "motivo",
                    "status",
                    "criado_por",
                    "foi_solicitado_fora_do_prazo",
                    "terceirizada_conferiu_gestao",
                ]
            )
        return tuple(readonly_fields)


@admin.register(SubstituicaoAlimentacaoNoPeriodoEscolar)
class SubstituicaoAlimentacaoNoPeriodoEscolarAdmin(admin.ModelAdmin):
    """Admin do Django para substituições de alimentação no período escolar.

    Disponibiliza a edição individual de
    :class:`SubstituicaoAlimentacaoNoPeriodoEscolar`, incluindo os tipos de
    alimentação substituídos e os substitutos.

    Attributes:
        autocomplete_fields (tuple[str, ...]): Campos com busca por autocomplete.
            Valores: ``("periodo_escolar", "tipos_alimentacao_de", "tipos_alimentacao_para")``.
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("uuid", "alteracao_cardapio", "periodo_escolar", "qtd_alunos")``.
    """

    autocomplete_fields = (
        "periodo_escolar",
        "tipos_alimentacao_de",
        "tipos_alimentacao_para",
    )
    list_display = ("uuid", "alteracao_cardapio", "periodo_escolar", "qtd_alunos")


@admin.register(DataIntervaloAlteracaoCardapio)
class DataIntervaloAlteracaoCardapioAdmin(admin.ModelAdmin):
    """Admin do Django para as datas do intervalo da alteração de cardápio.

    Disponibiliza a edição individual de
    :class:`DataIntervaloAlteracaoCardapio`, permitindo cancelar pontualmente
    um dia sem invalidar toda a solicitação.

    Attributes:
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("uuid", "alteracao_cardapio", "data", "cancelado")``.
    """

    list_display = ("uuid", "alteracao_cardapio", "data", "cancelado")


admin.site.register(MotivoAlteracaoCardapio)
