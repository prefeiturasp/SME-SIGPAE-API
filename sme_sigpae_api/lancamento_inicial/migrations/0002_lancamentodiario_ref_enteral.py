# Generated by Django 2.2.13 on 2020-10-07 11:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lancamento_inicial", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lancamentodiario",
            name="ref_enteral",
            field=models.IntegerField(null=True),
        ),
    ]