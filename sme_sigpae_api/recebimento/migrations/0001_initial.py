# Generated by Django 4.2.7 on 2024-03-21 18:59

import uuid

import multiselectfield.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="QuestaoConferencia",
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
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "alterado_em",
                    models.DateTimeField(auto_now=True, verbose_name="Alterado em"),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("questao", models.CharField(verbose_name="Questão")),
                (
                    "tipo_questao",
                    multiselectfield.db.fields.MultiSelectField(
                        choices=[
                            ("PRIMARIA", "Primária"),
                            ("SECUNDARIA", "Secundária"),
                        ],
                        max_length=19,
                        verbose_name="Tipo de Questão",
                    ),
                ),
                (
                    "pergunta_obrigatoria",
                    models.BooleanField(
                        default=False, verbose_name="Pergunta Obrigatória?"
                    ),
                ),
                (
                    "posicao",
                    models.PositiveSmallIntegerField(
                        blank=True, null=True, verbose_name="Posição"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("ATIVO", "Ativo"), ("INATIVO", "Inativo")],
                        default="ATIVO",
                        max_length=10,
                    ),
                ),
            ],
            options={
                "verbose_name": "Questão para Conferência",
                "verbose_name_plural": "Questões para Conferência",
            },
        ),
    ]