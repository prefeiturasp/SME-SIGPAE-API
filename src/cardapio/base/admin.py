from django.contrib import admin

from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


@admin.register(VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar)
class VinculoTipoAlimentacaoModelAdmin(admin.ModelAdmin):
    """Admin do Django para vinculos de tipo de alimentacao por periodo e U.E.

    Configura a listagem administrativa de
    :class:`VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar`,
    disponibilizando filtros por periodo escolar, tipo de unidade escolar e
    status de ativacao do vinculo.

    Attributes:
        list_filter (tuple[str, ...]): Filtros laterais disponiveis na listagem.
            Valores: ``("periodo_escolar__nome", "tipo_unidade_escolar__iniciais", "ativo")``.
    """

    list_filter = ("periodo_escolar__nome", "tipo_unidade_escolar__iniciais", "ativo")


@admin.register(TipoAlimentacao)
class TipoAlimentacaoAdmin(admin.ModelAdmin):
    """Admin do Django para os tipos de alimentacao do cardapio.

    Configura a tela administrativa de :class:`TipoAlimentacao`, habilitando
    busca por nome e mantendo o UUID apenas para leitura no formulario de
    edicao.

    Attributes:
        search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
            Valores: ``("nome",)``.
        readonly_fields (tuple[str, ...]): Campos somente leitura no formulario.
            Valores: ``("uuid",)``.
    """

    search_fields = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(MotivoDRENaoValida)
class MotivoDRENaoValidaAdmin(admin.ModelAdmin):
    """Admin do Django para motivos usados pela DRE ao nao validar solicitacoes.

    Mantem o cadastro administrativo de :class:`MotivoDRENaoValida` com o
    comportamento padrao do Django Admin, sem customizacoes adicionais de
    listagem ou formulario.
    """


@admin.register(HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar)
class HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarAdmin(admin.ModelAdmin):
    """Admin do Django para horarios de tipos de alimentacao por escola.

    Disponibiliza o cadastro administrativo de
    :class:`HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar` com o
    comportamento padrao do Django Admin, permitindo consultar e editar as
    faixas de horario configuradas para cada escola, periodo escolar e tipo de
    alimentacao.
    """
