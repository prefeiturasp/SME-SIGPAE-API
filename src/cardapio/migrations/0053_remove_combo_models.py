from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cardapio", "0052_remove_inversaocardapio_cardapio_para_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        ),
        migrations.DeleteModel(
            name="ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        ),
    ]
