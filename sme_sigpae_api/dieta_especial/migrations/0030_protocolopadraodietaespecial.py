# Generated by Django 2.2.13 on 2021-04-15 17:49

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import sme_sigpae_api.dados_comuns.behaviors


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dieta_especial", "0029_auto_20210308_1029"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProtocoloPadraoDietaEspecial",
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("nome_protocolo", models.TextField(verbose_name="Nome do Protocolo")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("LIBERADO", "Liberado"),
                            ("NAO_LIBERADO", "Não Liberado"),
                        ],
                        default="NAO_LIBERADO",
                        max_length=25,
                        verbose_name="Status da guia",
                    ),
                ),
                (
                    "criado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Protocolo padrão de dieta especial",
                "verbose_name_plural": "Protocolos padrões de dieta especial",
                "ordering": ("-criado_em",),
            },
            bases=(
                models.Model,
                sme_sigpae_api.dados_comuns.behaviors.TemIdentificadorExternoAmigavel,
            ),
        ),
    ]
