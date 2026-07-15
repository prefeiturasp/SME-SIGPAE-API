from django.contrib import admin

from src.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)


@admin.register(AlteracaoCardapio)
class AlteracaoCardapioModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de alteração do tipo de alimentação.

    Configura a listagem administrativa de :class:`AlteracaoCardapio`,
    exibindo informações da escola e do período da solicitação, habilitando
    busca textual, filtros por motivo e rastros administrativos e mantendo o
    campo ``escola`` apenas para leitura.

    Attributes:
        list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
            Valores: ``("escola__codigo_eol", "escola__nome", "data_inicial", "data_final", "status", "DESCRICAO")``.
        search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
            Valores: ``("uuid", "escola__nome", "escola__codigo_eol")``.
        search_help_text (str): Texto auxiliar exibido abaixo do campo de busca.
            Valores: ``"Pesquisar por: UUID, nome da escola, codigo eol da escola"``.
        list_filter (tuple[str, ...]): Filtros laterais disponíveis na listagem.
            Valores: ``("motivo__nome", "status", "rastro_lote", "rastro_terceirizada")``.
        readonly_fields (tuple[str, ...]): Campos somente leitura no formulário.
            Valores: ``("escola",)``.
    """

    list_display = (
        "escola__codigo_eol",
        "escola__nome",
        "data_inicial",
        "data_final",
        "status",
        "DESCRICAO",
    )
    search_fields = ("uuid", "escola__nome", "escola__codigo_eol")
    search_help_text = "Pesquisar por: UUID, nome da escola, codigo eol da escola"
    list_filter = ("motivo__nome", "status", "rastro_lote", "rastro_terceirizada")
    readonly_fields = ("escola",)


admin.site.register(MotivoAlteracaoCardapio)
