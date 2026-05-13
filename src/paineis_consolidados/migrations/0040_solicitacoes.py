import environ
from django.db import migrations

ROOT_DIR = environ.Path(__file__) - 2

sql_path = ROOT_DIR.path("sql", "0041_solicitacoes.sql")
with open(sql_path, "r") as f:
    sql = f.read()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cardapio", "0046_dataintervaloalteracaocardapiocemei"),
        ("dieta_especial", "0047_auto_20220321_0955"),
        (
            "inclusao_alimentacao",
            "0025_diasmotivosinclusaodealimentacaocemei_inclusaodealimentacaocemei_quantidadedealunosemeiinclusaodeali",
        ),
        (
            "kit_lanche",
            "0014_faixasquantidadeskitlancheceidacemei_solicitacaokitlancheceidacemei_solicitacaokitlanchecemei_solici",
        ),
        ("paineis_consolidados", "0039_solicitacoes"),
    ]

    operations = [
        migrations.RunSQL(sql),
    ]
