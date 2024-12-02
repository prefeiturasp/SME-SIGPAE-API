# Generated by Django 4.2.7 on 2024-04-25 16:12

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("terceirizada", "0019_alter_contrato_ata"),
        ("imr", "0009_alter_tipopenalidade_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportacaoPlanilhaTipoOcorrencia",
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
                ("conteudo", models.FileField(blank=True, default="", upload_to="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDENTE", "PENDENTE"),
                            ("SUCESSO", "SUCESSO"),
                            ("ERRO", "ERRO"),
                            ("PROCESSADO_COM_ERRO", "PROCESSADO_COM_ERRO"),
                            ("PROCESSANDO", "PROCESSANDO"),
                            ("REMOVIDO", "REMOVIDO"),
                        ],
                        default="PENDENTE",
                        max_length=35,
                        verbose_name="status",
                    ),
                ),
                ("log", models.TextField(blank=True, default="")),
                ("resultado", models.FileField(blank=True, default="", upload_to="")),
            ],
            options={
                "verbose_name": "Arquivo para importação/atualização de tipos de ocorrência",
                "verbose_name_plural": "Arquivos para importação/atualização de tipos de ocorrência",
            },
        ),
        migrations.AlterModelOptions(
            name="categoriaocorrencia",
            options={
                "ordering": ("posicao", "nome"),
                "verbose_name": "Categoria das Ocorrências",
                "verbose_name_plural": "Categorias das Ocorrências",
            },
        ),
        migrations.AlterModelOptions(
            name="tipopenalidade",
            options={
                "ordering": ("edital__numero", "numero_clausula"),
                "verbose_name": "Tipo de Penalidade",
                "verbose_name_plural": "Tipos de Penalidades",
            },
        ),
        migrations.AlterUniqueTogether(
            name="tipoocorrencia",
            unique_together={("edital", "categoria", "penalidade")},
        ),
    ]