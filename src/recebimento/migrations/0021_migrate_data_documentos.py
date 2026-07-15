from django.db import migrations


def migrar_dados_documentos(apps, schema_editor):
    DocumentoFichaDeRecebimento = apps.get_model(
        "recebimento", "DocumentoFichaDeRecebimento"
    )
    FichaDeRecebimento = apps.get_model("recebimento", "FichaDeRecebimento")

    for ficha in FichaDeRecebimento.objects.all():
        for documento in ficha.documentos_recebimento.all():
            DocumentoFichaDeRecebimento.objects.create(
                ficha_recebimento=ficha,
                documento_recebimento=documento,
                quantidade_recebida=None,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("recebimento", "0020_alter_documentofichaderecebimento_quantidade_recebida"),
    ]

    operations = [
        migrations.RunPython(migrar_dados_documentos),
    ]
