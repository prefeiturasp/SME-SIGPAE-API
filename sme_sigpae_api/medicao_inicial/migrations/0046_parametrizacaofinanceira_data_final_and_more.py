import django.db.models.deletion
from django.db import migrations, models


def apagar_parametrizacoes(apps, _):
    ParametrizacaoFinanceira = apps.get_model("medicao_inicial", "ParametrizacaoFinanceira")
    ParametrizacaoFinanceira.objects.all().delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("escola", "0076_auto_20251017_1652"),
        ("medicao_inicial", "0045_alter_medicao_status_and_more"),
    ]

    operations = [
        migrations.RunPython(apagar_parametrizacoes),
        migrations.AddField(
            model_name="parametrizacaofinanceira",
            name="data_final",
            field=models.DateField(blank=True, null=True, verbose_name="Data final"),
        ),
        migrations.AddField(
            model_name="parametrizacaofinanceira",
            name="data_inicial",
            field=models.DateField(blank=True, null=True, verbose_name="Data inicial"),
        ),
        migrations.AddField(
            model_name="parametrizacaofinanceira",
            name="grupo_unidade_escolar",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parametrizacao_financeira_grupo_unidade_escolar",
                to="escola.grupounidadeescolar",
            ),
            preserve_default=False,
        ),
    ]
