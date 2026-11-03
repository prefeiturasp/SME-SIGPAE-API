from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pos_recebimento", "0006_alter_termorecebimentodefinitivo_status_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "UPDATE pos_recebimento_termorecebimentodefinitivo "
                "SET status = 'ENVIADO_FISCAIS' "
                "WHERE status = 'ENVIADO';"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
