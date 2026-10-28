from django.core.validators import MinLengthValidator
from django.db import migrations, models

CAMPOS_TEXTO_DO_LOG = (
    "codigo_eol_aluno",
    "nome_aluno",
    "codigo_eol_escola_origem",
    "nome_escola_origem",
    "codigo_eol_escola_destino",
    "nome_escola_destino",
)


def preenche_campos_nulos(apps, _):
    """Substitui NULL por string vazia nos campos que deixam de aceitar NULL."""
    PlanilhaDietasAtivas = apps.get_model("dieta_especial", "PlanilhaDietasAtivas")
    PlanilhaDietasAtivas.objects.filter(tempfile__isnull=True).update(tempfile="")

    LogDietasAtivasCanceladasAutomaticamente = apps.get_model(
        "dieta_especial", "LogDietasAtivasCanceladasAutomaticamente"
    )
    for campo in CAMPOS_TEXTO_DO_LOG:
        LogDietasAtivasCanceladasAutomaticamente.objects.filter(
            **{f"{campo}__isnull": True}
        ).update(**{campo: ""})


class Migration(migrations.Migration):
    dependencies = [
        ("dieta_especial", "0068_delete_tipocontagem"),
    ]

    operations = [
        migrations.RunPython(preenche_campos_nulos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="codigo_eol_aluno",
            field=models.CharField(
                blank=True,
                default="",
                max_length=7,
                validators=[MinLengthValidator(7)],
                verbose_name="Código EOL aluno",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="codigo_eol_escola_destino",
            field=models.CharField(
                blank=True,
                default="",
                max_length=6,
                validators=[MinLengthValidator(6)],
                verbose_name="Código EOL escola destino",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="codigo_eol_escola_origem",
            field=models.CharField(
                blank=True,
                default="",
                max_length=6,
                validators=[MinLengthValidator(6)],
                verbose_name="Código EOL escola origem",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="nome_aluno",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                verbose_name="Nome do Aluno",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="nome_escola_destino",
            field=models.CharField(
                blank=True,
                default="",
                max_length=160,
                verbose_name="Nome da Escola destino",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="logdietasativascanceladasautomaticamente",
            name="nome_escola_origem",
            field=models.CharField(
                blank=True,
                default="",
                max_length=160,
                verbose_name="Nome da Escola origem",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="planilhadietasativas",
            name="tempfile",
            field=models.CharField(
                blank=True,
                default="",
                help_text="JSON temporario",
                max_length=100,
            ),
            preserve_default=False,
        ),
    ]
