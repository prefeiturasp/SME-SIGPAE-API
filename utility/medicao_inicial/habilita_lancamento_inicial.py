import os
import django
import datetime
from dateutil.relativedelta import relativedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()


ANO = 2024
MES = 10
DIAS_MES = 31
QUANTIDADE_ALUNOS = 25



def habilitar_dias_letivos():
    from sme_sigpae_api.escola.utils import calendario_sgp
    d = datetime.date(ANO, MES, 1)
    calendario_sgp(d)

if __name__ == "__main__":
    habilitar_dias_letivos()