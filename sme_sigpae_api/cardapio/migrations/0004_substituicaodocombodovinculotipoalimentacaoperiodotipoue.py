# Generated by Django 2.2.6 on 2019-12-06 16:53

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cardapio", "0003_auto_20191205_1815"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "combo",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="substituicoes",
                        to="cardapio.ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
                    ),
                ),
                (
                    "tipos_alimentacao",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Tipos de alimentacao das substituições dos combos.",
                        related_name="cardapio_substituicaodocombodovinculotipoalimentacaoperiodotipoue_possibilidades",
                        to="cardapio.TipoAlimentacao",
                    ),
                ),
            ],
            options={
                "verbose_name": "Substituição do combo do vínculo tipo alimentação",
                "verbose_name_plural": "Substituições do  combos do vínculo tipo alimentação",
            },
        ),
    ]