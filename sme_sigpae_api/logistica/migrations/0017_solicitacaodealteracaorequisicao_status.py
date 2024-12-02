# Generated by Django 2.2.13 on 2021-02-11 15:00

import django_xworkflows.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logistica", "0016_auto_20210211_1204"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitacaodealteracaorequisicao",
            name="status",
            field=django_xworkflows.models.StateField(
                max_length=31,
                workflow=django_xworkflows.models._SerializedWorkflow(
                    initial_state="AGUARDANDO_ENVIO",
                    name="SolicitacaoRemessaWorkFlow",
                    states=[
                        "AGUARDANDO_ENVIO",
                        "DILOG_ENVIA",
                        "CANCELADA",
                        "DISTRIBUIDOR_CONFIRMA",
                        "DISTRIBUIDOR_SOLICITA_ALTERACAO",
                    ],
                ),
            ),
        ),
    ]