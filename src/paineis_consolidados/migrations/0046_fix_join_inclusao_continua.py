import environ
from django.db import migrations

ROOT_DIR = environ.Path(__file__) - 2

sql_path = ROOT_DIR.path("sql", "0043_solicitacoes.sql")
with open(sql_path, "r") as f:
    sql = f.read()


class Migration(migrations.Migration):
    dependencies = [
        (
            "paineis_consolidados",
            "0045_merge_0043_solicitacoes_0044_otimizacao_indices_v2",
        ),
    ]

    operations = [
        migrations.RunSQL(sql),
    ]
