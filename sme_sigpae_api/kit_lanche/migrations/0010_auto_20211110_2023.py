# Generated by Django 2.2.13 on 2021-11-10 20:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kit_lanche", "0009_remove_kitlanche_itens"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitacaokitlancheavulsa",
            name="terceirizada_conferiu_gestao",
            field=models.BooleanField(
                default=False, verbose_name="Terceirizada conferiu?"
            ),
        ),
        migrations.AddField(
            model_name="solicitacaokitlancheceiavulsa",
            name="terceirizada_conferiu_gestao",
            field=models.BooleanField(
                default=False, verbose_name="Terceirizada conferiu?"
            ),
        ),
        migrations.AddField(
            model_name="solicitacaokitlancheunificada",
            name="terceirizada_conferiu_gestao",
            field=models.BooleanField(
                default=False, verbose_name="Terceirizada conferiu?"
            ),
        ),
    ]