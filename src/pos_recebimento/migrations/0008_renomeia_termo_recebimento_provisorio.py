from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pos_recebimento", "0007_corrige_status_enviado"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="TermoRecebimentoDefinitivo",
            new_name="TermoRecebimentoProvisorio",
        ),
        migrations.RenameModel(
            old_name="CronogramaTermoRecebimentoDefinitivo",
            new_name="CronogramaTermoRecebimentoProvisorio",
        ),
        migrations.RenameModel(
            old_name="AssinaturaTermoRecebimentoDefinitivo",
            new_name="AssinaturaTermoRecebimentoProvisorio",
        ),
    ]
