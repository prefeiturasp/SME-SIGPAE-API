from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("escola", "0084_alter_escola_acesso_desde"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="escola",
            name="idades",
        ),
        migrations.DeleteModel(
            name="FaixaIdadeEscolar",
        ),
    ]
