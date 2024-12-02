# Generated by Django 2.2.13 on 2020-09-03 11:13

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dieta_especial", "0013_auto_20200826_1327"),
    ]

    operations = [
        migrations.AlterField(
            model_name="anexo",
            name="solicitacao_dieta_especial",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="dieta_especial.SolicitacaoDietaEspecial",
            ),
        ),
        migrations.AlterField(
            model_name="solicitacaodietaespecial",
            name="registro_funcional_pescritor",
            field=models.CharField(
                blank=True,
                help_text="CRN/CRM/CRFa...",
                max_length=200,
                validators=[
                    django.core.validators.MinLengthValidator(4),
                    django.core.validators.MaxLengthValidator(6),
                ],
                verbose_name="Nome completo do pescritor da receita",
            ),
        ),
        migrations.AlterField(
            model_name="substituicaoalimento",
            name="solicitacao_dieta_especial",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="dieta_especial.SolicitacaoDietaEspecial",
            ),
        ),
    ]