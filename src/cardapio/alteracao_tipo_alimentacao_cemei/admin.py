from django.contrib import admin

from src.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
)


@admin.register(AlteracaoCardapioCEMEI)
class AlteracaoCardapioCEMEIModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de alteração do tipo de alimentação CEMEI.

    Configura a listagem administrativa de :class:`AlteracaoCardapioCEMEI`,
    exibindo o UUID, a data e o status de cada solicitação, e habilitando
    filtro por status.

    Attributes:
        list_display (list[str]): Colunas exibidas na listagem do admin.
            Valores: ``["uuid", "data", "status"]``.
        list_filter (list[str]): Filtros laterais disponíveis na listagem.
            Valores: ``["status"]``.
    """

    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]
