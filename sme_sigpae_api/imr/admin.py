from django import forms
from django.contrib import admin, messages
from django.urls import path
from rangefilter.filters import DateRangeFilter

from sme_sigpae_api.dados_comuns.behaviors import PerfilDiretorSupervisao
from sme_sigpae_api.dados_comuns.utils import custom_titled_filter
from sme_sigpae_api.imr.api.services import (
    exportar_planilha_importacao_tipos_ocorrencia,
    exportar_planilha_importacao_tipos_penalidade,
)
from sme_sigpae_api.imr.models import (
    AnexosFormularioBase,
    CategoriaOcorrencia,
    EditalEquipamento,
    EditalInsumo,
    EditalMobiliario,
    EditalReparoEAdaptacao,
    EditalUtensilioCozinha,
    EditalUtensilioMesa,
    Equipamento,
    FaixaPontuacaoIMR,
    FormularioDiretor,
    FormularioOcorrenciasBase,
    FormularioSupervisao,
    ImportacaoPlanilhaTipoOcorrencia,
    ImportacaoPlanilhaTipoPenalidade,
    Insumo,
    Mobiliario,
    NotificacoesAssinadasFormularioBase,
    ObrigacaoPenalidade,
    OcorrenciaNaoSeAplica,
    ParametrizacaoOcorrencia,
    PeriodoVisita,
    ReparoEAdaptacao,
    RespostaCampoNumerico,
    RespostaCampoTextoLongo,
    RespostaCampoTextoSimples,
    RespostaDatas,
    RespostaEquipamento,
    RespostaFaixaEtaria,
    RespostaInsumo,
    RespostaMobiliario,
    RespostaPeriodo,
    RespostaReparoEAdaptacao,
    RespostaSimNao,
    RespostaSimNaoNaoSeAplica,
    RespostaTipoAlimentacao,
    RespostaUtensilioCozinha,
    RespostaUtensilioMesa,
    TipoGravidade,
    TipoOcorrencia,
    TipoPenalidade,
    TipoPerguntaParametrizacaoOcorrencia,
    TipoRespostaModelo,
    UtensilioCozinha,
    UtensilioMesa,
)
from utility.carga_dados.imr.importa_dados import (
    importa_tipos_ocorrencia,
    importa_tipos_penalidade,
)
from utility.carga_dados.perfil.importa_dados import valida_arquivo_importacao_usuarios


class ObrigacaoPenalidadeInline(admin.StackedInline):
    model = ObrigacaoPenalidade
    extra = 1  # Quantidade de linhas que serão exibidas.
    show_change_link = True


@admin.register(TipoPenalidade)
class TipoPenalidadeAdmin(admin.ModelAdmin):
    list_display = (
        "edital",
        "numero_clausula",
        "gravidade",
        "status",
    )
    ordering = ("criado_em",)
    search_fields = ("numero_clausula",)
    search_help_text = "Pesquise por: número da cláusula"
    list_filter = (
        "edital",
        "gravidade",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "criado_por", "alterado_em")
    autocomplete_fields = ("edital",)
    inlines = [ObrigacaoPenalidadeInline]

    def save_model(self, request, obj, form, change):
        if not change:  # Apenas para novos registros
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImportacaoPlanilhaTipoPenalidade)
class ImportacaoPlanilhaTipoPenalidadeAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/imr/importacao_tipos_penalidade.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_tipos_penalidade/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_tipos_penalidade(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_tipos_penalidade(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos tipos de penalidade"
    )


class PerfisMultipleChoiceForm(forms.ModelForm):
    perfis = forms.MultipleChoiceField(choices=PerfilDiretorSupervisao.PERFIS)


class TipoOcorrenciaForm(forms.ModelForm):
    perfis = forms.MultipleChoiceField(choices=PerfilDiretorSupervisao.PERFIS)

    class Meta:
        model = TipoOcorrencia
        fields = "__all__"


@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = (
        "posicao",
        "edital",
        "categoria",
        "titulo",
        "penalidade",
        "pontuacao",
        "perfis",
        "status",
        "aceita_multiplas_respostas",
    )
    ordering = ("criado_em",)
    search_fields = ("titulo",)
    search_help_text = "Pesquise por: título"
    list_filter = (
        "edital",
        ("categoria__nome", custom_titled_filter("Categoria")),
        "status",
        "aceita_multiplas_respostas",
    )
    readonly_fields = ("uuid", "criado_em", "criado_por", "alterado_em")
    autocomplete_fields = ("edital", "penalidade")
    form = TipoOcorrenciaForm

    def save_model(self, request, obj, form, change):
        if not change:  # Apenas para novos registros
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(CategoriaOcorrencia)
class CategoriaOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "posicao", "perfis", "gera_notificacao")
    ordering = ("posicao", "criado_em")
    list_filter = ("gera_notificacao",)
    form = PerfisMultipleChoiceForm


@admin.register(ImportacaoPlanilhaTipoOcorrencia)
class ImportacaoPlanilhaTipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/imr/importacao_tipos_ocorrencia.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_tipos_ocorrencia/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_tipos_ocorrencia(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_tipos_ocorrencia(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos tipos de ocorrência"
    )


class PerfisFilter(admin.SimpleListFilter):
    title = "Perfis"
    parameter_name = "perfis"

    def lookups(self, request, model_admin):
        return [
            (PerfilDiretorSupervisao.DIRETOR, PerfilDiretorSupervisao.DIRETOR),
            (PerfilDiretorSupervisao.SUPERVISAO, PerfilDiretorSupervisao.SUPERVISAO),
        ]

    def queryset(self, request, queryset):
        if self.value() == "Tudo":
            return queryset.all()
        if self.value() in [
            PerfilDiretorSupervisao.DIRETOR,
            PerfilDiretorSupervisao.SUPERVISAO,
        ]:
            return queryset.filter(tipo_ocorrencia__perfis__contains=[self.value()])
        return queryset.all()


@admin.register(ParametrizacaoOcorrencia)
class ParametrizacaoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = (
        "tipo_ocorrencia",
        "edital",
        "posicao",
        "titulo",
        "tipo_pergunta",
        "perfis",
    )
    ordering = ("criado_em",)
    search_fields = ("edital__numero", "titulo")
    search_help_text = "Pesquise por: número do edital, título"
    list_filter = ("tipo_ocorrencia", "tipo_ocorrencia__edital", PerfisFilter)
    autocomplete_fields = ("tipo_ocorrencia",)
    readonly_fields = ("uuid",)

    def edital(self, obj):
        return obj.tipo_ocorrencia.edital.numero

    def perfis(self, obj):
        return obj.tipo_ocorrencia.perfis


class TipoFormularioFilter(admin.SimpleListFilter):
    title = "Tipo de formulário"
    parameter_name = "tipo_formulario"

    def lookups(self, request, model_admin):
        return [
            (PerfilDiretorSupervisao.DIRETOR, PerfilDiretorSupervisao.DIRETOR),
            (PerfilDiretorSupervisao.SUPERVISAO, PerfilDiretorSupervisao.SUPERVISAO),
        ]

    def queryset(self, request, queryset):
        if self.value() == "Tudo":
            return queryset.all()
        elif self.value() == PerfilDiretorSupervisao.DIRETOR:
            return queryset.filter(formulariodiretor__isnull=False)
        elif self.value() == PerfilDiretorSupervisao.SUPERVISAO:
            return queryset.filter(formulariosupervisao__isnull=False)
        return queryset.all()


class OcorrenciaNaoSeAplicaInline(admin.TabularInline):
    model = OcorrenciaNaoSeAplica
    extra = 0


class FormularioSupervisaoInline(admin.StackedInline):
    model = FormularioSupervisao
    max_num = 1
    extra = 0
    autocomplete_fields = ("escola",)


class FormularioDiretorInline(admin.StackedInline):
    model = FormularioDiretor
    max_num = 1
    extra = 0


class RespostaSimNaoInline(admin.TabularInline):
    model = RespostaSimNao
    extra = 0


class RespostaCampoNumericoInline(admin.TabularInline):
    model = RespostaCampoNumerico
    extra = 0


class RespostaCampoTextoSimplesInline(admin.TabularInline):
    model = RespostaCampoTextoSimples
    extra = 0


class RespostaCampoTextoLongoInline(admin.TabularInline):
    model = RespostaCampoTextoLongo
    extra = 0


class RespostaDatasInline(admin.TabularInline):
    model = RespostaDatas
    extra = 0


class RespostaPeriodoInline(admin.TabularInline):
    model = RespostaPeriodo
    extra = 0


class RespostaFaixaEtariaInline(admin.TabularInline):
    model = RespostaFaixaEtaria
    extra = 0


class RespostaTipoAlimentacaoInline(admin.TabularInline):
    model = RespostaTipoAlimentacao
    extra = 0


class RespostaSimNaoNaoSeAplicaInline(admin.TabularInline):
    model = RespostaSimNaoNaoSeAplica
    extra = 0


class AnexosFormularioBaseInline(admin.TabularInline):
    model = AnexosFormularioBase
    extra = 0


class NotificacoesAssinadasFormularioBaseInline(admin.TabularInline):
    model = NotificacoesAssinadasFormularioBase
    extra = 0


class RespostaUtensilioMesaInline(admin.TabularInline):
    model = RespostaUtensilioMesa
    extra = 0


class RespostaUtensilioCozinhaInline(admin.TabularInline):
    model = RespostaUtensilioCozinha
    extra = 0


class RespostaEquipamentoInline(admin.TabularInline):
    model = RespostaEquipamento
    extra = 0


class RespostaMobiliarioInline(admin.TabularInline):
    model = RespostaMobiliario
    extra = 0


class RespostaReparoEAdaptacaoInline(admin.TabularInline):
    model = RespostaReparoEAdaptacao
    extra = 0


class RespostaInsumoInline(admin.TabularInline):
    model = RespostaInsumo
    extra = 0


@admin.register(FormularioOcorrenciasBase)
class FormularioOcorrenciasBaseAdmin(admin.ModelAdmin):
    inlines = [
        FormularioSupervisaoInline,
        FormularioDiretorInline,
        RespostaSimNaoInline,
        RespostaCampoNumericoInline,
        RespostaCampoTextoSimplesInline,
        RespostaCampoTextoLongoInline,
        RespostaDatasInline,
        RespostaPeriodoInline,
        RespostaFaixaEtariaInline,
        RespostaTipoAlimentacaoInline,
        RespostaSimNaoNaoSeAplicaInline,
        RespostaUtensilioMesaInline,
        RespostaUtensilioCozinhaInline,
        RespostaEquipamentoInline,
        RespostaMobiliarioInline,
        RespostaReparoEAdaptacaoInline,
        RespostaInsumoInline,
        OcorrenciaNaoSeAplicaInline,
        AnexosFormularioBaseInline,
        NotificacoesAssinadasFormularioBaseInline,
    ]
    list_filter = (TipoFormularioFilter, ("data", DateRangeFilter))


@admin.register(FormularioDiretor)
class FormularioDiretorAdmin(admin.ModelAdmin):
    list_filter = (("formulario_base__data", DateRangeFilter),)


@admin.register(FormularioSupervisao)
class FormularioSupervisaoAdmin(admin.ModelAdmin):
    list_filter = (
        ("formulario_base__data", DateRangeFilter),
        "acompanhou_visita",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")


class FaixaPontuacaoIMRForm(forms.ModelForm):
    class Meta:
        model = FaixaPontuacaoIMR
        fields = "__all__"


@admin.register(FaixaPontuacaoIMR)
class FaixaPontuacaoIMRAdmin(admin.ModelAdmin):
    list_display = (
        "pontuacao_minima",
        "pontuacao_maxima",
        "porcentagem_desconto",
        "criado_em",
        "alterado_em",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    form = FaixaPontuacaoIMRForm


class UtensilioMesaAdminForm(forms.ModelForm):
    class Meta:
        model = UtensilioMesa
        fields = "__all__"
        labels = {"nome": "Nome do Utensílio de Mesa"}


@admin.register(UtensilioMesa)
class UtensilioMesaAdmin(admin.ModelAdmin):
    form = UtensilioMesaAdminForm
    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do utensílio de mesa"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Utensílio de Mesa"


@admin.register(EditalUtensilioMesa)
class EditalUtensilioMesaAdmin(admin.ModelAdmin):
    filter_horizontal = ("utensilios_mesa",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


class UtensilioCozinhaAdminForm(forms.ModelForm):
    class Meta:
        model = UtensilioCozinha
        fields = "__all__"
        labels = {"nome": "Nome do Utensílio de Cozinha"}


@admin.register(UtensilioCozinha)
class UtensilioCozinhaAdmin(admin.ModelAdmin):
    form = UtensilioCozinhaAdminForm

    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do utensílio de cozinha"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Utensílio de Cozinha"


@admin.register(EditalUtensilioCozinha)
class EditalUtensilioCozinhaAdmin(admin.ModelAdmin):
    filter_horizontal = ("utensilios_cozinha",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


class EquipamentoAdminForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = "__all__"
        labels = {"nome": "Nome do Equipamento"}


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    form = EquipamentoAdminForm

    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do equipamento"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Equipamento"


@admin.register(EditalEquipamento)
class EditalEquipamentoAdmin(admin.ModelAdmin):
    filter_horizontal = ("equipamentos",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


class MobiliarioAdminForm(forms.ModelForm):
    class Meta:
        model = Mobiliario
        fields = "__all__"
        labels = {"nome": "Nome do Mobiliário"}


@admin.register(Mobiliario)
class MobiliarioAdmin(admin.ModelAdmin):
    form = MobiliarioAdminForm

    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do mobiliário"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Mobiliário"


@admin.register(EditalMobiliario)
class EditalMobiliarioAdmin(admin.ModelAdmin):
    filter_horizontal = ("mobiliarios",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


class ReparoEAdaptacaoAdminForm(forms.ModelForm):
    class Meta:
        model = ReparoEAdaptacao
        fields = "__all__"
        labels = {"nome": "Nome do Reparo e Adaptação"}


@admin.register(ReparoEAdaptacao)
class ReparoEAdaptacaoAdmin(admin.ModelAdmin):
    form = ReparoEAdaptacaoAdminForm

    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do reparo e adaptação"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Reparo e Adaptação"


@admin.register(EditalReparoEAdaptacao)
class EditalReparoEAdaptacaoAdmin(admin.ModelAdmin):
    filter_horizontal = ("reparos_e_adaptacoes",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


class InsumoAdminForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = "__all__"
        labels = {"nome": "Nome do Insumo"}


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    form = InsumoAdminForm

    list_display = (
        "nome_label",
        "status",
    )
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    search_fields = ("nome",)
    search_help_text = "Pesquise por: nome do insumo"
    list_filter = ("status",)

    def nome_label(self, obj):
        return obj.nome

    nome_label.short_description = "Nome do Insumo"


@admin.register(EditalInsumo)
class EditalInsumoAdmin(admin.ModelAdmin):
    filter_horizontal = ("insumos",)
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("edital",)
    search_fields = ("edital__numero",)
    search_help_text = "Pesquise por: número do edital"


@admin.register(OcorrenciaNaoSeAplica)
class OcorrenciaNaoSeAplicaAdmin(admin.ModelAdmin):
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    autocomplete_fields = ("tipo_ocorrencia",)
    search_fields = (
        "tipo_ocorrencia__edital__numero",
        "formulario_base__usuario__email",
        "formulario_base__usuario__nome",
    )
    search_help_text = (
        "Pesquise por: número do edital; (email, nome) do usuário do formulário."
    )
    list_display = ("tipo_ocorrencia", "formulario_base", "descricao", "criado_em")
    list_filter = ("tipo_ocorrencia",)


admin.site.register(TipoGravidade)
admin.site.register(ObrigacaoPenalidade)
admin.site.register(TipoPerguntaParametrizacaoOcorrencia)
admin.site.register(RespostaSimNao)
admin.site.register(RespostaCampoNumerico)
admin.site.register(RespostaCampoTextoSimples)
admin.site.register(RespostaCampoTextoLongo)
admin.site.register(RespostaDatas)
admin.site.register(RespostaPeriodo)
admin.site.register(RespostaFaixaEtaria)
admin.site.register(RespostaTipoAlimentacao)
admin.site.register(RespostaSimNaoNaoSeAplica)
admin.site.register(RespostaEquipamento)
admin.site.register(RespostaInsumo)
admin.site.register(RespostaMobiliario)
admin.site.register(RespostaReparoEAdaptacao)
admin.site.register(RespostaUtensilioCozinha)
admin.site.register(RespostaUtensilioMesa)
admin.site.register(TipoRespostaModelo)
admin.site.register(PeriodoVisita)
