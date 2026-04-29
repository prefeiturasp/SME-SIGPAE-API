from django.contrib import admin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)


class SubstituicoesCEIInLine(admin.TabularInline):
    """Inline do Django para substituições de alimentação no período escolar CEI.

    Exibe e permite editar instâncias de
    :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEI` diretamente no
    formulário de :class:`AlteracaoCardapioCEI`.

    Attributes:
        model (Model): Modelo gerenciado pelo inline.
            Valor: :class:`SubstituicaoAlimentacaoNoPeriodoEscolarCEI`.
        extra (int): Número de formulários extras exibidos para novos registros.
            Valor: ``1``.
    """

    model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
    extra = 1


@admin.register(AlteracaoCardapioCEI)
class AlteracaoCardapioCEIModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de alteração do tipo de alimentação CEI.

    Configura a listagem administrativa de :class:`AlteracaoCardapioCEI`,
    exibindo o UUID, a data e o status de cada solicitação, habilitando filtro
    por status e incorporando o inline de substituições no formulário de edição.

    Attributes:
        inlines (list): Inlines exibidos no formulário de edição.
            Valor: ``[SubstituicoesCEIInLine]``.
        list_display (list[str]): Colunas exibidas na listagem do admin.
            Valores: ``["uuid", "data", "status"]``.
        list_filter (list[str]): Filtros laterais disponíveis na listagem.
            Valores: ``["status"]``.
    """

    inlines = [SubstituicoesCEIInLine]
    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]
