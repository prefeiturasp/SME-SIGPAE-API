# Generated by Django 2.2.13 on 2021-10-25 17:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("escola", "0043_auto_20211025_1729"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diretoriaregional",
            name="iniciais",
            field=models.CharField(blank=True, max_length=20, verbose_name="Iniciais"),
        ),
        migrations.AlterField(
            model_name="lote",
            name="iniciais",
            field=models.CharField(blank=True, max_length=20, verbose_name="Iniciais"),
        ),
        migrations.AlterField(
            model_name="tipounidadeescolar",
            name="iniciais",
            field=models.CharField(blank=True, max_length=20, verbose_name="Iniciais"),
        ),
    ]