from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "cardapio",
            "0050_alter_faixaetariasubstituicaoalimentacaocei_matriculados_quando_criado_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="alteracaocardapio",
            name="eh_alteracao_com_lanche_repetida",
        ),
        migrations.RemoveField(
            model_name="alteracaocardapiocei",
            name="eh_alteracao_com_lanche_repetida",
        ),
    ]
