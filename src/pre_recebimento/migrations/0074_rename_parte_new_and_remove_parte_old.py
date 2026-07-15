from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pre_recebimento", "0073_alter_etapasdocronograma_parte"),
    ]

    operations = [
        # Remove the old parte field
        migrations.RemoveField(
            model_name="etapasdocronograma",
            name="parte",
        ),
        # Rename parte_new to parte
        migrations.RenameField(
            model_name="etapasdocronograma",
            old_name="parte_new",
            new_name="parte",
        ),
    ]
