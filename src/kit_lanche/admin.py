from django import forms
from django.contrib import admin

from .models import (
    EscolaQuantidade,
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    ItemKitLanche,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheUnificada,
)

admin.site.register(KitLanche)
admin.site.register(ItemKitLanche)
admin.site.register(SolicitacaoKitLancheUnificada)
admin.site.register(EscolaQuantidade)
admin.site.register(FaixaEtariaSolicitacaoKitLancheCEIAvulsa)


class SolicitacaoKitLancheBaseForm(forms.ModelForm):
    """Formulário que permite editar os campos da solicitação base de kit lanche.

    A ``SolicitacaoKitLancheAvulsa`` aponta para uma ``SolicitacaoKitLanche``,
    tabela acessória que guarda a data, o motivo, a descrição, o tempo de
    passeio e os kits. Para permitir editar esses dados no mesmo formulário da
    solicitação avulsa, os campos editáveis são declarados aqui e persistidos
    em :meth:`save_solicitacao_kit_lanche`.

    Attributes:
        campos_base (tuple[str, ...]): Campos da solicitação base editáveis no
            formulário. Valores: ``("data", "motivo", "descricao", "tempo_passeio")``.
    """

    campos_base = ("data", "motivo", "descricao", "tempo_passeio")

    data = SolicitacaoKitLanche._meta.get_field("data").formfield(
        widget=admin.widgets.AdminDateWidget,
    )
    motivo = SolicitacaoKitLanche._meta.get_field("motivo").formfield(
        widget=forms.Textarea(attrs={"rows": 2, "cols": 60}),
    )
    descricao = SolicitacaoKitLanche._meta.get_field("descricao").formfield(
        widget=forms.Textarea(attrs={"rows": 2, "cols": 60}),
    )
    tempo_passeio = SolicitacaoKitLanche._meta.get_field("tempo_passeio").formfield()

    class Meta:
        model = SolicitacaoKitLancheAvulsa
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = self._solicitacao_kit_lanche_base()
        if base is None:
            for nome in self.campos_base:
                self.fields.pop(nome, None)
            return
        self.initial.update(
            {
                "data": base.data,
                "motivo": base.motivo,
                "descricao": base.descricao,
                "tempo_passeio": base.tempo_passeio,
            }
        )

    def _solicitacao_kit_lanche_base(self):
        """Retorna a solicitação base vinculada, se existir.

        Returns:
            SolicitacaoKitLanche | None: Solicitação base vinculada à instância
            em edição, ou ``None`` quando o registro ainda não existe ou não
            possui vínculo.
        """
        if self.instance.solicitacao_kit_lanche_id:
            return self.instance.solicitacao_kit_lanche
        return None

    def save_solicitacao_kit_lanche(self):
        """Persiste os campos editados da solicitação base de kit lanche.

        Returns:
            None
        """
        base = self.cleaned_data.get("solicitacao_kit_lanche")
        if not base or "data" not in self.cleaned_data:
            return
        base.data = self.cleaned_data["data"]
        base.motivo = self.cleaned_data["motivo"]
        base.descricao = self.cleaned_data["descricao"]
        base.tempo_passeio = self.cleaned_data["tempo_passeio"]
        base.save()


class SolicitacaoKitLancheAvulsaAdminBase(admin.ModelAdmin):
    """Configuração comum aos admins de solicitações avulsas de kit lanche.

    As solicitações avulsas apontam para tabelas muito grandes (escolas,
    alunos, usuários e solicitações base de kit lanche). Por isso os
    relacionamentos usam autocomplete, que carrega as opções sob demanda em
    vez de renderizar um ``select`` com todos os registros, e os campos
    controlados pelo fluxo de aprovação ficam apenas para leitura. Na edição,
    a escola e o usuário criador também passam a ser somente leitura e os
    campos da solicitação base são exibidos no próprio formulário, agrupados
    na seção "Solicitação base de kit lanche".

    Attributes:
        form (type): Formulário usado no admin.
            Valor: :class:`SolicitacaoKitLancheBaseForm`.
        autocomplete_fields (tuple[str, ...]): Relacionamentos com busca por autocomplete.
            Valores: ``("escola", "solicitacao_kit_lanche", "alunos_com_dieta_especial_participantes", "criado_por")``.
        readonly_fields (tuple[str, ...]): Campos somente leitura no formulário.
            Valores: ``("uuid", "status", "foi_solicitado_fora_do_prazo", "terceirizada_conferiu_gestao", "kits")``.
        search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
            Valores: ``("=uuid", "escola__nome", "escola__codigo_eol")``.
        list_select_related (tuple[str, ...]): Relações carregadas via ``select_related``.
            Valores: ``("escola", "solicitacao_kit_lanche")``.
        ordering (tuple[str, ...]): Ordenação padrão da listagem.
            Valores: ``("escola", "status")``.
        campos_identificacao (tuple[str, ...]): Campos da seção de identificação.
            Valores: ``("uuid", "status", "escola", "criado_por", "foi_solicitado_fora_do_prazo", "terceirizada_conferiu_gestao")``.
        campos_base (tuple[str, ...]): Campos da seção da solicitação base.
            Valores: ``("data", "motivo", "descricao", "tempo_passeio", "kits")``.
    """

    form = SolicitacaoKitLancheBaseForm
    autocomplete_fields = (
        "escola",
        "solicitacao_kit_lanche",
        "alunos_com_dieta_especial_participantes",
        "criado_por",
    )
    readonly_fields = (
        "uuid",
        "status",
        "foi_solicitado_fora_do_prazo",
        "terceirizada_conferiu_gestao",
        "kits",
    )
    search_fields = ("=uuid", "escola__nome", "escola__codigo_eol")
    list_select_related = ("escola", "solicitacao_kit_lanche")
    ordering = ("escola", "status")
    campos_identificacao = (
        "uuid",
        "status",
        "escola",
        "criado_por",
        "foi_solicitado_fora_do_prazo",
        "terceirizada_conferiu_gestao",
    )
    campos_base = ("data", "motivo", "descricao", "tempo_passeio", "kits")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(
                [
                    "escola",
                    "criado_por",
                ]
            )
        return tuple(readonly_fields)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return ((None, {"fields": self.campos_cadastro}),)
        return (
            ("Identificação", {"fields": self.campos_identificacao}),
            ("Solicitação", {"fields": self.campos_solicitacao}),
            (
                "Solicitação base de kit lanche",
                {"fields": self.campos_base},
            ),
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.save_solicitacao_kit_lanche()

    @admin.display(description="Kits")
    def kits(self, obj):
        """Retorna os nomes dos kits da solicitação base, somente para leitura.

        Args:
            obj (SolicitacaoKitLancheAvulsa | None): Solicitação avulsa exibida.

        Returns:
            str: Nomes dos kits separados por vírgula, ou ``"-"`` quando não há
            solicitação base ou kits vinculados.
        """
        if not obj or not obj.solicitacao_kit_lanche_id:
            return "-"
        nomes = obj.solicitacao_kit_lanche.kits.values_list("nome", flat=True)
        return ", ".join(nomes) or "-"


@admin.register(SolicitacaoKitLancheAvulsa)
class SolicitacaoKitLancheAvulsaAdmin(SolicitacaoKitLancheAvulsaAdminBase):
    """Admin do Django para solicitações avulsas de kit lanche.

    Attributes:
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("uuid", "escola", "data", "local", "quantidade_alunos", "status")``.
        campos_cadastro (tuple[str, ...]): Campos exibidos no formulário de inclusão.
            Valores: ``("escola", "solicitacao_kit_lanche", "local", "evento", "quantidade_alunos", "alunos_com_dieta_especial_participantes", "criado_por")``.
        campos_solicitacao (tuple[str, ...]): Campos exibidos na seção da solicitação.
            Valores: ``("solicitacao_kit_lanche", "local", "evento", "quantidade_alunos", "alunos_com_dieta_especial_participantes")``.
    """

    list_display = ("uuid", "escola", "data", "local", "quantidade_alunos", "status")
    campos_cadastro = (
        "escola",
        "solicitacao_kit_lanche",
        "local",
        "evento",
        "quantidade_alunos",
        "alunos_com_dieta_especial_participantes",
        "criado_por",
    )
    campos_solicitacao = (
        "solicitacao_kit_lanche",
        "local",
        "evento",
        "quantidade_alunos",
        "alunos_com_dieta_especial_participantes",
    )


@admin.register(SolicitacaoKitLanche)
class SolicitacaoKitLancheAdmin(admin.ModelAdmin):
    """Admin do Django para as solicitações base de kit lanche.

    Attributes:
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("criado_em", "data")``.
        search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
            Valores: ``("=uuid", "=id")``.
    """

    list_display = ("criado_em", "data")
    search_fields = ("=uuid", "=id")


@admin.register(SolicitacaoKitLancheCEIAvulsa)
class SolicitacaoKitLancheCEIAvulsaAdmin(SolicitacaoKitLancheAvulsaAdminBase):
    """Admin do Django para solicitações avulsas de kit lanche de CEI.

    Attributes:
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("uuid", "escola", "data", "local", "status")``.
        campos_cadastro (tuple[str, ...]): Campos exibidos no formulário de inclusão.
            Valores: ``("escola", "solicitacao_kit_lanche", "local", "evento", "alunos_com_dieta_especial_participantes", "criado_por")``.
        campos_solicitacao (tuple[str, ...]): Campos exibidos na seção da solicitação.
            Valores: ``("solicitacao_kit_lanche", "local", "evento", "alunos_com_dieta_especial_participantes")``.
    """

    list_display = ("uuid", "escola", "data", "local", "status")
    campos_cadastro = (
        "escola",
        "solicitacao_kit_lanche",
        "local",
        "evento",
        "alunos_com_dieta_especial_participantes",
        "criado_por",
    )
    campos_solicitacao = (
        "solicitacao_kit_lanche",
        "local",
        "evento",
        "alunos_com_dieta_especial_participantes",
    )
