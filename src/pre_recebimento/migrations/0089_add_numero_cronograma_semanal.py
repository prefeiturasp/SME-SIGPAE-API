# Generated manually - Adiciona campo numero ao CronogramaSemanal e popula para registros existentes

from django.db import migrations, models


def popular_numeros_cronogramas_semanais(apps, schema_editor):
    """Popula o campo numero para cronogramas semanais existentes."""
    CronogramaSemanal = apps.get_model("pre_recebimento", "CronogramaSemanal")

    # Ordena por ano de criacao e depois por data de criacao
    cronogramas = CronogramaSemanal.objects.all().order_by("criado_em")

    ano_atual = None
    sequencial = 0

    for cronograma in cronogramas:
        ano_criacao = cronograma.criado_em.year

        if ano_criacao != ano_atual:
            ano_atual = ano_criacao
            sequencial = 1
        else:
            sequencial += 1

        cronograma.numero = f"{str(sequencial).zfill(3)}/{ano_atual}"
        cronograma.save(update_fields=["numero"])


def reverse_popular_numeros(apps, schema_editor):
    """Reverse migration - limpa o campo numero."""
    CronogramaSemanal = apps.get_model("pre_recebimento", "CronogramaSemanal")
    CronogramaSemanal.objects.all().update(numero=None)


class Migration(migrations.Migration):
    dependencies = [
        ("pre_recebimento", "0088_alter_fluxocronograma_semanal_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="cronogramasemanal",
            name="numero",
            field=models.CharField(
                "Número do Cronograma Semanal",
                blank=True,
                max_length=250,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(
            popular_numeros_cronogramas_semanais,
            reverse_popular_numeros,
        ),
    ]
