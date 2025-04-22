from django.contrib import admin

from .forms import NomeDeProdutoEditalForm
from .models import (
    EmbalagemProduto,
    Fabricante,
    HomologacaoProduto,
    ImagemDoProduto,
    InformacaoNutricional,
    InformacoesNutricionaisDoProduto,
    ItemCadastro,
    LogNomeDeProdutoEdital,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProtocoloDeDietaEspecial,
    ReclamacaoDeProduto,
    RespostaAnaliseSensorial,
    SolicitacaoCadastroProdutoDieta,
    TipoDeInformacaoNutricional,
    UnidadeMedida,
)


class InformacoesNutricionaisDoProdutoInline(admin.TabularInline):
    model = InformacoesNutricionaisDoProduto
    extra = 1


class ImagemDoProdutoInline(admin.TabularInline):
    model = ImagemDoProduto
    extra = 1


@admin.register(Marca)
class MarcaModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Fabricante)
class FabricanteModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(UnidadeMedida)
class UnidadeMedidaModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(EmbalagemProduto)
class EmbalagemProdutoModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Produto)
class ProdutoModelAdmin(admin.ModelAdmin):
    inlines = [InformacoesNutricionaisDoProdutoInline, ImagemDoProdutoInline]
    list_display = ("nome", "marca", "fabricante")
    search_fields = ("nome", "marca__nome", "fabricante__nome")
    ordering = ("nome",)


@admin.register(NomeDeProdutoEdital)
class NomeDeProdutoEditalAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_produto", "get_usuario", "criado_em", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo",)
    readonly_fields = ("get_usuario",)
    form = NomeDeProdutoEditalForm
    object_history_template = "produto/object_history.html"

    def salvar_log(self, request, obj, acao):
        LogNomeDeProdutoEdital.objects.create(
            acao=acao,
            nome_de_produto_edital=obj,
            criado_por=request.user,
        )

    def save_model(self, request, obj, form, change):
        if change:
            if obj.ativo:
                acao = "a"
            else:
                acao = "i"
            self.salvar_log(request, obj, acao)
        else:
            obj.criado_por = request.user
        super(NomeDeProdutoEditalAdmin, self).save_model(request, obj, form, change)

    def get_usuario(self, obj):
        return obj.criado_por.nome if obj.criado_por else None

    get_usuario.short_description = "Usuário"

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProtocoloDeDietaEspecial)
class ProtocoloDeDietaEspecialModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(TipoDeInformacaoNutricional)
class TipoDeInformacaoNutricionalModelAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(HomologacaoProduto)
class HomologacaoProdutoModelAdmin(admin.ModelAdmin):
    list_display = ("__str__", "produto", "status", "uuid")
    search_fields = ("produto__nome",)


@admin.register(InformacaoNutricional)
class InformacaoNutricionalModelAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tipo_nutricional", "medida", "eh_fixo")
    search_fields = ("nome",)
    list_filter = ("tipo_nutricional",)
    list_editable = ("eh_fixo",)


@admin.register(ItemCadastro)
class ItemCadastroModelAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tipo")
    list_filter = ("content_type",)
    actions = ("cria_itens",)

    def cria_itens(self, request, _):
        from sme_sigpae_api.produto.utils.genericos import cria_itens_cadastro

        cria_itens_cadastro()

        self.message_user(request, "Processo iniciado com sucesso.")

    cria_itens.short_description = (
        "Cria ItemCadastro para cada Marca e/ou Fabricante caso não exista."
    )


admin.site.register(ReclamacaoDeProduto)
admin.site.register(RespostaAnaliseSensorial)
admin.site.register(SolicitacaoCadastroProdutoDieta)
