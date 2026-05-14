import environ
from django.db import migrations

ROOT_DIR = environ.Path(__file__) - 2

sql_path = ROOT_DIR.path("sql", "0043_solicitacoes.sql")
with open(sql_path, "r") as f:
    sql = f.read()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cardapio", "0053_remove_combo_models"),
        ("paineis_consolidados", "0042_solicitacoes"),
    ]

    operations = [
        migrations.RunSQL(sql),
    ]
