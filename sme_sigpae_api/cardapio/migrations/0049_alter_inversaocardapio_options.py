# Generated by Django 5.2 on 2025-05-14 10:47

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cardapio", "0048_suspensaoalimentacao_cancelado_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="inversaocardapio",
            options={
                "verbose_name": "Inversão de cardápio",
                "verbose_name_plural": "Inversões de cardápio",
            },
        ),
    ]
