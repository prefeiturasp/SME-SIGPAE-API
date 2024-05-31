# Generated by Django 4.2.7 on 2024-05-10 15:47

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("imr", "0020_insumo_editalinsumo"),
    ]

    operations = [
        migrations.CreateModel(
            name="RespostaUtensilioMesa",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_utensilios_mesa",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_utensilios_mesa",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.utensiliomesa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Utensílio de Mesa",
                "verbose_name_plural": "Respostas Utensílio de Mesa",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
        migrations.CreateModel(
            name="RespostaUtensilioCozinha",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_utensilios_cozinha",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_utensilios_cozinha",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.utensiliocozinha",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Utensílio de Cozinha",
                "verbose_name_plural": "Respostas Utensílio de Cozinha",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
        migrations.CreateModel(
            name="RespostaReparoEAdaptacao",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_reparos_e_adaptacoes",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_reparos_e_adaptacoes",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.reparoeadaptacao",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Reparo e Adaptação",
                "verbose_name_plural": "Respostas Reparo e Adaptação",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
        migrations.CreateModel(
            name="RespostaMobiliario",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_mobiliarios",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_mobiliarios",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.mobiliario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Mobiliário",
                "verbose_name_plural": "Respostas Mobiliário",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
        migrations.CreateModel(
            name="RespostaInsumo",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_insumos",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_insumos",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.insumo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Insumo",
                "verbose_name_plural": "Respostas Insumo",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
        migrations.CreateModel(
            name="RespostaEquipamento",
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
                    "grupo",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="Grupo de respostas"
                    ),
                ),
                (
                    "formulario_base",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_equipamentos",
                        to="imr.formularioocorrenciasbase",
                        verbose_name="Formulário de Ocorrências",
                    ),
                ),
                (
                    "parametrizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respostas_equipamentos",
                        to="imr.parametrizacaoocorrencia",
                    ),
                ),
                (
                    "resposta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="respostas_relatorio_imr",
                        to="imr.equipamento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resposta Equipamento",
                "verbose_name_plural": "Respostas Equipamento",
                "unique_together": {("formulario_base", "parametrizacao", "grupo")},
            },
        ),
    ]