from django.db import migrations, models


def migrate_parte_forward(apps, schema_editor):
    """Migrate data from parte to parte_new, extracting the number from 'Parte X'."""
    with schema_editor.connection.cursor() as cursor:
        # Extract number from 'Parte X' format and convert to integer
        cursor.execute(
            """
            UPDATE pre_recebimento_etapasdocronograma
            SET parte_new = CAST(SUBSTRING(parte FROM 'Parte (\\d+)') AS INTEGER)
            WHERE parte ~ '^Parte \\d+$';
        """
        )

        # Set NULL for any non-matching values
        cursor.execute(
            """
            UPDATE pre_recebimento_etapasdocronograma
            SET parte_new = NULL
            WHERE parte IS NULL OR parte = '' OR parte !~ '^Parte \\d+$';
        """
        )


def migrate_parte_backward(apps, schema_editor):
    """Migrate data back from parte_new to parte, converting to 'Parte X' format."""
    with schema_editor.connection.cursor() as cursor:
        # Convert back to 'Parte X' format
        cursor.execute(
            """
            UPDATE pre_recebimento_etapasdocronograma
            SET parte = 'Parte ' || parte_new::text
            WHERE parte_new IS NOT NULL;
        """
        )

        # Set empty string for NULL values
        cursor.execute(
            """
            UPDATE pre_recebimento_etapasdocronograma
            SET parte = ''
            WHERE parte_new IS NULL;
        """
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "pre_recebimento",
            "0072_analisefichatecnica_fabricante_envasador_conferido_and_more",
        ),
    ]

    operations = [
        # Add the new integer field
        migrations.AddField(
            model_name="etapasdocronograma",
            name="parte_new",
            field=models.IntegerField(blank=True, null=True, verbose_name="Parte"),
        ),
        # Run the data migration
        migrations.RunPython(
            code=migrate_parte_forward,
            reverse_code=migrate_parte_backward,
        ),
        # Make the original field nullable
        migrations.AlterField(
            model_name="etapasdocronograma",
            name="parte",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
