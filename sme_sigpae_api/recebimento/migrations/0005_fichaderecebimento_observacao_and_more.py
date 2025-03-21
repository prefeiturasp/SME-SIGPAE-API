# Generated by Django 4.2.7 on 2024-04-25 20:32

import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import sme_sigpae_api.dados_comuns.validators


class Migration(migrations.Migration):
    dependencies = [
        ("recebimento", "0004_fichaderecebimento_data_fabricacao_de_acordo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="fichaderecebimento",
            name="observacao",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fichaderecebimento",
            name="sistema_vedacao_embalagem_secundaria",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Sistema de Vedação da Embalagem Secundária",
            ),
        ),
        migrations.CreateModel(
            name="ArquivoFichaRecebimento",
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
                    "arquivo",
                    models.FileField(
                        upload_to="arquivos_fichas_de_recebimentos",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["PDF", "PNG", "JPG", "JPEG"]
                            ),
                            sme_sigpae_api.dados_comuns.validators.validate_file_size_10mb,
                        ],
                    ),
                ),
                ("nome", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "ficha_recebimento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="arquivos",
                        to="recebimento.fichaderecebimento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Arquivo Ficha de Recebimento",
                "verbose_name_plural": "Arquivos Fichas de Recebimentos",
            },
        ),
    ]
