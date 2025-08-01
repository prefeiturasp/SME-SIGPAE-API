# Generated by Django 5.2.1 on 2025-07-18 11:06

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recebimento", "0010_alter_questaoficharecebimento_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="OcorrenciaFichaRecebimento",
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
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("FALTA", "Falta"),
                            ("RECUSA", "Recusa"),
                            ("OUTROS_MOTIVOS", "Outros Motivos"),
                        ],
                        max_length=20,
                        verbose_name="Tipo de Ocorrência",
                    ),
                ),
                (
                    "relacao",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CRONOGRAMA", "Cronograma"),
                            ("NOTA_FISCAL", "Nota Fiscal"),
                            ("TOTAL", "Total"),
                            ("PARCIAL", "Parcial"),
                        ],
                        max_length=20,
                        null=True,
                        verbose_name="Relação",
                    ),
                ),
                (
                    "numero_nota",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Número da Nota",
                    ),
                ),
                (
                    "quantidade",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Quantidade"
                    ),
                ),
                ("descricao", models.TextField(verbose_name="Descrição")),
                (
                    "ficha_recebimento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ocorrencias",
                        to="recebimento.fichaderecebimento",
                        verbose_name="Ficha de Recebimento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ocorrência da Ficha de Recebimento",
                "verbose_name_plural": "Ocorrências das Fichas de Recebimento",
                "ordering": ["criado_em"],
            },
        ),
    ]
