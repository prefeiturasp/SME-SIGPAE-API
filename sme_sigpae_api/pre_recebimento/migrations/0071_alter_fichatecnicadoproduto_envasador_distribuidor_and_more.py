# Generated by Django 5.2.1 on 2025-06-25 14:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "pre_recebimento",
            "0070_remove_fichatecnicadoproduto_fabricante_ficha_tecnica_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="fichatecnicadoproduto",
            name="envasador_distribuidor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fichas_tecnicas_como_envasador_distribuidor",
                to="pre_recebimento.fabricantefichatecnica",
                verbose_name="Envasador/Distribuidor",
            ),
        ),
        migrations.AlterField(
            model_name="fichatecnicadoproduto",
            name="fabricante",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fichas_tecnicas_como_fabricante",
                to="pre_recebimento.fabricantefichatecnica",
            ),
        ),
    ]
