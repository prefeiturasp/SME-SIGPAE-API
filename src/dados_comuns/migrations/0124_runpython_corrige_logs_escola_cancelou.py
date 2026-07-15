# Manually generated

from django.db import migrations


def substituir_status_evento(apps, _):
    LogSolicitacoesUsuario = apps.get_model("dados_comuns", "LogSolicitacoesUsuario")

    LogSolicitacoesUsuario.objects.filter(
        status_evento=103,  # CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL
        solicitacao_tipo=8,  # DIETA_ESPECIAL
        usuario__vinculos__content_type__model="escola",
    ).update(
        status_evento=13,  # ESCOLA_CANCELOU
    )


def reverte_status_evento(apps, _):
    LogSolicitacoesUsuario = apps.get_model("dados_comuns", "LogSolicitacoesUsuario")

    LogSolicitacoesUsuario.objects.filter(
        status_evento=13,  # ESCOLA_CANCELOU
        solicitacao_tipo=8,  # DIETA_ESPECIAL
        usuario__vinculos__content_type__model="escola",
    ).update(
        status_evento=103,  # CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL
    )


class Migration(migrations.Migration):

    dependencies = [
        ("dados_comuns", "0123_alter_logsolicitacoesusuario_status_evento"),
    ]

    operations = [
        migrations.RunPython(substituir_status_evento, reverte_status_evento),
    ]
