# Generated by Django 2.2.13 on 2021-09-09 11:14

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("escola", "0033_auto_20210512_1803"),
    ]

    operations = [
        migrations.CreateModel(
            name="LogAlunosMatriculadosPeriodoEscolaRegular",
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
                ("observacao", models.TextField(blank=True, verbose_name="Observação")),
                (
                    "quantidade_alunos",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Quantidade de alunos"
                    ),
                ),
                (
                    "escola",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="logs_alunos_matriculados_por_periodo",
                        to="escola.Escola",
                    ),
                ),
                (
                    "periodo_escolar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="logs_alunos_matriculados",
                        to="escola.PeriodoEscolar",
                    ),
                ),
            ],
            options={
                "verbose_name": "Log Alteração quantidade de alunos",
                "verbose_name_plural": "Logs de Alteração quantidade de alunos",
                "ordering": ("criado_em",),
            },
        ),
        migrations.CreateModel(
            name="AlunosMatriculadosPeriodoEscolaRegular",
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
                    "quantidade_alunos",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Quantidade de alunos"
                    ),
                ),
                (
                    "escola",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="alunos_matriculados_por_periodo",
                        to="escola.Escola",
                    ),
                ),
                (
                    "periodo_escolar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="alunos_matriculados",
                        to="escola.PeriodoEscolar",
                    ),
                ),
            ],
            options={
                "verbose_name": "Alunos Matriculados por Período e Escola",
                "verbose_name_plural": "Alunos Matriculados por Períodos e Escolas",
            },
        ),
    ]