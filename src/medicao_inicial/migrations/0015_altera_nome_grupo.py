from django.db import migrations


def altera_nome_grupo(apps, _):
    GrupoMedicao = apps.get_model("medicao_inicial", "GrupoMedicao")
    GrupoMedicao.objects.filter(nome="Solicitações de alimentação").update(
        nome="Solicitações de Alimentação"
    )


def backwards(apps, _):
    GrupoMedicao = apps.get_model("medicao_inicial", "GrupoMedicao")
    GrupoMedicao.objects.filter(nome="Solicitações de Alimentação").update(
        nome="Solicitações de alimentação"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("medicao_inicial", "0014_valormedicao_habilitado_correcao"),
    ]

    operations = [
        migrations.RunPython(altera_nome_grupo, backwards),
    ]
