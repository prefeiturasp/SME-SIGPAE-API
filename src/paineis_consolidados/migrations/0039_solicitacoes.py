import environ
from django.db import migrations

ROOT_DIR = environ.Path(__file__) - 2

sql_path = ROOT_DIR.path("sql", "0040_solicitacoes.sql")
with open(sql_path, "r") as f:
    sql = f.read()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("paineis_consolidados", "0038_solicitacoes"),
    ]

    operations = [
        migrations.RunSQL(sql),
    ]
