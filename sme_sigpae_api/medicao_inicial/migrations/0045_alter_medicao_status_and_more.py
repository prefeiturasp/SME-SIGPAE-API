# Generated by Django 5.2.2 on 2025-07-01 15:48

import django_xworkflows.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("medicao_inicial", "0044_relatoriofinanceiro_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="medicao",
            name="status",
            field=django_xworkflows.models.StateField(
                max_length=39,
                workflow=django_xworkflows.models._SerializedWorkflow(
                    initial_state="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                    name="SolicitacaoMedicaoInicialWorkflow",
                    states=[
                        "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                        "MEDICAO_ENVIADA_PELA_UE",
                        "MEDICAO_CORRECAO_SOLICITADA",
                        "MEDICAO_CORRECAO_SOLICITADA_CODAE",
                        "MEDICAO_CORRIGIDA_PELA_UE",
                        "MEDICAO_CORRIGIDA_PARA_CODAE",
                        "MEDICAO_APROVADA_PELA_DRE",
                        "MEDICAO_APROVADA_PELA_CODAE",
                        "MEDICAO_SEM_LANCAMENTOS",
                    ],
                ),
            ),
        ),
        migrations.AlterField(
            model_name="ocorrenciamedicaoinicial",
            name="status",
            field=django_xworkflows.models.StateField(
                max_length=39,
                workflow=django_xworkflows.models._SerializedWorkflow(
                    initial_state="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                    name="SolicitacaoMedicaoInicialWorkflow",
                    states=[
                        "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                        "MEDICAO_ENVIADA_PELA_UE",
                        "MEDICAO_CORRECAO_SOLICITADA",
                        "MEDICAO_CORRECAO_SOLICITADA_CODAE",
                        "MEDICAO_CORRIGIDA_PELA_UE",
                        "MEDICAO_CORRIGIDA_PARA_CODAE",
                        "MEDICAO_APROVADA_PELA_DRE",
                        "MEDICAO_APROVADA_PELA_CODAE",
                        "MEDICAO_SEM_LANCAMENTOS",
                    ],
                ),
            ),
        ),
        migrations.AlterField(
            model_name="solicitacaomedicaoinicial",
            name="status",
            field=django_xworkflows.models.StateField(
                max_length=39,
                workflow=django_xworkflows.models._SerializedWorkflow(
                    initial_state="MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                    name="SolicitacaoMedicaoInicialWorkflow",
                    states=[
                        "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE",
                        "MEDICAO_ENVIADA_PELA_UE",
                        "MEDICAO_CORRECAO_SOLICITADA",
                        "MEDICAO_CORRECAO_SOLICITADA_CODAE",
                        "MEDICAO_CORRIGIDA_PELA_UE",
                        "MEDICAO_CORRIGIDA_PARA_CODAE",
                        "MEDICAO_APROVADA_PELA_DRE",
                        "MEDICAO_APROVADA_PELA_CODAE",
                        "MEDICAO_SEM_LANCAMENTOS",
                    ],
                ),
            ),
        ),
    ]
