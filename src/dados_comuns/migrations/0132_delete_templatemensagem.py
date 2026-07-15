from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dados_comuns", "0131_alter_logsolicitacoesusuario_status_evento_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TemplateMensagem",
        ),
    ]
