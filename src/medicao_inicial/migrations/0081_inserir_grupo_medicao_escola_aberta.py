from django.db import migrations

NOME_GRUPO_MEDICAO = "Escola Aberta"


def inserir_grupo_medicao(apps, schema_editor):
    GrupoMedicao = apps.get_model("medicao_inicial", "GrupoMedicao")

    GrupoMedicao.objects.get_or_create(
        nome=NOME_GRUPO_MEDICAO,
        defaults={"ativo": True},
    )


def remover_grupo_medicao(apps, schema_editor):
    GrupoMedicao = apps.get_model("medicao_inicial", "GrupoMedicao")

    GrupoMedicao.objects.filter(nome=NOME_GRUPO_MEDICAO).delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "medicao_inicial",
            "0080_solicitacaomedicaoinicial_lanche_emergencial_extraordinario",
        ),
    ]

    operations = [
        migrations.RunPython(
            inserir_grupo_medicao,
            remover_grupo_medicao,
        ),
    ]
