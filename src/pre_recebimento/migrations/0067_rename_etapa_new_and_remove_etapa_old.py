from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pre_recebimento", "0066_alter_etapasdocronograma_etapa"),
    ]

    operations = [
        # 1. Remove the old etapa field
        migrations.RemoveField(
            model_name="etapasdocronograma",
            name="etapa",
        ),
        # 2. Rename etapa_new to etapa
        migrations.RenameField(
            model_name="etapasdocronograma",
            old_name="etapa_new",
            new_name="etapa",
        ),
    ]
