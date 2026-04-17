from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dieta_especial", "0065_alter_solicitacaodietaespecial_status"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ArquivoCargaUsuariosEscola",
        ),
    ]
