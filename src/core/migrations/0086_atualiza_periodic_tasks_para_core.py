from django.db import migrations
from django.utils import timezone

PREFIXO_ANTIGO = "src.escola.tasks."
PREFIXO_NOVO = "src.core.tasks."


def _marca_beat_para_recarregar(apps):
    PeriodicTasks = apps.get_model("django_celery_beat", "PeriodicTasks")
    PeriodicTasks.objects.all().update(last_update=timezone.now())


def atualiza_periodic_tasks_para_core(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    for tarefa in PeriodicTask.objects.filter(task__startswith=PREFIXO_ANTIGO):
        tarefa.task = PREFIXO_NOVO + tarefa.task[len(PREFIXO_ANTIGO) :]
        tarefa.save(update_fields=["task"])

    _marca_beat_para_recarregar(apps)


def volta_periodic_tasks_para_escola(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    for tarefa in PeriodicTask.objects.filter(task__startswith=PREFIXO_NOVO):
        tarefa.task = PREFIXO_ANTIGO + tarefa.task[len(PREFIXO_NOVO) :]
        tarefa.save(update_fields=["task"])

    _marca_beat_para_recarregar(apps)


class Migration(migrations.Migration):

    dependencies = [
        ("escola", "0085_remove_escola_idades_delete_faixaidadeescolar"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(
            atualiza_periodic_tasks_para_core,
            volta_periodic_tasks_para_escola,
        ),
    ]
