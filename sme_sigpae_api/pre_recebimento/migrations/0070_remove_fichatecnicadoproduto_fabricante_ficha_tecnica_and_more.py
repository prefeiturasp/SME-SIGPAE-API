import django.db.models.deletion
from django.db import migrations, models


def migrar_dados_fabricante(apps, schema_editor):
    """
    Copia os dados do campo fabricante_ficha_tecnica para um novo campo temporário.
    """
    FichaTecnicaDoProduto = apps.get_model("pre_recebimento", "FichaTecnicaDoProduto")

    for ficha in FichaTecnicaDoProduto.objects.filter(
        fabricante_ficha_tecnica__isnull=False
    ):
        ficha.fabricante_temp = ficha.fabricante_ficha_tecnica
        ficha.save(update_fields=["fabricante_temp"])


def reverter_migracao_fabricante(apps, schema_editor):
    """
    Reverte a migração, copiando os dados de volta para fabricante_ficha_tecnica.
    """
    FichaTecnicaDoProduto = apps.get_model("pre_recebimento", "FichaTecnicaDoProduto")

    for ficha in FichaTecnicaDoProduto.objects.filter(fabricante_temp__isnull=False):
        ficha.fabricante_ficha_tecnica = ficha.fabricante_temp
        ficha.save(update_fields=["fabricante_ficha_tecnica"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "pre_recebimento",
            "0069_remove_fichatecnicadoproduto_bairro_fabricante_and_more",
        ),
        ("produto", "0083_alter_produtoedital_suspenso_justificativa"),
    ]

    operations = [
        # 1. Adiciona um campo temporário para armazenar a referência
        migrations.AddField(
            model_name="fichatecnicadoproduto",
            name="fabricante_temp",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fichas_tecnicas_temp",
                to="pre_recebimento.fabricantefichatecnica",
            ),
        ),
        # 2. Copia os dados para o campo temporário
        migrations.RunPython(
            code=migrar_dados_fabricante,
            reverse_code=reverter_migracao_fabricante,
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="fabricante_ficha_tecnica",
        ),
        migrations.RenameField(
            model_name="fichatecnicadoproduto",
            old_name="fabricante_temp",
            new_name="fabricante",
        ),
        migrations.AddField(
            model_name="fichatecnicadoproduto",
            name="envasador_distribuidor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fichas_tecnicas_como_envasador_distribuidor",
                to="pre_recebimento.fabricantefichatecnica",
                verbose_name="Envasador/Distribuidor",
            ),
        ),
    ]
