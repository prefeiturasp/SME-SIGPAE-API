from django.contrib import admin

from .models import (
    CategoriaPerguntaFrequente,
    CentralDeDownload,
    Contato,
    Endereco,
    LogSolicitacoesUsuario,
    Notificacao,
    PerguntaFrequente,
    TemplateMensagem,
)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("email", "nome", "telefone", "telefone2", "eh_nutricionista")
    search_fields = ("email", "nome", "telefone", "telefone2")


@admin.register(CentralDeDownload)
class CentralDeDownloadAdmin(admin.ModelAdmin):
    list_display = ("identificador", "status", "criado_em", "visto")
    readonly_fields = (
        "uuid",
        "id",
    )
    list_display_links = ("identificador",)


admin.site.register(CategoriaPerguntaFrequente)
admin.site.register(Endereco)
admin.site.register(LogSolicitacoesUsuario)
admin.site.register(Notificacao)
admin.site.register(PerguntaFrequente)
admin.site.register(TemplateMensagem)
