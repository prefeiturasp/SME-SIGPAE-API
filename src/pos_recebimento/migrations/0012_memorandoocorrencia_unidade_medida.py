"""Adiciona ``unidade_medida`` ao Memorando de Ocorrência.

A coluna é NOT NULL. Para memorandos pré-existentes, usamos como default a
unidade de medida de pré-recebimento mais antiga.
"""

from django.db import migrations, models


def backfill_unidade_medida(apps, schema_editor):
    Memorando = apps.get_model("pos_recebimento", "MemorandoOcorrencia")
    UnidadeMedida = apps.get_model("pre_recebimento", "UnidadeMedida")

    pendentes = Memorando.objects.filter(unidade_medida__isnull=True)
    if not pendentes.exists():
        return

    default = UnidadeMedida.objects.order_by("criado_em").first()
    if default is None:
        raise RuntimeError(
            "Não há UnidadeMedida cadastrada para preencher memorandos "
            "pré-existentes. Cadastre ao menos uma antes de rodar a migration."
        )
    pendentes.update(unidade_medida=default)


class Migration(migrations.Migration):

    dependencies = [
        ("pos_recebimento", "0011_remove_status_e_etapa_sem_uso"),
        (
            "pre_recebimento",
            "0092_documentoderecebimento_justificativa_reprovacao_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="memorandoocorrencia",
            name="unidade_medida",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name="memorandos_ocorrencia",
                to="pre_recebimento.unidademedida",
                verbose_name="Unidade de Medida",
            ),
        ),
        migrations.RunPython(
            backfill_unidade_medida,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="memorandoocorrencia",
            name="unidade_medida",
            field=models.ForeignKey(
                on_delete=models.deletion.PROTECT,
                related_name="memorandos_ocorrencia",
                to="pre_recebimento.unidademedida",
                verbose_name="Unidade de Medida",
            ),
        ),
    ]
