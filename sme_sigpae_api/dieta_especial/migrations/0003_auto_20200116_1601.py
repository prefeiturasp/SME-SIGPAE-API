# Generated by Django 2.2.8 on 2020-01-16 19:01

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dieta_especial", "0002_auto_20191205_1815"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlergiaIntolerancia",
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
                ("descricao", models.TextField(blank=True, verbose_name="Descricao")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ClassificacaoDieta",
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
                ("descricao", models.TextField(blank=True, verbose_name="Descricao")),
                (
                    "nome",
                    models.CharField(blank=True, max_length=100, verbose_name="Nome"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MotivoNegacao",
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
                ("descricao", models.TextField(blank=True, verbose_name="Descricao")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="TipoDieta",
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
                ("descricao", models.TextField(blank=True, verbose_name="Descricao")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="anexo",
            name="eh_laudo_medico",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="anexo",
            name="nome",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="justificativa_negacao",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="registro_funcional_nutricionista",
            field=models.CharField(
                blank=True,
                help_text="CRN/CRM/CRFa...",
                max_length=200,
                validators=[django.core.validators.MinLengthValidator(6)],
                verbose_name="Nome completo do pescritor da receita",
            ),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="alergias_intolerancias",
            field=models.ManyToManyField(
                blank=True, to="dieta_especial.AlergiaIntolerancia"
            ),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="classificacao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="dieta_especial.ClassificacaoDieta",
            ),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="motivo_negacao",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="dieta_especial.MotivoNegacao",
            ),
        ),
        migrations.AddField(
            model_name="solicitacaodietaespecial",
            name="tipos",
            field=models.ManyToManyField(blank=True, to="dieta_especial.TipoDieta"),
        ),
    ]