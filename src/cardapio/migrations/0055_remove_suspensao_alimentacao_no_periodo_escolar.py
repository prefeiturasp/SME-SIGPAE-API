# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cardapio", "0054_popula_vinculos_ceu_polo_e_ceu_polo_uab"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SuspensaoAlimentacaoNoPeriodoEscolar",
        ),
    ]
