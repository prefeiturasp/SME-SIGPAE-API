from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cardapio", "0052_remove_inversaocardapio_cardapio_para_and_more"),
        ("inclusao_alimentacao", "0041_quantidadeporperiodo_encerrado_a_partir_de"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        ),
        migrations.DeleteModel(
            name="ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        ),
    ]
