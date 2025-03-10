# Generated by Django 2.2.6 on 2019-12-05 21:15

import uuid

import django_xworkflows.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AlteracaoCardapio",
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
                ("data_inicial", models.DateField(verbose_name="Data inicial")),
                ("data_final", models.DateField(verbose_name="Data final")),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("observacao", models.TextField(blank=True, verbose_name="Observação")),
                (
                    "status",
                    django_xworkflows.models.StateField(
                        max_length=29,
                        workflow=django_xworkflows.models._SerializedWorkflow(
                            initial_state="RASCUNHO",
                            name="PedidoAPartirDaEscolaWorkflow",
                            states=[
                                "RASCUNHO",
                                "DRE_A_VALIDAR",
                                "DRE_VALIDADO",
                                "DRE_PEDIU_ESCOLA_REVISAR",
                                "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
                                "CODAE_AUTORIZADO",
                                "CODAE_NEGOU_PEDIDO",
                                "TERCEIRIZADA_TOMOU_CIENCIA",
                                "ESCOLA_CANCELOU",
                                "CANCELADO_AUTOMATICAMENTE",
                            ],
                        ),
                    ),
                ),
            ],
            options={
                "verbose_name": "Alteração de cardápio",
                "verbose_name_plural": "Alterações de cardápio",
            },
        ),
        migrations.CreateModel(
            name="Cardapio",
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
                    "ativo",
                    models.BooleanField(default=True, verbose_name="Está ativo?"),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                ("data", models.DateField(verbose_name="Data")),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
            ],
            options={
                "verbose_name": "Cardápio",
                "verbose_name_plural": "Cardápios",
            },
        ),
        migrations.CreateModel(
            name="ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
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
            ],
            options={
                "verbose_name": "Combo do vínculo tipo alimentação",
                "verbose_name_plural": "Combos do vínculo tipo alimentação",
            },
        ),
        migrations.CreateModel(
            name="GrupoSuspensaoAlimentacao",
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
                    "status",
                    django_xworkflows.models.StateField(
                        max_length=26,
                        workflow=django_xworkflows.models._SerializedWorkflow(
                            initial_state="RASCUNHO",
                            name="InformativoPartindoDaEscolaWorkflow",
                            states=[
                                "RASCUNHO",
                                "INFORMADO",
                                "TERCEIRIZADA_TOMOU_CIENCIA",
                            ],
                        ),
                    ),
                ),
            ],
            options={
                "verbose_name": "Grupo de suspensão de alimentação",
                "verbose_name_plural": "Grupo de suspensão de alimentação",
            },
        ),
        migrations.CreateModel(
            name="InversaoCardapio",
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
                ("motivo", models.TextField(blank=True, verbose_name="Motivo")),
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
                    "status",
                    django_xworkflows.models.StateField(
                        max_length=29,
                        workflow=django_xworkflows.models._SerializedWorkflow(
                            initial_state="RASCUNHO",
                            name="PedidoAPartirDaEscolaWorkflow",
                            states=[
                                "RASCUNHO",
                                "DRE_A_VALIDAR",
                                "DRE_VALIDADO",
                                "DRE_PEDIU_ESCOLA_REVISAR",
                                "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
                                "CODAE_AUTORIZADO",
                                "CODAE_NEGOU_PEDIDO",
                                "TERCEIRIZADA_TOMOU_CIENCIA",
                                "ESCOLA_CANCELOU",
                                "CANCELADO_AUTOMATICAMENTE",
                            ],
                        ),
                    ),
                ),
            ],
            options={
                "verbose_name": "Inversão de cardápio",
                "verbose_name_plural": "Inversão$ProjectFileDir$ de cardápios",
            },
        ),
        migrations.CreateModel(
            name="MotivoAlteracaoCardapio",
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
                    "nome",
                    models.CharField(blank=True, max_length=100, verbose_name="Nome"),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
            ],
            options={
                "verbose_name": "Motivo de alteração de cardápio",
                "verbose_name_plural": "Motivos de alteração de cardápio",
            },
        ),
        migrations.CreateModel(
            name="MotivoSuspensao",
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
                    "nome",
                    models.CharField(blank=True, max_length=100, verbose_name="Nome"),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
            ],
            options={
                "verbose_name": "Motivo de suspensão de alimentação",
                "verbose_name_plural": "Motivo de suspensão de alimentação",
            },
        ),
        migrations.CreateModel(
            name="QuantidadePorPeriodoSuspensaoAlimentacao",
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
                ("numero_alunos", models.SmallIntegerField()),
            ],
            options={
                "verbose_name": "Quantidade por período de suspensão de alimentação",
                "verbose_name_plural": "Quantidade por período de suspensão de alimentação",
            },
        ),
        migrations.CreateModel(
            name="SubstituicaoAlimentacaoNoPeriodoEscolar",
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
            ],
            options={
                "verbose_name": "Substituições de alimentação no período",
                "verbose_name_plural": "Substituições de alimentação no período",
            },
        ),
        migrations.CreateModel(
            name="SuspensaoAlimentacao",
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
                ("data", models.DateField(verbose_name="Data")),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("prioritario", models.BooleanField(default=False)),
                (
                    "outro_motivo",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Outro motivo"
                    ),
                ),
            ],
            options={
                "verbose_name": "Suspensão de alimentação",
                "verbose_name_plural": "Suspensões de alimentação",
            },
        ),
        migrations.CreateModel(
            name="SuspensaoAlimentacaoNoPeriodoEscolar",
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
                ("qtd_alunos", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Suspensão de alimentação no período",
                "verbose_name_plural": "Suspensões de alimentação no período",
            },
        ),
        migrations.CreateModel(
            name="TipoAlimentacao",
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
                    "nome",
                    models.CharField(blank=True, max_length=100, verbose_name="Nome"),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
            ],
            options={
                "verbose_name": "Tipo de alimentação",
                "verbose_name_plural": "Tipos de alimentação",
            },
        ),
        migrations.CreateModel(
            name="VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
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
            ],
            options={
                "verbose_name": "Vínculo tipo alimentação",
                "verbose_name_plural": "Vínculos tipo alimentação",
            },
        ),
    ]
