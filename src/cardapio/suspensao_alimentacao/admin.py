from django.contrib import admin

from src.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)


class SuspensaoAlimentacaoInline(admin.TabularInline):
    """Inline para gerenciar ``SuspensaoAlimentacao`` vinculadas ao grupo.

    Permite adicionar e editar as datas de suspensão diretamente no formulário
    de administração da solicitação de suspensão de alimentação.
    """

    model = SuspensaoAlimentacao
    extra = 1


class QuantidadePorPeriodoSuspensaoAlimentacaoInline(admin.TabularInline):
    """Inline para gerenciar ``QuantidadePorPeriodoSuspensaoAlimentacao``.

    Permite adicionar e editar as quantidades de alunos por período escolar
    diretamente no formulário de administração da solicitação.
    """

    model = QuantidadePorPeriodoSuspensaoAlimentacao
    extra = 1


@admin.register(GrupoSuspensaoAlimentacao)
class GrupoSuspensaoAlimentacaoModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de suspensão de alimentação.

    Configura a listagem administrativa de :class:`GrupoSuspensaoAlimentacao`,
    com inlines para gerenciar as datas de suspensão e as quantidades por
    período escolar associadas à solicitação.
    """

    inlines = [
        SuspensaoAlimentacaoInline,
        QuantidadePorPeriodoSuspensaoAlimentacaoInline,
    ]


admin.site.register(MotivoSuspensao)
