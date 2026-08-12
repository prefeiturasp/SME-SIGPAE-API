# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dados_comuns", "0133_alter_logsolicitacoesusuario_status_evento"),
    ]

    operations = [
        migrations.CreateModel(
            name="VersaoSistema",
            fields=[
                (
                    "id",
                    models.PositiveIntegerField(
                        default=1,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("versao", models.CharField(max_length=50, default="2.71.5")),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Versão do Sistema",
                "verbose_name_plural": "Versões do Sistema",
            },
        ),
    ]
