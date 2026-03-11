import datetime

from django.db import migrations, models


def criar_lanche_emergencial_diario(apps, schema_editor):
    Escola = apps.get_model("escola", "Escola")
    LancheEmergencialDiario = apps.get_model(
        "medicao_inicial", "LancheEmergencialDiario"
    )

    escola = Escola.objects.filter(codigo_eol="000329").first()
    if not escola:
        return

    LancheEmergencialDiario.objects.get_or_create(
        escola=escola,
        data_inicial=datetime.date(2026, 3, 1),
        defaults={"data_final": None},
    )


def excluir_lanche_emergencial_diario(apps, schema_editor):
    Escola = apps.get_model("escola", "Escola")
    LancheEmergencialDiario = apps.get_model(
        "medicao_inicial", "LancheEmergencialDiario"
    )

    escola = Escola.objects.filter(codigo_eol="000329").first()
    if not escola:
        return

    LancheEmergencialDiario.objects.filter(
        escola=escola,
        data_inicial=datetime.date(2026, 3, 1),
        data_final__isnull=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("medicao_inicial", "0059_alter_relatoriofinanceiro_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="LancheEmergencialDiario",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data_inicial", models.DateField(verbose_name="Data inicial")),
                (
                    "data_final",
                    models.DateField(blank=True, null=True, verbose_name="Data final"),
                ),
                (
                    "escola",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="lanches_emergenciais_diarios",
                        to="escola.escola",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lanche Emergencial Diário",
                "verbose_name_plural": "Lanches Emergenciais Diários",
                "ordering": ("escola__nome", "data_inicial"),
            },
        ),
        migrations.RunPython(
            criar_lanche_emergencial_diario, excluir_lanche_emergencial_diario
        ),
    ]
